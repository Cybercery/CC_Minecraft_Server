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

    def get_status(self) -> dict:
        container = self.get_container()
        if not container:
            return {
                "status": "not_found",
                "running": False,
                "container_id": None,
                "name": settings.MC_CONTAINER_NAME
            }
        
        container.reload()
        return {
            "status": container.status,
            "running": container.status == "running",
            "container_id": container.id[:12],
            "name": container.name,
            "image": container.image.tags[0] if container.image.tags else str(container.image.id)
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
