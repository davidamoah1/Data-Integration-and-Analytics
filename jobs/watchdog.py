"""Stale-job watchdog.

Periodically scans the ``background_jobs`` table for jobs that have been
``pending`` or ``running`` beyond configurable thresholds and marks them
``failed`` so they never stay stuck indefinitely.

Intended to run inside the dedicated worker process (``worker_entry.py``)
alongside the ``WorkerPool``, but can also be started in the web service
when no dedicated worker exists.
"""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timedelta, timezone

import shared.database
from jobs.repositories import JobRepository

logger = logging.getLogger(__name__)

# Configurable via environment variables so operators can tune without code changes.
PENDING_TIMEOUT_SECONDS = int(os.getenv("JOB_PENDING_TIMEOUT_SECONDS", "300"))  # 5 min
RUNNING_TIMEOUT_SECONDS = int(os.getenv("JOB_RUNNING_TIMEOUT_SECONDS", "1800"))  # 30 min
WATCHDOG_INTERVAL_SECONDS = int(os.getenv("JOB_WATCHDOG_INTERVAL_SECONDS", "60"))  # check every 60s


async def run_watchdog(stop_event: asyncio.Event | None = None) -> None:
    """Run the stale-job watchdog loop.

    Call via ``asyncio.create_task(run_watchdog())`` inside a long-lived
    process (the worker entry point).  The loop exits when *stop_event*
    is set or the process receives a cancellation signal.
    """
    logger.info(
        "Stale-job watchdog started (pending_timeout=%ds, running_timeout=%ds, interval=%ds)",
        PENDING_TIMEOUT_SECONDS,
        RUNNING_TIMEOUT_SECONDS,
        WATCHDOG_INTERVAL_SECONDS,
    )

    while True:
        if stop_event is not None and stop_event.is_set():
            logger.info("Stale-job watchdog stopping (stop event set).")
            break

        try:
            await _sweep_once()
        except asyncio.CancelledError:
            logger.info("Stale-job watchdog cancelled.")
            break
        except Exception:
            logger.exception("Stale-job watchdog sweep failed")

        try:
            await asyncio.sleep(WATCHDOG_INTERVAL_SECONDS)
        except asyncio.CancelledError:
            logger.info("Stale-job watchdog cancelled during sleep.")
            break


async def _sweep_once() -> dict:
    """Run a single sweep of the stale-job watchdog.

    Returns a summary dict for logging/testing.
    """
    engine = shared.database.get_engine()
    factory = shared.database.get_session_factory(engine)
    db = factory()

    now = datetime.now(timezone.utc)
    pending_threshold = now - timedelta(seconds=PENDING_TIMEOUT_SECONDS)
    running_threshold = now - timedelta(seconds=RUNNING_TIMEOUT_SECONDS)

    swept = {"pending": 0, "running": 0}

    try:
        repo = JobRepository(db)

        # --- Stale pending jobs ---
        stale_pending = repo.find_stale_pending(pending_threshold)
        for job in stale_pending:
            error_msg = (
                "Background worker did not pick up this job within "
                f"{PENDING_TIMEOUT_SECONDS}s. The worker may be offline or "
                "overloaded. Please try again."
            )
            repo.mark_failed(job.id, error_msg)
            logger.warning(
                "JOB_TIMEOUT job_id=%d status=pending age=%ds error='%s'",
                job.id,
                int((now - job.created_at.replace(tzinfo=timezone.utc)).total_seconds()),
                error_msg,
            )
            swept["pending"] += 1

        # --- Stale running jobs (no heartbeat) ---
        stale_running = repo.find_stale_running(running_threshold)
        for job in stale_running:
            error_msg = (
                "Background worker stopped responding while processing this job "
                f"(no heartbeat for {RUNNING_TIMEOUT_SECONDS}s). The worker may "
                "have crashed or been killed. Please try again."
            )
            repo.mark_failed(job.id, error_msg)
            logger.warning(
                "JOB_TIMEOUT job_id=%d status=running heartbeat_age=%ss error='%s'",
                job.id,
                int((now - (job.last_heartbeat_at or job.started_at).replace(tzinfo=timezone.utc)).total_seconds()),
                error_msg,
            )
            swept["running"] += 1

        if swept["pending"] or swept["running"]:
            db.commit()
            logger.info(
                "Watchdog swept %d stale pending, %d stale running jobs",
                swept["pending"],
                swept["running"],
            )
    finally:
        db.close()

    return swept
