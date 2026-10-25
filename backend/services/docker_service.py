import docker
from docker.errors import NotFound, APIError
from backend.config import settings
import logging

logger = logging.getLogger(__name__)

class DockerService:
    def __init__(self):
        self._client = None

    def _get_client(self):
        if not self._client:
            self._client = docker.from_env()
        return self._client

    def get_container(self, name: str = None):
        target = name or settings.MC_CONTAINER_NAME
        try:
            return self._get_client().containers.get(target)
        except NotFound:
            return None
        except Exception as e:
            logger.error(f"Error fetching container {target}: {e}")
            raise

    def get_online_mode(self) -> bool:
        container = self.get_container()
        if container:
            try:
                container.reload()
                env_list = container.attrs.get("Config", {}).get("Env", [])
                for env in env_list:
                    if env.startswith("ONLINE_MODE="):
                        val = env.split("=", 1)[1].strip().lower()
                        return val in ("true", "1", "yes")
            except Exception as e:
                logger.warning(f"Error inspecting container ONLINE_MODE: {e}")
        return bool(settings.MINECRAFT_ONLINE_MODE)

    def get_server_properties(self) -> dict:
        online_mode = self.get_online_mode()
        container = self.get_container()
        inspect_running = f"docker exec {settings.MC_CONTAINER_NAME} cat /data/server.properties"
        inspect_stopped = "docker run --rm -v minecraft_server_project_mc_data:/data alpine cat /data/server.properties"

        if not container:
            return {
                "source": "environment",
                "container_state": "not_found",
                "online_mode": online_mode,
                "properties_file_found": False,
                "content": None,
                "parsed": {
                    "online-mode": str(online_mode).lower(),
                    "max-players": str(settings.MC_MAX_PLAYERS),
                    "enable-rcon": "true"
                },
                "inspect_command_running": inspect_running,
                "inspect_command_stopped": inspect_stopped
            }

        container.reload()
        if container.status == "running":
            try:
                res = container.exec_run("cat /data/server.properties")
                if res.exit_code == 0:
                    raw_content = res.output.decode("utf-8", errors="replace")
                    parsed = {}
                    for line in raw_content.splitlines():
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            parsed[k.strip()] = v.strip()
                    effective_online = parsed.get("online-mode", str(online_mode)).lower() in ("true", "1", "yes")
                    return {
                        "source": "container_filesystem",
                        "container_state": "running",
                        "online_mode": effective_online,
                        "properties_file_found": True,
                        "content": raw_content,
                        "parsed": parsed,
                        "inspect_command_running": inspect_running,
                        "inspect_command_stopped": inspect_stopped
                    }
            except Exception as e:
                logger.warning(f"Error reading server.properties via exec: {e}")

        return {
            "source": "container_config",
            "container_state": container.status,
            "online_mode": online_mode,
            "properties_file_found": False,
            "content": None,
            "parsed": {
                "online-mode": str(online_mode).lower(),
                "max-players": str(settings.MC_MAX_PLAYERS),
                "enable-rcon": "true"
            },
            "inspect_command_running": inspect_running,
            "inspect_command_stopped": inspect_stopped
        }

    def get_status(self) -> dict:
        container = self.get_container()
        if not container:
            return {
                "status": "not_found",
                "running": False,
                "container_id": None,
                "name": settings.MC_CONTAINER_NAME,
                "online_mode": self.get_online_mode()
            }
        
        container.reload()
        return {
            "status": container.status,
            "running": container.status == "running",
            "container_id": container.id[:12],
            "name": container.name,
            "image": container.image.tags[0] if container.image.tags else str(container.image.id),
            "online_mode": self.get_online_mode()
        }

    def start_server(self) -> dict:
        container = self.get_container()
        if not container:
            raise NotFound(f"Container '{settings.MC_CONTAINER_NAME}' not found.")
        container.reload()
        if container.status != "running":
            container.start()
            container.reload()
        return {"message": "Server started", "status": container.status}

    def stop_server(self, timeout: int = 15) -> dict:
        container = self.get_container()
        if not container:
            raise NotFound(f"Container '{settings.MC_CONTAINER_NAME}' not found.")
        container.reload()
        if container.status == "running":
            container.stop(timeout=timeout)
            container.reload()
        return {"message": "Server stopped", "status": container.status}

    def restart_server(self, timeout: int = 15) -> dict:
        container = self.get_container()
        if not container:
            raise NotFound(f"Container '{settings.MC_CONTAINER_NAME}' not found.")
        container.restart(timeout=timeout)
        container.reload()
        return {"message": "Server restarted", "status": container.status}

    def get_logs(self, tail: int = 100) -> list[str]:
        container = self.get_container()
        if not container:
            raise NotFound(f"Container '{settings.MC_CONTAINER_NAME}' not found.")
        raw_logs = container.logs(tail=tail, stdout=True, stderr=True)
        return raw_logs.decode("utf-8", errors="replace").splitlines()

docker_service = DockerService()
