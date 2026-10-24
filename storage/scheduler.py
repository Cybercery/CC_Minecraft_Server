from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from backend.config import settings
from storage.backup import backup_service
from storage.retention import retention_service
import logging

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()

def scheduled_backup_job():
    logger.info("Executing scheduled automated backup job...")
    try:
        res = backup_service.create_backup(backup_type="scheduled")
        logger.info(f"Scheduled backup created successfully: {res.get('filename')}")
        # Apply retention policy immediately after backup
        purged = retention_service.apply_retention()
        if purged:
            logger.info(f"Retention policy purged {len(purged)} older backups.")
    except Exception as e:
        logger.error(f"Scheduled backup failed: {e}")

def start_backup_scheduler():
    cron_expr = settings.BACKUP_SCHEDULE_CRON or "0 3 * * *"
    try:
        # e.g., "0 3 * * *" -> minute='0', hour='3', day='*', month='*', day_of_week='*'
        parts = cron_expr.split()
        if len(parts) == 5:
            trigger = CronTrigger(
                minute=parts[0],
                hour=parts[1],
                day=parts[2],
                month=parts[3],
                day_of_week=parts[4]
            )
            scheduler.add_job(scheduled_backup_job, trigger, id="automated_backup_job", replace_existing=True)
            if not scheduler.running:
                scheduler.start()
            logger.info(f"Backup scheduler started with cron: {cron_expr}")
    except Exception as e:
        logger.error(f"Failed to start backup scheduler: {e}")
