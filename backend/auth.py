from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional
import os
import logging
from backend.config import settings
from backend.database import db_session
from backend.permissions import Role, has_permission

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)

class AuthenticatedUser(BaseModel):
    uid: str
    email: str
    role: str

_firebase_initialized = False

def get_firebase_app():
    global _firebase_initialized
    if not _firebase_initialized:
        try:
            import firebase_admin
            from firebase_admin import credentials
            cred_path = settings.GOOGLE_APPLICATION_CREDENTIALS
            local_fallback = os.path.join(os.path.dirname(__file__), "secrets", "firebase-service-account.json")
            target_cred = None

            if cred_path and os.path.exists(cred_path):
                target_cred = cred_path
            elif os.path.exists(local_fallback):
                target_cred = local_fallback

            if target_cred:
                cred = credentials.Certificate(target_cred)
                firebase_admin.initialize_app(cred, {"projectId": settings.FIREBASE_PROJECT_ID})
            else:
                firebase_admin.initialize_app(options={"projectId": settings.FIREBASE_PROJECT_ID})
            _firebase_initialized = True
        except Exception as e:
            logger.warning(f"Firebase initialize_app warning: {e}")
            _firebase_initialized = True

def verify_token(token: str) -> dict:
    if settings.ENVIRONMENT == "development" or settings.FIREBASE_AUTH_EMULATOR_HOST:
        # Development / test mock payload support if token format is "mock:uid:email"
        if token.startswith("mock:"):
            parts = token.split(":")
            uid = parts[1] if len(parts) > 1 else "mock_uid"
            email = parts[2] if len(parts) > 2 else "mock@example.com"
            return {"uid": uid, "email": email}

    # First attempt: Firebase Admin SDK verify_id_token
    try:
        get_firebase_app()
        from firebase_admin import auth
        decoded = auth.verify_id_token(token)
        return decoded
    except Exception as e:
        logger.info(f"Firebase Admin SDK verify failed ({e}), attempting public JWT verification...")

    # Fallback: Verify JWT using PyJWT against Google's public certificates (no service account needed)
    try:
        import jwt
        # Unverified decode to inspect headers and claims
        unverified_header = jwt.get_unverified_header(token)
        unverified_claims = jwt.decode(token, options={"verify_signature": False})
        kid = unverified_header.get("kid")
        alg = unverified_header.get("alg")

        # Fetch Google's public JWK / x509 certs
        import urllib.request
        import json
        jwks_url = "https://www.googleapis.com/service_accounts/v1/jwk/securetoken@system.gserviceaccount.com"
        req = urllib.request.Request(jwks_url, headers={"User-Agent": "FastAPI-Backend"})
        with urllib.request.urlopen(req, timeout=5) as response:
            jwks_data = json.loads(response.read().decode())

        # Locate matching key
        matching_key = None
        for key in jwks_data.get("keys", []):
            if key.get("kid") == kid:
                matching_key = key
                break

        if matching_key:
            public_key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(matching_key))
            project_id = unverified_claims.get("aud") or settings.FIREBASE_PROJECT_ID
            decoded = jwt.decode(
                token,
                public_key,
                algorithms=[alg or "RS256"],
                audience=project_id,
                issuer=f"https://securetoken.google.com/{project_id}"
            )
            return {
                "uid": decoded.get("user_id") or decoded.get("sub"),
                "email": decoded.get("email") or f"{decoded.get('sub')}@example.com"
            }
        elif settings.ENVIRONMENT == "development":
            # If development and key couldn't be resolved, permit validly formed unverified claims
            uid = unverified_claims.get("user_id") or unverified_claims.get("sub")
            email = unverified_claims.get("email") or f"{uid}@example.com"
            if uid:
                logger.warning(f"Development fallback: accepting token for {email} ({uid})")
                return {"uid": uid, "email": email}
    except Exception as fallback_err:
        logger.error(f"Public JWT fallback error: {fallback_err}")

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

def get_or_create_user(uid: str, email: str) -> AuthenticatedUser:
    with db_session() as conn:
        cursor = conn.execute("SELECT uid, email, role FROM users WHERE uid = ? OR email = ?", (uid, email))
        row = cursor.fetchone()
        
        if not row:
            # Check if this email is the bootstrap admin email
            role = Role.ADMIN.value if email.lower() == settings.BOOTSTRAP_ADMIN_EMAIL.lower() else Role.USER.value
            conn.execute(
                """
                INSERT INTO users (uid, email, role, last_login)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (uid, email, role)
            )
            return AuthenticatedUser(uid=uid, email=email, role=role)
        else:
            conn.execute("UPDATE users SET uid = ?, last_login = CURRENT_TIMESTAMP WHERE email = ?", (uid, email))
            return AuthenticatedUser(uid=uid, email=row["email"], role=row["role"])

def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security)
) -> AuthenticatedUser:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    token_data = verify_token(token)
    uid = token_data.get("uid")
    email = token_data.get("email", f"{uid}@example.com")
    
    if not uid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="UID missing from token",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    return get_or_create_user(uid=uid, email=email)

def require_permission(permission: str):
    def permission_dependency(current_user: AuthenticatedUser = Depends(get_current_user)) -> AuthenticatedUser:
        if not has_permission(current_user.role, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' denied for role '{current_user.role}'"
            )
        return current_user
    return permission_dependency
