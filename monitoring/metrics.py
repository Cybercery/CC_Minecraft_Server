from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from backend.config import settings
from backend.database import db_session
from monitoring.collector import collector
import logging

logger = logging.getLogger(__name__)

class MetricsService:
    @staticmethod
    def get_latest_metrics() -> Dict[str, Any]:
        return collector.collect_current_metrics()

    @staticmethod
    def get_historical_metrics(hours: int = 24, limit: int = 200) -> List[Dict[str, Any]]:
        since_time = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
        with db_session() as conn:
            cursor = conn.execute(
                """
                SELECT id, cpu_percent, memory_bytes, memory_percent,
                       disk_used_bytes, disk_total_bytes, disk_percent,
                       online_players, is_running, timestamp
                FROM server_metrics
                WHERE timestamp >= ?
                ORDER BY timestamp ASC
                LIMIT ?
                """,
                (since_time, limit)
            )
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    @staticmethod
    def purge_old_metrics(retention_days: Optional[int] = None) -> int:
        days = retention_days or settings.METRICS_RETENTION_DAYS or 7
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        with db_session() as conn:
            cursor = conn.execute("DELETE FROM server_metrics WHERE timestamp < ?", (cutoff,))
            deleted = cursor.rowcount
        return deleted

metrics_service = MetricsService()
