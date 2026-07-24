"""Scheduled report runner using APScheduler.

The runner reads active `ScheduledReport` records from the database and
registers APScheduler cron jobs that generate AI reports. Each job creates a
new DB session for thread safety.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

import shared.database
from ai.engines.report_writer import AIReportWriter
from etl.logging_config import logger
from notifications.service import NotificationService
from scheduler.models import ScheduledReport

_active_scheduler: ReportScheduler | None = None


@contextmanager
def _session():
    """Yield a short-lived DB session for a background job."""
    engine = shared.database.get_engine()
    factory = shared.database.get_session_factory(engine)
    db = factory()
    try:
        yield db
    finally:
        db.close()


def _run_scheduled_report(report_id: int) -> None:
    """Generate the report for a scheduled report definition."""
    with _session() as db:
        report_def = db.query(ScheduledReport).filter(ScheduledReport.id == report_id).first()
        if not report_def or not report_def.is_active:
            return
        try:
            writer = AIReportWriter(db)
            result = writer.generate_report(
                report_type=report_def.report_type,
                title=report_def.title,
                user_id=report_def.user_id,
                **(report_def.parameters or {}),
            )
            report_def.last_run_at = datetime.now(timezone.utc)
            db.commit()
            NotificationService(db).send_in_app(
                subject=f"Scheduled report ready: {report_def.name}",
                body=f"Report '{result.get('title')}' generated successfully.",
                user_id=report_def.user_id,
                org_id=report_def.organization_id,
            )
            logger.info("Scheduled report %s generated: %s", report_id, result.get("report_id"))
        except Exception as exc:
            logger.exception("Scheduled report %s failed: %s", report_id, exc)
            report_def.last_run_at = datetime.now(timezone.utc)
            db.commit()


class ReportScheduler:
    """Manages scheduled report jobs."""

    def __init__(self) -> None:
        """Initialize a background scheduler for reports."""
        self.scheduler = BackgroundScheduler()

    def sync_jobs(self) -> None:
        """Reload scheduled report jobs from the database."""
        with _session() as db:
            active = db.query(ScheduledReport).filter(ScheduledReport.is_active.is_(True)).all()
        active_ids = {r.id for r in active}

        for report in active:
            job_id = f"report_{report.id}"
            try:
                minute, hour, day, month, day_of_week = report.cron.split()
                trigger = CronTrigger(
                    minute=minute,
                    hour=hour,
                    day=day,
                    month=month,
                    day_of_week=day_of_week,
                )
            except ValueError:
                logger.warning("Invalid cron expression for report %s: %s", report.id, report.cron)
                continue
            self.scheduler.add_job(
                _run_scheduled_report,
                trigger=trigger,
                id=job_id,
                args=(report.id,),
                replace_existing=True,
                max_instances=1,
            )

        # Remove jobs for deactivated/deleted reports
        for job in list(self.scheduler.get_jobs()):
            if job.id.startswith("report_"):
                try:
                    job_report_id = int(job.id.split("_", 1)[1])
                    if job_report_id not in active_ids:
                        self.scheduler.remove_job(job.id)
                except ValueError:
                    pass

    def start(self) -> None:
        """Start the scheduler and sync jobs if not in test mode."""
        global _active_scheduler
        if os.getenv("PYTEST_RUNNING"):
            return
        self.sync_jobs()
        self.scheduler.start()
        _active_scheduler = self

    def shutdown(self) -> None:
        """Stop the scheduler."""
        global _active_scheduler
        self.scheduler.shutdown(wait=False)
        _active_scheduler = None

    @staticmethod
    def is_running() -> bool:
        """Return whether an active scheduler instance is running."""
        return _active_scheduler is not None and _active_scheduler.scheduler.running
