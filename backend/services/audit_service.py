import json
from typing import Optional, Dict, Any
from backend.database import db_session
import logging

logger = logging.getLogger(__name__)

class AuditService:
    @staticmethod
    def log_action(
        action: str,
        resource: str,
        status: str,
        uid: Optional[str] = None,
        email: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        try:
            details_json = json.dumps(details) if details else None
            with db_session() as conn:
                conn.execute(
                    """
                    INSERT INTO audit_logs (uid, email, action, resource, status, details)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (uid, email, action, resource, status, details_json)
                )
        except Exception as e:
            logger.error(f"Failed to record audit log: {e}")

    @staticmethod
    def list_logs(limit: int = 100, offset: int = 0) -> list[dict]:
        with db_session() as conn:
            cursor = conn.execute(
                """
                SELECT id, uid, email, action, resource, status, details, timestamp
                FROM audit_logs
                ORDER BY timestamp DESC
                LIMIT ? OFFSET ?
                """,
                (limit, offset)
            )
            rows = cursor.fetchall()
            logs = []
            for r in rows:
                item = dict(r)
                if item["details"]:
                    try:
                        item["details"] = json.loads(item["details"])
                    except Exception:
                        pass
                logs.append(item)
            return logs

audit_service = AuditService()
