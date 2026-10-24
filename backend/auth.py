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

    try:
        get_firebase_app()
        from firebase_admin import auth
        decoded = auth.verify_id_token(token)
        return decoded
    except Exception as e:
        logger.error(f"Token verification error: {e}")
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
