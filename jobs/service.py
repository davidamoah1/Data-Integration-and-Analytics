"""Job service â€” orchestrates background job lifecycle.

Bridges the persistent Job model with the in-memory/Redis TaskQueue.
When a user creates a job:
  1. A Job record is persisted to the database (status=pending)
  2. A Task is enqueued in the TaskQueue
  3. A worker picks up the task, executes the handler, and updates the Job
  4. On completion, a notification is sent to the user

Job handlers are registered per job_type and receive (job_id, payload, db).
"""

from __future__ import annotations

import asyncio
import json
import logging
import threading
from collections.abc import Callable

from sqlalchemy.orm import Session as DbSession

import shared.database
from jobs.models import Job
from jobs.repositories import JobRepository
from notifications.service import NotificationService
from performance.queue import Task, TaskPriority, TaskQueue

logger = logging.getLogger(__name__)

# â”€â”€ Handler registry â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

JobHandler = Callable[[int, dict, DbSession], dict]
"""A job handler function: (job_id, payload, db) -> result_dict."""

_HANDLERS: dict[str, tuple[JobHandler, TaskPriority]] = {}


def register_handler(
    job_type: str,
    handler: JobHandler,
    priority: TaskPriority = TaskPriority.NORMAL,
) -> None:
    """Register a handler function for a job type."""
    _HANDLERS[job_type] = (handler, priority)
    logger.info("Registered job handler: %s (priority=%s)", job_type, priority.value)


def get_registered_types() -> list[str]:
    """Return all registered job type keys."""
    return list(_HANDLERS.keys())


# â”€â”€ Singleton queue â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

_queue: TaskQueue | None = None
_queue_lock = threading.Lock()


def get_task_queue() -> TaskQueue:
    """Get or create the singleton TaskQueue instance."""
    global _queue
    if _queue is None:
        with _queue_lock:
            if _queue is None:
                import config

                redis_url = getattr(config, "REDIS_URL", "") or None
                _queue = TaskQueue(redis_url=redis_url if redis_url else None)
                logger.info(
                    "TaskQueue initialized (backend: %s)",
                    "redis" if _queue.is_redis_backend else "memory",
                )
    return _queue


# â”€â”€ Job Service â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


