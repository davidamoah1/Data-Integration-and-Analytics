"""Centralized audit logging service.

This module provides a single helper to record security-relevant events across
the platform. It writes to the existing `AuditLog` and `SecurityLog` models so
that all actions are captured consistently and can be queried for compliance.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import Request
from sqlalchemy.orm import Session as DbSession

from audit.models import AuditLog, SecurityLog
from shared.context import correlation_id, request_id


def _get_client_ip(request: Request | None) -> str | None:
    """Extract the client IP from a FastAPI request."""
    if request is None:
        return None
    if request.client:
        return request.client.host
    return None


def _get_user_agent(request: Request | None) -> str | None:
    """Extract the user-agent from a FastAPI request."""
    if request is None:
        return None
    return request.headers.get("user-agent")


def log_audit_event(
    db: DbSession,
    action: str,
    user_id: int | None,
    organization_id: int | None,
    resource_type: str | None = None,
    resource_id: int | str | None = None,
    old_values: dict[str, Any] | None = None,
    new_values: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
    request: Request | None = None,
) -> AuditLog:
    """Create a single audit-log entry.

    Args:
        db: Active SQLAlchemy session.
        action: Short action identifier, e.g. "dataset.upload".
        user_id: Primary key of the acting user, or None for anonymous actions.
        organization_id: Organization scope, or None if not applicable.
        resource_type: Type of resource being acted on, e.g. "dataset".
        resource_id: Identifier of the resource.
        old_values: Previous state for update/delete events.
        new_values: New state for create/update events.
        metadata: Extra context (e.g., file size, export format, role names).
        request: Optional FastAPI request for IP / user-agent capture.

    Returns:
        The created AuditLog instance (not yet committed).
    """
    entry = AuditLog(
        user_id=user_id,
        organization_id=organization_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id if isinstance(resource_id, int) else None,
        old_values=old_values,
        new_values=new_values,
        audit_metadata=metadata,
        ip_address=_get_client_ip(request),
        user_agent=_get_user_agent(request),
        request_id=request_id.get() or None,
        created_at=datetime.now(timezone.utc),
    )
    db.add(entry)
    return entry


def log_security_event(
    db: DbSession,
    event_type: str,
    severity: str,
    user_id: int | None = None,
    organization_id: int | None = None,
    resource: str | None = None,
    details: dict[str, Any] | None = None,
    request: Request | None = None,
) -> SecurityLog:
    """Create a single security-log entry.

    Use this for authentication failures, authorization failures, suspicious
    activity, and any event that may need security operations review.
    """
    entry = SecurityLog(
        user_id=user_id,
        organization_id=organization_id,
        event_type=event_type,
        severity=severity,
        resource=resource,
        details={
            **(details or {}),
            "correlation_id": correlation_id.get() or None,
            "request_id": request_id.get() or None,
        },
        ip_address=_get_client_ip(request),
        user_agent=_get_user_agent(request),
        created_at=datetime.now(timezone.utc),
    )
    db.add(entry)
    return entry


def log_data_governance_event(
    db: DbSession,
    action: str,
    user_id: int | None,
    organization_id: int | None,
    resource_type: str,
    resource_id: int | str | None,
    classification: str | None = None,
    request: Request | None = None,
) -> AuditLog:
    """Convenience wrapper for data-governance actions (lifecycle, classification)."""
    return log_audit_event(
        db=db,
        action=action,
        user_id=user_id,
        organization_id=organization_id,
        resource_type=resource_type,
        resource_id=resource_id,
        new_values={"classification": classification} if classification else None,
        request=request,
    )
