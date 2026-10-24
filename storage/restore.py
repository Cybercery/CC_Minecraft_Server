import os
import tarfile
import tempfile
import hashlib
from typing import Optional, Dict, Any
from backend.config import settings
from backend.services.minio_client import get_minio_client
from backend.services.docker_service import docker_service
from backend.services.audit_service import audit_service
from backend.database import db_session
from storage.backup import BackupService
import logging

logger = logging.getLogger(__name__)

class RestoreService:
    @classmethod
    def restore_backup(
        cls,
        backup_id: int,
        target_dir: str = "/data",
        restored_by_uid: Optional[str] = None,
        restored_by_email: Optional[str] = None
    ) -> Dict[str, Any]:
        with db_session() as conn:
            cursor = conn.execute("SELECT id, filename, s3_key, checksum_sha256 FROM backups WHERE id = ?", (backup_id,))
            backup_record = cursor.fetchone()

        if not backup_record:
            raise ValueError(f"Backup with ID {backup_id} not found.")

        s3_key = backup_record["s3_key"]
        expected_checksum = backup_record["checksum_sha256"]
        filename = backup_record["filename"]

        scratch_dir = "/tmp/scratch" if os.path.exists("/tmp/scratch") else tempfile.gettempdir()
        download_path = os.path.join(scratch_dir, f"restore_{filename}")

        # 1. Stop Minecraft container safely if running
        stopped_for_restore = False
        try:
            status = docker_service.get_status()
            if status.get("running"):
                docker_service.stop_server(timeout=20)
                stopped_for_restore = True
        except Exception as e:
            logger.warning(f"Could not check/stop container before restore: {e}")

        try:
            # 2. Download archive from MinIO
            client = get_minio_client()
            client.download_file(settings.MINIO_BUCKET, s3_key, download_path)

            # 3. Verify integrity
            actual_checksum = BackupService.calculate_sha256(download_path)
            if actual_checksum != expected_checksum:
                raise ValueError(f"Integrity check failed! Expected {expected_checksum}, got {actual_checksum}")

            # 4. Extract archive to target directory safely
            os.makedirs(target_dir, exist_ok=True)
            with tarfile.open(download_path, "r:gz") as tar:
                # Security filter against path traversal attacks
                for member in tar.getmembers():
                    if member.name.startswith("/") or ".." in member.name:
                        raise ValueError(f"Security check failed: dangerous member name {member.name}")
                tar.extractall(path=target_dir)

            audit_service.log_action(
                action="backup_restore",
                resource=f"backups/{filename}",
                status="success",
                uid=restored_by_uid,
                email=restored_by_email,
                details={"backup_id": backup_id, "filename": filename}
            )

            return {
                "success": True,
                "message": f"Successfully restored backup {filename}",
                "backup_id": backup_id,
                "target_dir": target_dir
            }
        finally:
            if os.path.exists(download_path):
                try:
                    os.remove(download_path)
                except Exception:
                    pass
            # 5. Restart container if it was stopped for restore
            if stopped_for_restore:
                try:
                    docker_service.start_server()
                except Exception as e:
                    logger.error(f"Failed to restart Minecraft server after restore: {e}")

restore_service = RestoreService()
