"""ORM models for the background job system."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.mysql import LONGTEXT

from shared.database import Base, BigInt


class Job(Base):
    """A persistent background job tracked across the platform.

    Lifecycle: pending â†’ running â†’ completed | failed | cancelled

    Job types:
      - etl_run        â€” ETL pipeline execution
      - ocr_batch      â€” OCR processing for capture batches
      - report_gen     â€” AI report generation
      - data_import    â€” Large dataset imports
      - export         â€” Data exports
      - custom         â€” Custom user-defined tasks
    """

    __tablename__ = "background_jobs"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    organization_id = Column(BigInt, nullable=False, index=True)
    user_id = Column(BigInt, nullable=True, index=True)

    # Identification
    job_type = Column(String(64), nullable=False, index=True)  # etl_run, ocr_batch, etc.
    name = Column(String(255), nullable=False)  # human-readable label
    description = Column(Text, nullable=True)

    # Status tracking
    status = Column(String(32), nullable=False, default="pending", index=True)
    # pending | running | completed | failed | cancelled

    # Progress (0.0 â€“ 1.0)
    progress = Column(Float, nullable=False, default=0.0)
    progress_message = Column(String(512), nullable=True)

    # Payload â€” JSON-serializable input parameters
    payload = Column(Text().with_variant(LONGTEXT, "mysql"), nullable=True)  # JSON string

    # Result â€” JSON-serializable output (on success)
    result = Column(Text().with_variant(LONGTEXT, "mysql"), nullable=True)  # JSON string

    # Error â€” error message (on failure)
    error = Column(Text().with_variant(LONGTEXT, "mysql"), nullable=True)

    # Retry tracking
    retries = Column(Integer, nullable=False, default=0)
    max_retries = Column(Integer, nullable=False, default=3)

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Worker heartbeat — updated periodically while a job is running.
    # Used by the stale-job watchdog to detect crashed workers.
    last_heartbeat_at = Column(DateTime, nullable=True)

    # Idempotency key — prevents duplicate job submission.
    # Composed from tenant + operation + target (e.g. "org_5:ocr_document:doc_42").
    # If a job with the same key is already pending/running/completed, the
    # existing job is returned instead of creating a duplicate.
    idempotency_key = Column(String(255), nullable=True, index=True)

    # Internal queue task ID (for linking to TaskQueue)
    queue_task_id = Column(String(64), nullable=True, index=True)

    @property
    def duration_seconds(self) -> float | None:
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    def to_dict(self) -> dict:
        import json

        return {
            "id": self.id,
            "organization_id": self.organization_id,
            "user_id": self.user_id,
            "job_type": self.job_type,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "progress": self.progress,
            "progress_message": self.progress_message,
            "payload": json.loads(self.payload) if self.payload else None,
            "result": json.loads(self.result) if self.result else None,
            "error": self.error,
            "retries": self.retries,
            "max_retries": self.max_retries,
            "idempotency_key": self.idempotency_key,
            "queue_task_id": self.queue_task_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "last_heartbeat_at": (
                self.last_heartbeat_at.isoformat() if self.last_heartbeat_at else None
            ),
            "duration_seconds": self.duration_seconds,
        }