class JobService:
    """Service for creating, tracking, and managing background jobs."""

    def __init__(self, db: DbSession):
        self.db = db
        self.repo = JobRepository(db)

    # â”€â”€ Create â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    async def create_job(
        self,
        organization_id: int,
        user_id: int | None,
        job_type: str,
        name: str,
        *,
        description: str | None = None,
        payload: dict | None = None,
        max_retries: int = 3,
        idempotency_key: str | None = None,
    ) -> Job:
        """Create a job record and enqueue it for processing.

        If *idempotency_key* is provided and a pending/running/completed job
        with the same key already exists for this organization, that existing
        job is returned instead of creating a duplicate. Failed/cancelled jobs
        with the same key are allowed to be re-created (i.e. retried).

        Returns the persisted Job instance (with id).

        Raises ``RuntimeError`` if the job cannot be enqueued (e.g. Redis
        connection failure). The caller should catch this and return an
        appropriate error to the user instead of leaving the job stuck at
        "pending".
        """
        if job_type not in _HANDLERS:
            raise ValueError(
                f"No handler registered for job type '{job_type}'. "
                f"Available: {', '.join(get_registered_types())}"
            )

        # Idempotency check — return existing active/completed job if present
        if idempotency_key:
            existing = self.repo.find_by_idempotency_key(organization_id, idempotency_key)
            if existing:
                logger.info(
                    "Job %d returned (idempotency key '%s' already active/completed)",
                    existing.id,
                    idempotency_key,
                )
                return existing

        job = self.repo.create(
            organization_id=organization_id,
            user_id=user_id,
            job_type=job_type,
            name=name,
            description=description,
            status="pending",
            progress=0.0,
            payload=json.dumps(payload) if payload else None,
            max_retries=max_retries,
            idempotency_key=idempotency_key,
        )
        self.db.commit()
        logger.info(
            "JOB_CREATED job_id=%d job_type=%s name='%s' org_id=%d",
            job.id,
            job_type,
            name,
            organization_id,
        )

        # Enqueue in task queue
        queue = get_task_queue()
        handler, priority = _HANDLERS[job_type]
        task = Task(
            name=f"{job_type}:{job.id}",
            func=_run_job_wrapper,
            args=(job.id, job_type),
            priority=priority,
            metadata={"job_id": job.id, "job_type": job_type},
            max_retries=max_retries,
        )
        job.queue_task_id = task.id
        self.repo.update(job.id, queue_task_id=task.id)
        self.db.commit()

        # Enqueue synchronously — await the result before returning so
        # enqueue failures are caught immediately and the caller can
        # return an appropriate error to the user.
        logger.info(
            "JOB_ENQUEUE_STARTED job_id=%d queue_backend=%s",
            job.id,
            "redis" if queue.is_redis_backend else "memory",
        )
        try:
            await queue.enqueue(task)
        except Exception as e:
            logger.error("JOB_ENQUEUE_FAILED job_id=%d error='%s: %s'", job.id, type(e).__name__, e)
            # Mark the job as failed so it doesn't stay stuck at pending
            try:
                self.repo.mark_failed(
                    job.id,
                    f"Failed to enqueue job for background processing: {e}",
                )
                self.db.commit()
            except Exception:
                logger.exception("Failed to mark job %d as failed after enqueue error", job.id)
            raise RuntimeError(f"Failed to enqueue job: {e}") from e

        logger.info("JOB_ENQUEUE_SUCCESS job_id=%d", job.id)
        logger.info("Job %d created and enqueued: %s '%s'", job.id, job_type, name)
        return job

    def create_job_sync(
        self,
        organization_id: int,
        user_id: int | None,
        job_type: str,
        name: str,
        *,
        description: str | None = None,
        payload: dict | None = None,
        max_retries: int = 3,
        idempotency_key: str | None = None,
    ) -> Job:
        """Create a job record and enqueue it for processing (sync fallback).

        If *idempotency_key* is provided and a pending/running/completed job
        with the same key already exists for this organization, that existing
        job is returned instead of creating a duplicate. Failed/cancelled jobs
        with the same key are allowed to be re-created (i.e. retried).

        Returns the persisted Job instance (with id).

        Raises ``RuntimeError`` if the job cannot be enqueued (e.g. Redis
        connection failure). The caller should catch this and return an
        appropriate error to the user instead of leaving the job stuck at
        "pending".
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self.create_job(
                    organization_id,
                    user_id,
                    job_type,
                    name,
                    description=description,
                    payload=payload,
                    max_retries=max_retries,
                    idempotency_key=idempotency_key,
                )
            )
        finally:
            loop.close()

    # â”€â”€ Read â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def get_job(self, job_id: int, organization_id: int) -> Job | None:
        return self.repo.get_by_org(job_id, organization_id)

    def list_jobs(
        self,
        organization_id: int,
        *,
        status: str | None = None,
        job_type: str | None = None,
        user_id: int | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Job]:
        return self.repo.list_by_org(
            organization_id,
            status=status,
            job_type=job_type,
            user_id=user_id,
            limit=limit,
            offset=offset,
        )

    def list_active(self, organization_id: int) -> list[Job]:
        return self.repo.list_active(organization_id)

    def get_summary(self, organization_id: int) -> dict:
        counts = self.repo.count_by_status(organization_id)
        total = sum(counts.values())
        return {
            "total": total,
            "pending": counts.get("pending", 0),
            "running": counts.get("running", 0),
            "completed": counts.get("completed", 0),
            "failed": counts.get("failed", 0),
            "cancelled": counts.get("cancelled", 0),
        }

    # â”€â”€ Cancel â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def cancel_job(self, job_id: int, organization_id: int) -> Job | None:
        job = self.get_job(job_id, organization_id)
        if not job:
            return None
        if job.status not in ("pending", "running"):
            raise ValueError(f"Cannot cancel job in '{job.status}' state.")

        # Try to cancel in the queue
        queue = get_task_queue()
        if job.queue_task_id:
            queue.cancel_task(job.queue_task_id)

        self.repo.mark_cancelled(job_id)
        self.db.commit()
        logger.info("Job %d cancelled", job_id)
        return self.repo.get_by_id(job_id)

    # â”€â”€ Retry â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    async def retry_job(self, job_id: int, organization_id: int) -> Job | None:
        job = self.get_job(job_id, organization_id)
        if not job:
            return None
        if job.status not in ("failed", "cancelled"):
            raise ValueError(f"Can only retry failed or cancelled jobs (current: '{job.status}').")

        self.repo.update(
            job_id,
            status="pending",
            progress=0.0,
            error=None,
            result=None,
            started_at=None,
            completed_at=None,
        )
        self.db.commit()

        # Re-enqueue
        queue = get_task_queue()
        handler, priority = _HANDLERS.get(job.job_type, (None, TaskPriority.NORMAL))
        if handler:
            task = Task(
                name=f"{job.job_type}:{job.id}",
                func=_run_job_wrapper,
                args=(job.id, job.job_type),
                priority=priority,
                metadata={"job_id": job.id, "job_type": job.job_type},
                max_retries=job.max_retries,
            )
            self.repo.update(job_id, queue_task_id=task.id)
            self.db.commit()

            logger.info("JOB_RETRY_ENQUEUE_STARTED job_id=%d", job_id)
            try:
                await queue.enqueue(task)
            except Exception as e:
                logger.error(
                    "JOB_RETRY_ENQUEUE_FAILED job_id=%d error='%s: %s'", job_id, type(e).__name__, e
                )
                try:
                    self.repo.mark_failed(
                        job_id,
                        f"Failed to re-enqueue job for background processing: {e}",
                    )
                    self.db.commit()
                except Exception:
                    logger.exception(
                        "Failed to mark job %d as failed after retry enqueue error", job_id
                    )
                raise RuntimeError(f"Failed to re-enqueue job: {e}") from e

            logger.info("JOB_RETRY_ENQUEUE_SUCCESS job_id=%d", job_id)

        logger.info("Job %d retried", job_id)
        return self.repo.get_by_id(job_id)


# â”€â”€ Job execution wrapper â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


def _run_job_wrapper(job_id: int, job_type: str) -> dict:
    """Wrapper that executes a job handler with a fresh DB session.

    This function is called by the WorkerPool. It:
      1. Creates a fresh DB session
      2. Marks the job as running
      3. Calls the registered handler
      4. Updates the job status (completed/failed)
      5. Sends a notification to the user
    """
    engine = shared.database.get_engine()
    factory = shared.database.get_session_factory(engine)
    db = factory()

    try:
        repo = JobRepository(db)
        job = repo.get_by_id(job_id)
        if not job:
            logger.error("JOB_NOT_FOUND job_id=%d", job_id)
            return {"error": "Job not found"}

        if job.status == "cancelled":
            logger.info("JOB_SKIPPED job_id=%d reason=cancelled", job_id)
            return {"skipped": "cancelled"}

        # Mark running
        repo.mark_running(job_id)
        repo.update_heartbeat(job_id)
        db.commit()
        logger.info(
            "JOB_STARTED job_id=%d job_type=%s name='%s' org_id=%d user_id=%s",
            job_id,
            job_type,
            job.name,
            job.organization_id,
            job.user_id,
        )

        # Get handler
        handler_entry = _HANDLERS.get(job_type)
        if not handler_entry:
            error_msg = f"No handler for job type '{job_type}'"
            repo.mark_failed(job_id, error_msg)
            db.commit()
            logger.error("JOB_FAILED job_id=%d error='%s'", job_id, error_msg)
            return {"error": error_msg}

        handler, _ = handler_entry

        # Parse payload
        payload = json.loads(job.payload) if job.payload else {}

        # Execute
        logger.info(
            "JOB_PROGRESS job_id=%d status=running progress=0 message='Executing handler'", job_id
        )
        logger.info(
            "JOB_HANDLER_START job_id=%d job_type=%s handler=%s",
            job_id,
            job_type,
            f"{handler.__module__}.{handler.__qualname__}",
        )
        result = handler(job_id, payload, db)
        logger.info(
            "JOB_HANDLER_DONE job_id=%d job_type=%s result_keys=%s",
            job_id,
            job_type,
            list(result.keys()) if isinstance(result, dict) else type(result).__name__,
        )

        # Mark completed. default=str guards against handlers returning
        # numpy scalar types (bool_, int64, float64, ...) from pandas/numpy
        # operations - e.g. dataset_workflow's stage results - which the
        # stdlib json encoder cannot serialize directly.
        result_json = json.dumps(result, default=str) if result else None
        repo.mark_completed(job_id, result=result_json)
        db.commit()
        logger.info(
            "JOB_COMPLETED job_id=%d job_type=%s name='%s' org_id=%d",
            job_id,
            job_type,
            job.name,
            job.organization_id,
        )

        # Notify user
        if job.user_id:
            try:
                NotificationService(db).send_in_app(
                    subject=f"Job completed: {job.name}",
                    body=f"Your '{job.name}' task has completed successfully.",
                    user_id=job.user_id,
                    org_id=job.organization_id,
                )
            except Exception as e:
                logger.warning("Failed to send completion notification for job %d: %s", job_id, e)

        logger.info("Job %d completed successfully", job_id)
        return result or {}

    except Exception as e:
        logger.exception(
            "JOB_FAILED job_id=%d job_type=%s error_type=%s error='%s'",
            job_id,
            job_type,
            type(e).__name__,
            e,
        )
        try:
            db.rollback()
            repo = JobRepository(db)
            repo.mark_failed(job_id, str(e))
            db.commit()

            # Notify user of failure
            job = repo.get_by_id(job_id)
            if job and job.user_id:
                NotificationService(db).send_in_app(
                    subject=f"Job failed: {job.name}",
                    body=f"Your '{job.name}' task failed: {e}",
                    user_id=job.user_id,
                    org_id=job.organization_id,
                )
        except Exception:
            logger.exception("Failed to mark job %d as failed", job_id)
        return {"error": str(e)}

    finally:
        db.close()


# â”€â”€ Progress helper â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


def update_job_progress(job_id: int, progress: float, message: str | None = None) -> None:
    """Update job progress from within a handler.

    Uses a short-lived session so it doesn't interfere with the handler's session.
    Also updates the heartbeat timestamp so the stale-job watchdog knows the
    worker is still alive.
    """
    logger.info(
        "JOB_PROGRESS_UPDATE job_id=%d progress=%.2f message='%s'",
        job_id,
        progress,
        message or "",
    )
    engine = shared.database.get_engine()
    factory = shared.database.get_session_factory(engine)
    db = factory()
    try:
        repo = JobRepository(db)
        repo.update_progress(job_id, progress, message)
        repo.update_heartbeat(job_id)
        db.commit()
    finally:
        db.close()


def update_heartbeat(job_id: int) -> None:
    """Update the heartbeat timestamp for a running job.

    Can be called periodically from long-running handlers that don't update
    progress on every iteration.
    """
    engine = shared.database.get_engine()
    factory = shared.database.get_session_factory(engine)
    db = factory()
    try:
        repo = JobRepository(db)
        repo.update_heartbeat(job_id)
        db.commit()
    finally:
        db.close()
