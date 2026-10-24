from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from docker.errors import NotFound, APIError
from backend.services.docker_service import docker_service
from backend.services.rcon_service import rcon_service

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
def get_server_status():
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
def start_server():
    try:
        return docker_service.start_server()
    except NotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stop")
def stop_server():
    try:
        return docker_service.stop_server()
    except NotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/restart")
def restart_server():
    try:
        return docker_service.restart_server()
    except NotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/logs")
def get_server_logs(tail: int = Query(default=100, ge=1, le=1000)):
    try:
        logs = docker_service.get_logs(tail=tail)
        return {"tail": tail, "logs": logs}
    except NotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/rcon", response_model=RconCommandResponse)
def execute_rcon(request: RconCommandRequest):
    if not request.command or not request.command.strip():
        raise HTTPException(status_code=400, detail="Command cannot be empty")
    try:
        result = rcon_service.execute_command(request.command.strip())
        return RconCommandResponse(command=request.command, response=result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"RCON command execution failed: {e}")
