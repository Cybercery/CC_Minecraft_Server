from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from backend.auth import AuthenticatedUser, require_permission
from backend.permissions import Role
from backend.database import db_session
from backend.services.audit_service import audit_service

router = APIRouter(prefix="/users", tags=["users"])

class UserResponse(BaseModel):
    uid: str
    email: str
    role: str
    created_at: Optional[str] = None
    last_login: Optional[str] = None

class UpdateRoleRequest(BaseModel):
    role: str

@router.get("", response_model=List[UserResponse])
def list_users(
    user: AuthenticatedUser = Depends(require_permission("users:read"))
):
    with db_session() as conn:
        cursor = conn.execute("SELECT uid, email, role, created_at, last_login FROM users ORDER BY created_at DESC")
        rows = cursor.fetchall()
        return [dict(r) for r in rows]

@router.put("/{target_uid}/role", response_model=UserResponse)
def update_user_role(
    target_uid: str,
    request: UpdateRoleRequest,
    current_user: AuthenticatedUser = Depends(require_permission("users:write"))
):
    valid_roles = [Role.ADMIN.value, Role.OPERATOR.value, Role.USER.value]
    if request.role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Must be one of {valid_roles}"
        )

    with db_session() as conn:
        cursor = conn.execute("SELECT uid, email, role, created_at, last_login FROM users WHERE uid = ?", (target_uid,))
        target_user = cursor.fetchone()
        if not target_user:
            raise HTTPException(status_code=404, detail="User not found")

        # Prevent admin removing their own admin role to avoid lockout
        if target_uid == current_user.uid and request.role != Role.ADMIN.value:
            raise HTTPException(status_code=400, detail="Cannot demote yourself from Administrator")

        conn.execute("UPDATE users SET role = ? WHERE uid = ?", (request.role, target_uid))
        cursor = conn.execute("SELECT uid, email, role, created_at, last_login FROM users WHERE uid = ?", (target_uid,))
        updated_user = cursor.fetchone()

        audit_service.log_action(
            action="update_role",
            resource=f"users/{target_uid}",
            status="success",
            uid=current_user.uid,
            email=current_user.email,
            details={"old_role": target_user["role"], "new_role": request.role}
        )

        return dict(updated_user)
