"""SQLAlchemy models for the enterprise workflow engine.

A workflow is a versioned DAG of nodes. Executions are stored with full
context, metrics, errors, and lineage links.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from shared.database import Base, BigInt


class WorkflowDefinition(Base):
    """Top-level workflow container."""

    __tablename__ = "workflow_definitions"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    organization_id = Column(BigInt, ForeignKey("organizations.id"), nullable=True, index=True)
    created_by = Column(BigInt, ForeignKey("users.id"), nullable=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)
    is_active = Column(Integer, default=1, nullable=False)
    is_deleted = Column(Integer, default=0, nullable=False)
    published_version_id = Column(BigInt, nullable=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    versions = relationship(
        "WorkflowVersion",
        back_populates="workflow",
        order_by="WorkflowVersion.version_number.desc()",
    )
    executions = relationship("WorkflowExecution", back_populates="workflow")


class WorkflowVersion(Base):
    """Immutable snapshot of a workflow DAG."""

    __tablename__ = "workflow_versions"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    workflow_id = Column(
        BigInt,
        ForeignKey("workflow_definitions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version_number = Column(Integer, nullable=False)
    status = Column(String(20), default="draft", nullable=False)  # draft, published, archived
    nodes = Column(JSON, nullable=False, default=list)
    edges = Column(JSON, nullable=False, default=list)
    config = Column(JSON, nullable=False, default=dict)
    created_by = Column(BigInt, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    workflow = relationship("WorkflowDefinition", back_populates="versions")
    executions = relationship("WorkflowExecution", back_populates="version")

    __table_args__ = (UniqueConstraint("workflow_id", "version_number"),)


class WorkflowExecution(Base):
    """Record of a single workflow run."""

    __tablename__ = "workflow_executions"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    execution_id = Column(String(64), unique=True, nullable=False, index=True)
    workflow_id = Column(
        BigInt,
        ForeignKey("workflow_definitions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    version_id = Column(
        BigInt, ForeignKey("workflow_versions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    organization_id = Column(BigInt, ForeignKey("organizations.id"), nullable=True, index=True)
    triggered_by = Column(BigInt, ForeignKey("users.id"), nullable=True)
    trigger_type = Column(
        String(50), default="manual", nullable=False
    )  # manual, scheduled, webhook, api
    status = Column(
        String(30), default="pending", nullable=False
    )  # pending, running, completed, failed, retrying, cancelled, paused
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    node_results = Column(JSON, nullable=False, default=dict)
    context = Column(JSON, nullable=False, default=dict)
    metrics = Column(JSON, nullable=False, default=dict)
    errors = Column(JSON, nullable=False, default=list)
    warnings = Column(JSON, nullable=False, default=list)
    ai_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    workflow = relationship("WorkflowDefinition", back_populates="executions")
    version = relationship("WorkflowVersion", back_populates="executions")


class WorkflowJob(Base):
    """Job queue entry for asynchronous workflow execution."""

    __tablename__ = "workflow_jobs"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    execution_id = Column(
        String(64),
        ForeignKey("workflow_executions.execution_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status = Column(String(30), default="pending", nullable=False)
    priority = Column(Integer, default=0, nullable=False)
    retry_count = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)
    scheduled_at = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    worker_id = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class WorkflowLineage(Base):
    """Lineage edge between workflow entities."""

    __tablename__ = "workflow_lineage"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    execution_id = Column(
        String(64),
        ForeignKey("workflow_executions.execution_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    organization_id = Column(BigInt, ForeignKey("organizations.id"), nullable=True, index=True)
    source_type = Column(
        String(50), nullable=False
    )  # dataset, transformation, validation, ai, dashboard, report, export
    source_id = Column(String(255), nullable=True)
    target_type = Column(String(50), nullable=False)
    target_id = Column(String(255), nullable=True)
    transformation = Column(String(255), nullable=True)
    meta = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        UniqueConstraint("execution_id", "source_type", "source_id", "target_type", "target_id"),
    )


class WorkflowTemplate(Base):
    """Reusable workflow templates shared across organizations."""

    __tablename__ = "workflow_templates"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    created_by = Column(BigInt, ForeignKey("users.id"), nullable=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)
    nodes = Column(JSON, nullable=False, default=list)
    edges = Column(JSON, nullable=False, default=list)
    config = Column(JSON, nullable=False, default=dict)
    is_public = Column(Integer, default=0, nullable=False)
    is_active = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
