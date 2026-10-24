from typing import List, Dict, Any, Optional
import os
from backend.database import db_session
from backend.services.audit_service import audit_service
import logging

logger = logging.getLogger(__name__)

class AlertService:
    @staticmethod
    def _thresholds():
        """Read thresholds dynamically so tests can override via os.environ."""
        try:
            from backend.config import settings
            cpu = float(os.environ.get("CPU_ALERT_THRESHOLD", settings.CPU_ALERT_THRESHOLD))
            mem = float(os.environ.get("MEM_ALERT_THRESHOLD", settings.MEM_ALERT_THRESHOLD))
            disk = float(os.environ.get("DISK_ALERT_THRESHOLD", settings.DISK_ALERT_THRESHOLD))
        except Exception:
            cpu = float(os.environ.get("CPU_ALERT_THRESHOLD", 80.0))
            mem = float(os.environ.get("MEM_ALERT_THRESHOLD", 90.0))
            disk = float(os.environ.get("DISK_ALERT_THRESHOLD", 85.0))
        return cpu, mem, disk

    @staticmethod
    def evaluate_metrics(metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        cpu = metrics.get("cpu_percent", 0.0)
        mem = metrics.get("memory_percent", 0.0)
        disk = metrics.get("disk_percent", 0.0)

        cpu_threshold, mem_threshold, disk_threshold = AlertService._thresholds()

        triggered = []

        if cpu > cpu_threshold:
            triggered.append({
                "alert_type": "cpu_high",
                "severity": "critical" if cpu > 95 else "warning",
                "message": f"CPU usage exceeded threshold: {cpu:.1f}% > {cpu_threshold:.1f}%",
                "value": cpu,
                "threshold": cpu_threshold
            })

        if mem > mem_threshold:
            triggered.append({
                "alert_type": "memory_high",
                "severity": "critical" if mem > 95 else "warning",
                "message": f"Memory usage exceeded threshold: {mem:.1f}% > {mem_threshold:.1f}%",
                "value": mem,
                "threshold": mem_threshold
            })

        if disk > disk_threshold:
            triggered.append({
                "alert_type": "disk_high",
                "severity": "critical" if disk > 95 else "warning",
                "message": f"Disk usage exceeded threshold: {disk:.1f}% > {disk_threshold:.1f}%",
                "value": disk,
                "threshold": disk_threshold
            })

        for alert in triggered:
            AlertService.record_alert(alert)

        return triggered

    @staticmethod
    def record_alert(alert: Dict[str, Any]) -> int:
        try:
            with db_session() as conn:
                cursor = conn.execute(
                    """
                    INSERT INTO alerts (alert_type, severity, message, value, threshold, acknowledged)
                    VALUES (?, ?, ?, ?, ?, 0)
                    """,
                    (alert["alert_type"], alert["severity"], alert["message"], alert["value"], alert["threshold"])
                )
                alert_id = cursor.lastrowid

            audit_service.log_action(
                action="alert_triggered",
                resource=f"alerts/{alert['alert_type']}",
                status="warning",
                details=alert
            )
            return alert_id
        except Exception as e:
            logger.error(f"Failed to record alert: {e}")
            return -1

    @staticmethod
    def get_alerts(unacknowledged_only: bool = False, limit: int = 50) -> List[Dict[str, Any]]:
        with db_session() as conn:
            query = "SELECT id, alert_type, severity, message, value, threshold, acknowledged, created_at FROM alerts"
            params = []
            if unacknowledged_only:
                query += " WHERE acknowledged = 0"
            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)

            cursor = conn.execute(query, tuple(params))
            return [dict(r) for r in cursor.fetchall()]

    @staticmethod
    def acknowledge_alert(alert_id: int, user_uid: Optional[str] = None) -> bool:
        with db_session() as conn:
            cursor = conn.execute("UPDATE alerts SET acknowledged = 1 WHERE id = ?", (alert_id,))
            updated = cursor.rowcount > 0

        if updated:
            audit_service.log_action(
                action="alert_acknowledged",
                resource=f"alerts/{alert_id}",
                status="success",
                uid=user_uid
            )
        return updated

alert_service = AlertService()
