from fastapi import APIRouter, Depends, HTTPException, Header, status
from pydantic import BaseModel
from typing import Optional
from backend.auth import AuthenticatedUser, get_current_user, require_permission
from backend.config import settings
from backend.services.verification_service import verification_service
from backend.services.audit_service import audit_service

router = APIRouter(prefix="/minecraft", tags=["minecraft"])

class GenerateCodeResponse(BaseModel):
    code: str
    expires_at: str
    ttl_seconds: int

class MinecraftLinkResponse(BaseModel):
    linked: bool
    uid: Optional[str] = None
    minecraft_uuid: Optional[str] = None
    minecraft_username: Optional[str] = None
    linked_at: Optional[str] = None

class PluginVerifyRequest(BaseModel):
    code: str
    minecraft_uuid: str
    minecraft_username: str

def verify_plugin_api_key(x_plugin_api_key: Optional[str] = Header(None, alias="X-Plugin-Api-Key")):
    import os
    expected_key = os.environ.get("PLUGIN_API_KEY", settings.PLUGIN_API_KEY)
    if not expected_key or not x_plugin_api_key or x_plugin_api_key != expected_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-Plugin-Api-Key header"
        )
    return True

# --- User Web Endpoints ---

@router.post("/verification-code", response_model=GenerateCodeResponse)
def generate_verification_code(
    user: AuthenticatedUser = Depends(require_permission("minecraft:link"))
):
    code, expires_at = verification_service.generate_code(user.uid)
    return GenerateCodeResponse(
        code=code,
        expires_at=expires_at.isoformat(),
        ttl_seconds=settings.VERIFICATION_CODE_TTL_SECONDS
    )

@router.get("/link", response_model=MinecraftLinkResponse)
def get_user_minecraft_link(
    user: AuthenticatedUser = Depends(get_current_user)
):
    link = verification_service.get_link_by_uid(user.uid)
    if not link:
        return MinecraftLinkResponse(linked=False)
    return MinecraftLinkResponse(
        linked=True,
        uid=link["uid"],
        minecraft_uuid=link["minecraft_uuid"],
        minecraft_username=link["minecraft_username"],
        linked_at=link["linked_at"]
    )

@router.delete("/link")
def unlink_user_minecraft(
    user: AuthenticatedUser = Depends(require_permission("minecraft:link"))
):
    success = verification_service.unlink_by_uid(user.uid)
    if success:
        audit_service.log_action("minecraft_unlink", f"minecraft/{user.uid}", "success", uid=user.uid, email=user.email)
        return {"message": "Minecraft account unlinked successfully"}
    return {"message": "No linked Minecraft account found"}

# --- Plugin Endpoints (Secured by X-Plugin-Api-Key) ---

@router.post("/plugin/verify")
def plugin_verify_player(
    req: PluginVerifyRequest,
    _: bool = Depends(verify_plugin_api_key)
):
    res = verification_service.verify_and_link(
        raw_code=req.code,
        minecraft_uuid=req.minecraft_uuid,
        minecraft_username=req.minecraft_username
    )
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error", "Verification failed"))

    audit_service.log_action(
        "minecraft_link",
        f"minecraft/{req.minecraft_uuid}",
        "success",
        uid=res.get("uid"),
        details={"username": req.minecraft_username, "uuid": req.minecraft_uuid}
    )
    return {"success": True, "message": "Player successfully linked"}

@router.get("/plugin/player/{uuid}")
def plugin_get_player_status(
    uuid: str,
    _: bool = Depends(verify_plugin_api_key)
):
    link = verification_service.get_link_by_uuid(uuid)
    if not link:
        return {"linked": False, "verified": False}
    return {
        "linked": True,
        "verified": True,
        "uid": link["uid"],
        "email": link["email"],
        "role": link["role"],
        "username": link["minecraft_username"]
    }
