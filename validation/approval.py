"""Approval Workflow — manages validation approval/rejection decisions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

from validation.engine import ValidationResult, ValidationStatus


class ApprovalDecisionType(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass
class ApprovalDecision:
    approver: str
    role: str
    decision: ApprovalDecisionType
    comments: str
    timestamp: str

    def to_dict(self) -> dict:
        return {
            "approver": self.approver,
            "role": self.role,
            "decision": self.decision.value,
            "comments": self.comments,
            "timestamp": self.timestamp,
        }


VALID_ROLES = [
    "reviewer",
    "supervisor",
    "data_manager",
    "statistician",
    "administrator",
]


class ApprovalWorkflow:
    """Manages approval workflow for validation sessions."""

    @staticmethod
    def approve(
        result: ValidationResult,
        approver: str,
        role: str = "administrator",
        comments: str = "",
    ) -> tuple[ValidationResult, ApprovalDecision]:
        """Approve a validation result, allowing ETL to proceed despite failures."""
        if role not in VALID_ROLES:
            raise ValueError(f"Invalid role '{role}'. Must be one of: {VALID_ROLES}")

        result.status = ValidationStatus.APPROVED
        decision = ApprovalDecision(
            approver=approver,
            role=role,
            decision=ApprovalDecisionType.APPROVED,
            comments=comments,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        return result, decision

    @staticmethod
    def reject(
        result: ValidationResult,
        approver: str,
        role: str = "reviewer",
        comments: str = "",
    ) -> tuple[ValidationResult, ApprovalDecision]:
        """Reject a validation result, blocking ETL."""
        if role not in VALID_ROLES:
            raise ValueError(f"Invalid role '{role}'. Must be one of: {VALID_ROLES}")

        result.status = ValidationStatus.REJECTED
        decision = ApprovalDecision(
            approver=approver,
            role=role,
            decision=ApprovalDecisionType.REJECTED,
            comments=comments,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        return result, decision

    @staticmethod
    def can_approve(result: ValidationResult) -> bool:
        """Check if a result can be approved (must have been validated)."""
        return result.status in (
            ValidationStatus.FAILED,
            ValidationStatus.PASSED_WITH_WARNINGS,
            ValidationStatus.PENDING,
        )

    @staticmethod
    def is_etl_blocked(result: ValidationResult) -> bool:
        """Check if ETL is blocked by validation."""
        return not result.can_proceed_to_etl
