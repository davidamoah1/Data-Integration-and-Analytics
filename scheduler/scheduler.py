"""APScheduler-based pipeline scheduler.

Replaces the basic schedule library with APScheduler for:
  - Cron-style scheduling
  - Job persistence
  - Missed job handling
  - Graceful shutdown

Usage:
    python scheduler/scheduler.py

Configuration:
    PIPELINE_RUN_TIME env var (24h format, e.g. "08:00")
"""

import sys
import os
import signal

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

from config import PIPELINE_RUN_TIME
from etl.logging_config import logger
from services.etl_service import ETLService

scheduler = BlockingScheduler(job_defaults={"max_instances": 1, "coalesce": True})
_etl_service = ETLService()


def scheduled_job():
    """Execute the ETL pipeline."""
    logger.info("Scheduler triggered the pipeline.")
    print("\nScheduler triggered the pipeline.")
    try:
        metrics = _etl_service.run_pipeline()
        logger.info(f"Scheduled pipeline completed: {metrics}")
    except Exception as e:
        logger.error(f"Scheduled pipeline failed: {e}")


def job_listener(event):
    """Log job execution results.

    Args:
        event: APScheduler event.
    """
    if event.code == EVENT_JOB_EXECUTED:
        logger.info(f"Scheduler job executed successfully: {event.job_id}")
    elif event.code == EVENT_JOB_ERROR:
        logger.error(f"Scheduler job failed: {event.job_id} - {event.exception}")


# Parse PIPELINE_RUN_TIME (HH:MM format)
try:
    hour, minute = PIPELINE_RUN_TIME.split(":")
    trigger = CronTrigger(hour=int(hour), minute=int(minute))
except ValueError:
    logger.warning(f"Invalid PIPELINE_RUN_TIME format: {PIPELINE_RUN_TIME}. Defaulting to 08:00.")
    trigger = CronTrigger(hour=8, minute=0)

scheduler.add_listener(job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
scheduler.add_job(
    scheduled_job,
    trigger=trigger,
    id="etl_pipeline",
    name="ETL Pipeline Daily Run",
    replace_existing=True,
)


def graceful_shutdown(signum, frame):
    """Handle SIGINT/SIGTERM for clean shutdown."""
    logger.info("Received shutdown signal, stopping scheduler...")
    scheduler.shutdown(wait=False)
    sys.exit(0)


signal.signal(signal.SIGINT, graceful_shutdown)
signal.signal(signal.SIGTERM, graceful_shutdown)


if __name__ == "__main__":
    logger.info(f"Scheduler started. Pipeline will run daily at {PIPELINE_RUN_TIME}.")
    print(f"Scheduler is running. Pipeline will execute daily at {PIPELINE_RUN_TIME}.")
    print("Press Ctrl+C to stop.\n")
    scheduler.start()
