"""SQLAlchemy models for the Hospital Data Validation Engine."""

from __future__ import annotations

import enum
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from shared.database import Base, BigInt


class RuleSeverity(str, enum.Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class RuleStatus(str, enum.Enum):
    ENABLED = "enabled"
    DISABLED = "disabled"


class ValidationStatus(str, enum.Enum):
    PENDING = "pending"
    PASSED = "passed"
    PASSED_WITH_WARNINGS = "passed_with_warnings"
    FAILED = "failed"
    APPROVED = "approved"
    REJECTED = "rejected"


class ValidationSession(Base):
    """A single validation session for an uploaded dataset."""

    __tablename__ = "validation_sessions"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    dataset_name = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=True)
    row_count = Column(Integer, nullable=True)
    column_count = Column(Integer, nullable=True)
    status = Column(String(50), default=ValidationStatus.PENDING.value)
    overall_score = Column(Float, nullable=True)
    completeness_score = Column(Float, nullable=True)
    accuracy_score = Column(Float, nullable=True)
    consistency_score = Column(Float, nullable=True)
    validity_score = Column(Float, nullable=True)
    uniqueness_score = Column(Float, nullable=True)
    integrity_score = Column(Float, nullable=True)
    total_errors = Column(Integer, default=0)
    total_warnings = Column(Integer, default=0)
    total_findings = Column(Integer, default=0)
    validation_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    validated_at = Column(DateTime, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    approved_by = Column(String(255), nullable=True)
    approval_comments = Column(Text, nullable=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)

    findings = relationship("ValidationFinding", back_populates="session", cascade="all, delete-orphan")
    approvals = relationship("ValidationApproval", back_populates="session", cascade="all, delete-orphan")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "dataset_name": self.dataset_name,
            "file_path": self.file_path,
            "row_count": self.row_count,
            "column_count": self.column_count,
            "status": self.status,
            "overall_score": self.overall_score,
            "completeness_score": self.completeness_score,
            "accuracy_score": self.accuracy_score,
            "consistency_score": self.consistency_score,
            "validity_score": self.validity_score,
            "uniqueness_score": self.uniqueness_score,
            "integrity_score": self.integrity_score,
            "total_errors": self.total_errors,
            "total_warnings": self.total_warnings,
            "total_findings": self.total_findings,
            "validation_summary": self.validation_summary,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "validated_at": self.validated_at.isoformat() if self.validated_at else None,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "approved_by": self.approved_by,
            "approval_comments": self.approval_comments,
            "organization_id": self.organization_id,
        }


class ValidationFinding(Base):
    """A single finding from a validation check."""

    __tablename__ = "validation_findings"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    session_id = Column(BigInt, ForeignKey("validation_sessions.id"), nullable=False)
    rule_name = Column(String(255), nullable=False)
    rule_category = Column(String(100), nullable=False)
    severity = Column(String(20), nullable=False)
    column_name = Column(String(255), nullable=True)
    affected_rows = Column(Integer, default=0)
    affected_row_indices = Column(Text, nullable=True)
    message = Column(Text, nullable=False)
    suggested_fix = Column(Text, nullable=True)
    business_impact = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    session = relationship("ValidationSession", back_populates="findings")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "rule_name": self.rule_name,
            "rule_category": self.rule_category,
            "severity": self.severity,
            "column_name": self.column_name,
            "affected_rows": self.affected_rows,
            "affected_row_indices": self.affected_row_indices,
            "message": self.message,
            "suggested_fix": self.suggested_fix,
            "business_impact": self.business_impact,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ValidationRule(Base):
    """A configurable validation rule."""

    __tablename__ = "validation_rules"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True)
    category = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    severity = Column(String(20), default=RuleSeverity.ERROR.value)
    status = Column(String(20), default=RuleStatus.ENABLED.value)
    rule_config = Column(Text, nullable=True)
    hospital_id = Column(String(255), nullable=True)
    department = Column(String(255), nullable=True)
    dataset_pattern = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "severity": self.severity,
            "status": self.status,
            "rule_config": self.rule_config,
            "hospital_id": self.hospital_id,
            "department": self.department,
            "dataset_pattern": self.dataset_pattern,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ValidationApproval(Base):
    """An approval or rejection decision for a validation session."""

    __tablename__ = "validation_approvals"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    session_id = Column(BigInt, ForeignKey("validation_sessions.id"), nullable=False)
    approver = Column(String(255), nullable=False)
    role = Column(String(100), nullable=True)
    decision = Column(String(20), nullable=False)
    comments = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    session = relationship("ValidationSession", back_populates="approvals")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "approver": self.approver,
            "role": self.role,
            "decision": self.decision,
            "comments": self.comments,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ValidationAuditEntry(Base):
    """Audit log entry for validation events."""

    __tablename__ = "validation_audit_log"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    session_id = Column(BigInt, nullable=True)
    event_type = Column(String(100), nullable=False)
    user = Column(String(255), nullable=True)
    organization = Column(String(255), nullable=True)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "event_type": self.event_type,
            "user": self.user,
            "organization": self.organization,
            "details": self.details,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
