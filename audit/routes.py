"""Enhanced API routes for enterprise audit trails.

Endpoints:
  - GET  /api/audit/logs          — List audit logs with rich filtering
  - GET  /api/audit/logs/{id}     — Get single audit log entry
  - GET  /api/audit/logs/export   — Export audit logs (CSV/JSON)
  - GET  /api/audit/stats         — Audit statistics (action counts, daily counts, top users)
  - GET  /api/audit/filters       — Available filter values (actions, resource types)
  - GET  /api/audit/security      — List security logs
  - GET  /api/audit/activity/{user_id} — User activity history
"""

from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session as DbSession

from audit.repositories import AuditRepository
from shared.database import get_db
from shared.dependencies import get_current_user
from shared.tenant import get_current_organization_id, is_super_admin

router = APIRouter(prefix="/api/audit", tags=["audit"])


def _log_to_dict(log) -> dict[str, Any]:
    return {
        "id": log.id,
        "user_id": log.user_id,
        "organization_id": log.organization_id,
        "action": log.action,
        "resource_type": log.resource_type,
        "resource_id": log.resource_id,
        "old_values": log.old_values,
        "new_values": log.new_values,
        "metadata": log.audit_metadata,
        "ip_address": log.ip_address,
        "user_agent": log.user_agent,
        "request_id": log.request_id,
        "created_at": log.created_at.isoformat() if log.created_at else None,
    }


def _security_to_dict(log) -> dict[str, Any]:
    return {
        "id": log.id,
        "user_id": log.user_id,
        "organization_id": log.organization_id,
        "event_type": log.event_type,
        "ip_address": log.ip_address,
        "user_agent": log.user_agent,
        "resource": log.resource,
        "severity": log.severity,
        "details": log.details,
        "created_at": log.created_at.isoformat() if log.created_at else None,
    }


# ── Audit Logs ────────────────────────────────────────────────────────────


@router.get("/logs")
async def list_audit_logs(
    user_id: int | None = Query(None),
    action: str | None = Query(None),
    resource_type: str | None = Query(None),
    resource_id: int | None = Query(None),
    ip_address: str | None = Query(None),
    start_date: str | None = Query(None, description="ISO 8601 datetime"),
    end_date: str | None = Query(None, description="ISO 8601 datetime"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List audit logs with rich filtering. Organization-scoped for non-super-admins."""
    repo = AuditRepository(db)

    # Determine org scope
    org_id: int | None = None
    if not is_super_admin(current_user):
        org_id = get_current_organization_id(current_user, db)

    # Parse dates
    sd = datetime.fromisoformat(start_date) if start_date else None
    ed = datetime.fromisoformat(end_date) if end_date else None

    logs = repo.list_logs(
        organization_id=org_id,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=ip_address,
        start_date=sd,
        end_date=ed,
        limit=limit,
        offset=offset,
    )
    total = repo.count_logs(
        organization_id=org_id,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=ip_address,
        start_date=sd,
        end_date=ed,
    )

    return {
        "logs": [_log_to_dict(l) for l in logs],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/logs/{log_id}")
async def get_audit_log(
    log_id: int,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get a single audit log entry by ID."""
    repo = AuditRepository(db)
    log = repo.get_log(log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Audit log not found")

    # Org scoping
    if not is_super_admin(current_user):
        org_id = get_current_organization_id(current_user, db)
        if log.organization_id is not None and log.organization_id != org_id:
            raise HTTPException(status_code=404, detail="Audit log not found")

    return _log_to_dict(log)


@router.get("/logs/export")
async def export_audit_logs(
    format: str = Query("csv", regex="^(csv|json)$"),
    user_id: int | None = Query(None),
    action: str | None = Query(None),
    resource_type: str | None = Query(None),
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Export audit logs as CSV or JSON."""
    repo = AuditRepository(db)
    org_id: int | None = None
    if not is_super_admin(current_user):
        org_id = get_current_organization_id(current_user, db)

    sd = datetime.fromisoformat(start_date) if start_date else None
    ed = datetime.fromisoformat(end_date) if end_date else None

    logs = repo.list_logs(
        organization_id=org_id,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        start_date=sd,
        end_date=ed,
        limit=10000,
        offset=0,
    )

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    if format == "json":
        content = json.dumps([_log_to_dict(l) for l in logs], indent=2, default=str)
        return StreamingResponse(
            io.BytesIO(content.encode()),
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="audit_logs_{timestamp}.json"'},
        )

    # CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "id",
            "user_id",
            "organization_id",
            "action",
            "resource_type",
            "resource_id",
            "ip_address",
            "user_agent",
            "created_at",
        ]
    )
    for log in logs:
        writer.writerow(
            [
                log.id,
                log.user_id,
                log.organization_id,
                log.action,
                log.resource_type,
                log.resource_id,
                log.ip_address,
                log.user_agent,
                log.created_at.isoformat() if log.created_at else "",
            ]
        )

    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="audit_logs_{timestamp}.csv"'},
    )


# ── Stats ─────────────────────────────────────────────────────────────────


@router.get("/stats")
async def get_audit_stats(
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get audit statistics: action counts, daily counts, top users."""
    repo = AuditRepository(db)
    org_id: int | None = None
    if not is_super_admin(current_user):
        org_id = get_current_organization_id(current_user, db)

    sd = datetime.fromisoformat(start_date) if start_date else None
    ed = datetime.fromisoformat(end_date) if end_date else None

    return {
        "action_counts": repo.action_counts(org_id, start_date=sd, end_date=ed),
        "daily_counts": repo.daily_counts(org_id, start_date=sd, end_date=ed),
        "top_users": repo.top_users(org_id),
        "total": repo.count_logs(organization_id=org_id, start_date=sd, end_date=ed),
    }


# ── Filter Values ─────────────────────────────────────────────────────────


@router.get("/filters")
async def get_filter_values(
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get available filter values (actions, resource types) for the UI."""
    repo = AuditRepository(db)
    org_id: int | None = None
    if not is_super_admin(current_user):
        org_id = get_current_organization_id(current_user, db)

    return {
        "actions": repo.list_actions(org_id),
        "resource_types": repo.list_resource_types(org_id),
    }


# ── Security Logs ─────────────────────────────────────────────────────────


@router.get("/security")
async def list_security_logs(
    severity: str | None = Query(None),
    event_type: str | None = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List security logs with filtering."""
    repo = AuditRepository(db)
    org_id: int | None = None
    if not is_super_admin(current_user):
        org_id = get_current_organization_id(current_user, db)

    logs = repo.list_security_logs(
        organization_id=org_id,
        severity=severity,
        event_type=event_type,
        limit=limit,
        offset=offset,
    )
    total = repo.count_security_logs(
        organization_id=org_id,
        severity=severity,
        event_type=event_type,
    )

    return {
        "logs": [_security_to_dict(l) for l in logs],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


# ── User Activity ─────────────────────────────────────────────────────────


@router.get("/activity/{user_id}")
async def get_user_activity(
    user_id: int,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get activity history for a specific user."""
    repo = AuditRepository(db)
    activities = repo.list_user_activity(user_id, limit=limit, offset=offset)

    return {
        "activities": [
            {
                "id": a.id,
                "user_id": a.user_id,
                "activity_type": a.activity_type,
                "resource_type": a.resource_type,
                "resource_id": a.resource_id,
                "session_id": a.session_id,
                "ip_address": a.ip_address,
                "duration_seconds": a.duration_seconds,
                "extra_data": a.extra_data,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in activities
        ],
        "total": len(activities),
    }
