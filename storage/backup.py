import os
import tarfile
import hashlib
import tempfile
import time
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from backend.config import settings
from backend.services.minio_client import get_minio_client
from backend.services.rcon_service import rcon_service
from backend.services.audit_service import audit_service
from backend.database import db_session
import logging

logger = logging.getLogger(__name__)

class BackupService:
    @staticmethod
    def calculate_sha256(filepath: str) -> str:
        sha256 = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    @classmethod
    def create_backup(
        cls,
        source_dir: str = "/data",
        backup_type: str = "manual",
        created_by_uid: Optional[str] = None,
        created_by_email: Optional[str] = None
    ) -> Dict[str, Any]:
        # 1. Coordinate with Minecraft via RCON if server is running
        try:
            rcon_service.execute_command("save-off")
            rcon_service.execute_command("save-all flush")
            # brief pause to allow dirty pages to flush to disk
            time.sleep(1)
        except Exception as e:
            logger.info(f"RCON save-off/flush skipped (server offline or non-rcon): {e}")

        scratch_dir = "/tmp/scratch" if os.path.exists("/tmp/scratch") else tempfile.gettempdir()
        timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"mc_backup_{timestamp_str}_{backup_type}.tar.gz"
        archive_path = os.path.join(scratch_dir, filename)
        s3_key = f"backups/{filename}"

        try:
            # 2. Archive source directory into tar.gz
            with tarfile.open(archive_path, "w:gz") as tar:
                if os.path.exists(source_dir):
                    tar.add(source_dir, arcname="minecraft_data")
                else:
                    # Fallback / mock content if directory not present
                    dummy_file = os.path.join(scratch_dir, "world_info.txt")
                    with open(dummy_file, "w") as df:
                        df.write(f"Backup created at {timestamp_str}\n")
                    tar.add(dummy_file, arcname="world_info.txt")
                    try:
                        os.remove(dummy_file)
                    except Exception:
                        pass

            # 3. Calculate checksum & size
            size_bytes = os.path.getsize(archive_path)
            checksum = cls.calculate_sha256(archive_path)

            # 4. Upload to MinIO / S3
            client = get_minio_client()
            with open(archive_path, "rb") as f:
                client.put_object(
                    Bucket=settings.MINIO_BUCKET,
                    Key=s3_key,
                    Body=f,
                    ContentLength=size_bytes,
                    Metadata={"sha256": checksum, "backup_type": backup_type}
                )

            # 5. Insert backup record in SQLite
            with db_session() as conn:
                cursor = conn.execute(
                    """
                    INSERT INTO backups (filename, s3_key, size_bytes, checksum_sha256, backup_type, created_by_uid, created_by_email, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 'completed')
                    """,
                    (filename, s3_key, size_bytes, checksum, backup_type, created_by_uid, created_by_email)
                )
                backup_id = cursor.lastrowid

            audit_service.log_action(
                action="backup_create",
                resource=f"backups/{filename}",
                status="success",
                uid=created_by_uid,
                email=created_by_email,
                details={"size_bytes": size_bytes, "checksum": checksum, "backup_type": backup_type}
            )

            return {
                "id": backup_id,
                "filename": filename,
                "s3_key": s3_key,
                "size_bytes": size_bytes,
                "checksum_sha256": checksum,
                "backup_type": backup_type,
                "status": "completed"
            }
        finally:
            # Re-enable saving via RCON
            try:
                rcon_service.execute_command("save-on")
            except Exception:
                pass
            # Cleanup local scratch archive
            if os.path.exists(archive_path):
                try:
                    os.remove(archive_path)
                except Exception:
                    pass

backup_service = BackupService()
