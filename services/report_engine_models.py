"""ORM model for durable report composition storage.

Mirrors the pattern used by `dataset_workflow_models.py`: the
`ReportCompositionService` keeps an in-memory store for fast access
during a session, but every mutation is also persisted to the
`report_compositions` table so reports survive a restart.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import JSON, Column, DateTime, String, Text, func

from shared.database import Base, BigInt


class ReportCompositionRecord(Base):
    """Durable snapshot of a ReportComposition."""

    __tablename__ = "report_compositions"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    report_id = Column(String(100), unique=True, nullable=False, index=True)
    organization_id = Column(BigInt, nullable=True, index=True)
    title = Column(String(500), nullable=False)
    subtitle = Column(String(500), nullable=True)
    organization_name = Column(String(255), nullable=True)
    author_name = Column(String(255), nullable=True)
    template = Column(String(50), nullable=False, default="executive")
    industry = Column(String(100), nullable=True)
    dataset_id = Column(BigInt, nullable=True)
    analysis_id = Column(BigInt, nullable=True)
    sections = Column(JSON, nullable=True)
    executive_summary = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)
    status = Column(String(20), nullable=False, default="draft")
    created_by = Column(BigInt, nullable=True)
    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    def to_dict(self) -> dict:
        return {
            "report_id": self.report_id,
            "title": self.title,
            "subtitle": self.subtitle or "",
            "organization_name": self.organization_name or "",
            "author_name": self.author_name or "",
            "template": self.template,
            "industry": self.industry or "",
            "dataset_id": self.dataset_id,
            "analysis_id": self.analysis_id,
            "sections": self.sections or [],
            "executive_summary": self.executive_summary or "",
            "tags": self.tags or [],
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else "",
            "updated_at": self.updated_at.isoformat() if self.updated_at else "",
        }
