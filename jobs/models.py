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

from shared.database import Base, BigInt


class Job(Base):
    """A persistent background job tracked across the platform.

    Lifecycle: pending → running → completed | failed | cancelled

    Job types:
      - etl_run        — ETL pipeline execution
      - ocr_batch      — OCR processing for capture batches
      - report_gen     — AI report generation
      - data_import    — Large dataset imports
      - export         — Data exports
      - custom         — Custom user-defined tasks
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

    # Progress (0.0 – 1.0)
    progress = Column(Float, nullable=False, default=0.0)
    progress_message = Column(String(512), nullable=True)

    # Payload — JSON-serializable input parameters
    payload = Column(Text, nullable=True)  # JSON string

    # Result — JSON-serializable output (on success)
    result = Column(Text, nullable=True)  # JSON string

    # Error — error message (on failure)
    error = Column(Text, nullable=True)

    # Retry tracking
    retries = Column(Integer, nullable=False, default=0)
    max_retries = Column(Integer, nullable=False, default=3)

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

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
            "queue_task_id": self.queue_task_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.duration_seconds,
        }
