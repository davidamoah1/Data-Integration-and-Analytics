"""ORM model for durable dataset workflow state.

`DatasetWorkflowOrchestrator` (services/dataset_workflow.py) keeps live
workflow state in an in-process dict for fast synchronous execution and easy
unit testing. That in-memory state is lost on process restart and is never
visible to any process other than the one that ran the workflow.

`DatasetWorkflowRun` persists a snapshot of that state (stage results,
current stage, completion flags) after every stage transition, via a
progress callback registered in `services/dataset_workflow_routes.py`. It is
intentionally a plain key/value snapshot rather than a foreign-keyed,
normalized schema — the workflow orchestrator's stage results are the
source of truth and this table exists purely so that status/result reads
survive a restart or land on a different worker process.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, Column, DateTime, String

from shared.database import Base, BigInt


class DatasetWorkflowRun(Base):
    """Durable snapshot of a DatasetWorkflowOrchestrator run."""

    __tablename__ = "dataset_workflow_runs"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    workflow_id = Column(String(64), unique=True, nullable=False, index=True)
    dataset_name = Column(String(255), nullable=False)
    created_by = Column(BigInt, nullable=True, index=True)
    organization_id = Column(BigInt, nullable=True, index=True)
    current_stage = Column(String(64), nullable=False)
    # Mirrors WorkflowState.to_dict()["stages"] — keyed by stage value, each
    # entry has status/started_at/completed_at/duration_seconds/result/error.
    stages = Column(JSON, nullable=False, default=dict)
    is_complete = Column(Boolean, nullable=False, default=False)
    has_errors = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def to_state_dict(self) -> dict:
        """Return a dict shaped like `WorkflowState.to_dict()`."""
        return {
            "workflow_id": self.workflow_id,
            "dataset_name": self.dataset_name,
            "created_by": self.created_by,
            "organization_id": self.organization_id,
            "current_stage": self.current_stage,
            "stages": self.stages or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "is_complete": bool(self.is_complete),
            "has_errors": bool(self.has_errors),
        }
