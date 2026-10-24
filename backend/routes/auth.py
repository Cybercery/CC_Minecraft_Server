from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from backend.auth import AuthenticatedUser, get_current_user, require_permission
from backend.services.audit_service import audit_service

router = APIRouter(prefix="/auth", tags=["auth"])

class UserProfileResponse(BaseModel):
    uid: str
    email: str
    role: str

class AuditLogItem(BaseModel):
    id: int
    uid: Optional[str] = None
    email: Optional[str] = None
    action: str
    resource: str
    status: str
    details: Optional[dict] = None
    timestamp: Optional[str] = None

@router.get("/me", response_model=UserProfileResponse)
def get_me(user: AuthenticatedUser = Depends(get_current_user)):
    return UserProfileResponse(uid=user.uid, email=user.email, role=user.role)

@router.get("/audit-logs", response_model=List[AuditLogItem])
def get_audit_logs(
    limit: int = 100,
    offset: int = 0,
    user: AuthenticatedUser = Depends(require_permission("audit:read"))
):
    return audit_service.list_logs(limit=limit, offset=offset)
