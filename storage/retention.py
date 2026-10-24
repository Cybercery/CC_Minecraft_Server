from typing import List, Dict, Any
from backend.config import settings
from backend.services.minio_client import get_minio_client
from backend.services.audit_service import audit_service
from backend.database import db_session
import logging

logger = logging.getLogger(__name__)

class RetentionService:
    @classmethod
    def apply_retention(cls, keep_count: int = None) -> List[Dict[str, Any]]:
        limit = keep_count or settings.BACKUP_RETENTION_COUNT or 10

        with db_session() as conn:
            cursor = conn.execute(
                """
                SELECT id, filename, s3_key, created_at
                FROM backups
                ORDER BY created_at DESC
                """
            )
            all_backups = [dict(r) for r in cursor.fetchall()]

        if len(all_backups) <= limit:
            return []

        to_delete = all_backups[limit:]
        deleted_records = []
        client = get_minio_client()

        for item in to_delete:
            backup_id = item["id"]
            s3_key = item["s3_key"]
            filename = item["filename"]

            # Delete from MinIO
            try:
                client.delete_object(Bucket=settings.MINIO_BUCKET, Key=s3_key)
            except Exception as e:
                logger.warning(f"Could not delete S3 object {s3_key}: {e}")

            # Delete from DB
            with db_session() as conn:
                conn.execute("DELETE FROM backups WHERE id = ?", (backup_id,))

            audit_service.log_action(
                action="backup_retention_purge",
                resource=f"backups/{filename}",
                status="success",
                details={"backup_id": backup_id, "s3_key": s3_key}
            )

            deleted_records.append(item)

        return deleted_records

retention_service = RetentionService()
