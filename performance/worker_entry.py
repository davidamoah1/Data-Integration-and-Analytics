"""Worker entry point for background task processing.

Run as: python -m performance.worker_entry

Starts a WorkerPool that processes tasks from the queue.
Uses Redis as the queue backend when REDIS_URL is set,
otherwise falls back to in-memory queue.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import os
import signal

from jobs.handlers import register_builtin_handlers
from jobs.watchdog import run_watchdog
from performance.queue import TaskQueue
from performance.workers import WorkerPool

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("performance.worker_entry")


async def run_workers():
    """Start the worker pool and keep it running."""
    logger.info("WORKER_STARTUP_BEGIN pid=%s", os.getpid())

    # Register handlers
    register_builtin_handlers()
    from jobs.service import get_registered_types

    registered = get_registered_types()
    logger.info(
        "WORKER_HANDLERS_REGISTERED count=%d types=%s", len(registered), ", ".join(registered)
    )

    # Check Redis connectivity
    redis_url = os.getenv("REDIS_URL", "")
    if redis_url:
        logger.info("WORKER_REDIS_CONFIGURED url_present=true")
    else:
        logger.warning(
            "WORKER_REDIS_CONFIGURED url_present=false — using in-memory queue (jobs will not survive restart)"
        )

    # Check DB connectivity
    try:
        import shared.database

        engine = shared.database.get_engine()
        from sqlalchemy import text

        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("WORKER_DB_CONNECTED ok=true")
    except Exception as e:
        logger.error("WORKER_DB_CONNECTED ok=false error='%s: %s'", type(e).__name__, e)
        raise

    min_workers = int(os.getenv("WORKER_MIN_WORKERS") or "2")
    max_workers = int(os.getenv("WORKER_MAX_WORKERS") or "20")

    queue = TaskQueue(redis_url=redis_url if redis_url else None)
    logger.info(
        "WORKER_QUEUE_INITIALIZED backend=%s redis_connected=%s",
        "redis" if queue.is_redis_backend else "memory",
        queue.is_redis_backend,
    )

    pool = WorkerPool(
        task_queue=queue,
        min_workers=min_workers,
        max_workers=max_workers,
    )

    # Handle graceful shutdown
    stop_event = asyncio.Event()

    def signal_handler():
        logger.info("Received shutdown signal, stopping workers...")
        stop_event.set()

    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, signal_handler)
        except NotImplementedError:
            # Windows doesn't support add_signal_handler
            pass

    await pool.start()
    logger.info(
        "WORKER_POOL_RUNNING min_workers=%d max_workers=%d backend=%s",
        min_workers,
        max_workers,
        "redis" if queue.is_redis_backend else "memory",
    )

    # Start the stale-job watchdog alongside the worker pool so stuck
    # jobs are automatically detected and marked as failed.
    watchdog_task = asyncio.create_task(run_watchdog(stop_event))
    logger.info("Stale-job watchdog task created.")

    # Wait for shutdown signal
    await stop_event.wait()

    watchdog_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await watchdog_task

    await pool.stop()
    logger.info("Workers stopped, exiting.")


def main():
    """Entry point."""
    asyncio.run(run_workers())


if __name__ == "__main__":
    main()
