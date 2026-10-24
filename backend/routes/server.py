from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
from typing import List, Optional
from docker.errors import NotFound, APIError
from backend.services.docker_service import docker_service
from backend.services.rcon_service import rcon_service
from backend.auth import AuthenticatedUser, require_permission
from backend.services.audit_service import audit_service

router = APIRouter(prefix="/server", tags=["server"])

class RconCommandRequest(BaseModel):
    command: str

class RconCommandResponse(BaseModel):
    command: str
    response: str

class ServerStatusResponse(BaseModel):
    status: str
    running: bool
    container_id: Optional[str] = None
    name: str
    image: Optional[str] = None
    players_online: int = 0
    players: List[str] = []

@router.get("/status", response_model=ServerStatusResponse)
def get_server_status(user: AuthenticatedUser = Depends(require_permission("server:read"))):
    try:
        status_info = docker_service.get_status()
        players_online = 0
        players = []
        if status_info.get("running"):
            player_info = rcon_service.get_player_list()
            players_online = player_info.get("online_count", 0)
            players = player_info.get("players", [])

        return ServerStatusResponse(
            status=status_info.get("status", "unknown"),
            running=status_info.get("running", False),
            container_id=status_info.get("container_id"),
            name=status_info.get("name", ""),
            image=status_info.get("image"),
            players_online=players_online,
            players=players
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/start")
def start_server(user: AuthenticatedUser = Depends(require_permission("server:start"))):
    try:
        res = docker_service.start_server()
        audit_service.log_action("server_start", "server", "success", uid=user.uid, email=user.email)
        return res
    except NotFound as e:
        audit_service.log_action("server_start", "server", "failed", uid=user.uid, email=user.email, details={"error": str(e)})
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        audit_service.log_action("server_start", "server", "failed", uid=user.uid, email=user.email, details={"error": str(e)})
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stop")
def stop_server(user: AuthenticatedUser = Depends(require_permission("server:stop"))):
    try:
        res = docker_service.stop_server()
        audit_service.log_action("server_stop", "server", "success", uid=user.uid, email=user.email)
        return res
    except NotFound as e:
        audit_service.log_action("server_stop", "server", "failed", uid=user.uid, email=user.email, details={"error": str(e)})
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        audit_service.log_action("server_stop", "server", "failed", uid=user.uid, email=user.email, details={"error": str(e)})
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/restart")
def restart_server(user: AuthenticatedUser = Depends(require_permission("server:restart"))):
    try:
        res = docker_service.restart_server()
        audit_service.log_action("server_restart", "server", "success", uid=user.uid, email=user.email)
        return res
    except NotFound as e:
        audit_service.log_action("server_restart", "server", "failed", uid=user.uid, email=user.email, details={"error": str(e)})
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        audit_service.log_action("server_restart", "server", "failed", uid=user.uid, email=user.email, details={"error": str(e)})
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/logs")
def get_server_logs(
    tail: int = Query(default=100, ge=1, le=1000),
    user: AuthenticatedUser = Depends(require_permission("server:logs"))
):
    try:
        logs = docker_service.get_logs(tail=tail)
        return {"tail": tail, "logs": logs}
    except NotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/rcon", response_model=RconCommandResponse)
def execute_rcon(
    request: RconCommandRequest,
    user: AuthenticatedUser = Depends(require_permission("server:rcon"))
):
    if not request.command or not request.command.strip():
        raise HTTPException(status_code=400, detail="Command cannot be empty")
    try:
        result = rcon_service.execute_command(request.command.strip())
        audit_service.log_action(
            "rcon_command",
            "server",
            "success",
            uid=user.uid,
            email=user.email,
            details={"command": request.command.strip()}
        )
        return RconCommandResponse(command=request.command, response=result)
    except ValueError as e:
        audit_service.log_action("rcon_command", "server", "failed", uid=user.uid, email=user.email, details={"command": request.command, "error": str(e)})
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        audit_service.log_action("rcon_command", "server", "failed", uid=user.uid, email=user.email, details={"command": request.command, "error": str(e)})
        raise HTTPException(status_code=502, detail=f"RCON command execution failed: {e}")

