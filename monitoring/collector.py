import psutil
import shutil
import os
from datetime import datetime, timezone
from typing import Dict, Any
from backend.services.docker_service import docker_service
from backend.services.rcon_service import rcon_service
from backend.database import db_session
import logging

logger = logging.getLogger(__name__)

class MetricsCollector:
    @staticmethod
    def collect_current_metrics() -> Dict[str, Any]:
        # 1. System CPU & Memory
        cpu_percent = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory()

        # 2. Disk usage (/data if present, else root directory)
        check_path = "/data" if os.path.exists("/data") else "."
        disk = shutil.disk_usage(check_path)
        disk_percent = round((disk.used / disk.total) * 100, 2) if disk.total > 0 else 0.0

        # 3. Minecraft container status & players
        is_running = False
        online_players = 0
        try:
            status = docker_service.get_status()
            is_running = status.get("running", False)
            if is_running:
                players_data = rcon_service.get_player_list()
                online_players = players_data.get("online_count", 0)
        except Exception as e:
            logger.debug(f"Collector status/rcon check: {e}")

        return {
            "cpu_percent": cpu_percent,
            "memory_bytes": mem.used,
            "memory_total_bytes": mem.total,
            "memory_percent": mem.percent,
            "disk_used_bytes": disk.used,
            "disk_total_bytes": disk.total,
            "disk_percent": disk_percent,
            "online_players": online_players,
            "is_running": 1 if is_running else 0
        }

    @classmethod
    def record_snapshot(cls) -> Dict[str, Any]:
        metrics = cls.collect_current_metrics()
        now_iso = datetime.now(timezone.utc).isoformat()
        try:
            with db_session() as conn:
                conn.execute(
                    """
                    INSERT INTO server_metrics (
                        cpu_percent, memory_bytes, memory_percent,
                        disk_used_bytes, disk_total_bytes, disk_percent,
                        online_players, is_running, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        metrics["cpu_percent"],
                        metrics["memory_bytes"],
                        metrics["memory_percent"],
                        metrics["disk_used_bytes"],
                        metrics["disk_total_bytes"],
                        metrics["disk_percent"],
                        metrics["online_players"],
                        metrics["is_running"],
                        now_iso
                    )
                )
        except Exception as e:
            logger.error(f"Failed to record metrics snapshot: {e}")
        return metrics

collector = MetricsCollector()
