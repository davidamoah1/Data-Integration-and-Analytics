"""FastAPI routes for the Public API Platform — API keys, usage, and developer access."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import func as sa_func, select, update
from sqlalchemy.orm import Session as DbSession

from ecosystem.models import APIKey, APIKeyService, APIUsageLog
from shared.database import get_db
from shared.dependencies import get_current_user
from shared.response import success_response
from shared.tenant import get_current_organization_id

router = APIRouter(prefix="/platform", tags=["Platform / API Keys"])


# ─── Schemas ───────────────────────────────────────────────


class APIKeyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    scopes: list[str] | None = None
    rate_limit_per_hour: int = 1000
    expires_in_days: int | None = None


class APIKeyResponse(BaseModel):
    id: int
    name: str
    key_prefix: str
    scopes: list[str] | None = None
    rate_limit_per_hour: int
    is_active: bool
    expires_at: str | None = None
    last_used_at: str | None = None
    created_at: str | None = None


# ─── API Key CRUD ──────────────────────────────────────────


@router.post("/api-keys")
async def create_api_key(
    body: APIKeyCreate,
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Generate a new API key. The raw key is only shown once."""
    org_id = get_current_organization_id(current_user, db)
    raw_key, key_prefix, key_hash = APIKeyService.generate_key()
    expires_at = None
    if body.expires_in_days:
        expires_at = datetime.now(timezone.utc) + timedelta(days=body.expires_in_days)

    api_key = APIKey(
        organization_id=org_id,
        user_id=current_user["id"],
        name=body.name,
        key_prefix=key_prefix,
        key_hash=key_hash,
        scopes=body.scopes or ["datasets", "analytics", "ai", "workflows"],
        rate_limit_per_hour=body.rate_limit_per_hour,
        expires_at=expires_at,
    )
    db.add(api_key)
    db.flush()
    db.commit()
    return success_response(
        {
            "id": api_key.id,
            "name": api_key.name,
            "api_key": raw_key,  # only shown once
            "key_prefix": key_prefix,
            "scopes": api_key.scopes,
            "expires_at": str(expires_at) if expires_at else None,
        },
        "API key created — save it now, it won't be shown again",
    )


@router.get("/api-keys")
async def list_api_keys(
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """List all API keys for the current organization."""
    org_id = get_current_organization_id(current_user, db)
    keys = (
        db.execute(
            select(APIKey)
            .where(APIKey.organization_id == org_id, APIKey.is_active == True)  # noqa: E712
            .order_by(APIKey.created_at.desc())
        )
        .scalars()
        .all()
    )
    return success_response([
        {
            "id": k.id,
            "name": k.name,
            "key_prefix": k.key_prefix,
            "scopes": k.scopes,
            "rate_limit_per_hour": k.rate_limit_per_hour,
            "is_active": k.is_active,
            "expires_at": str(k.expires_at) if k.expires_at else None,
            "last_used_at": str(k.last_used_at) if k.last_used_at else None,
            "created_at": str(k.created_at) if k.created_at else None,
        }
        for k in keys
    ])


@router.delete("/api-keys/{key_id}")
async def revoke_api_key(
    key_id: int,
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Revoke an API key."""
    org_id = get_current_organization_id(current_user, db)
    key = db.execute(
        select(APIKey).where(APIKey.id == key_id, APIKey.organization_id == org_id)
    ).scalar_one_or_none()
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    db.execute(
        update(APIKey)
        .where(APIKey.id == key_id)
        .values(is_active=False, revoked_at=datetime.now(timezone.utc))
    )
    db.commit()
    return success_response(None, "API key revoked")


@router.post("/api-keys/{key_id}/rotate")
async def rotate_api_key(
    key_id: int,
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Rotate an API key — generates a new key and revokes the old one."""
    org_id = get_current_organization_id(current_user, db)
    key = db.execute(
        select(APIKey).where(APIKey.id == key_id, APIKey.organization_id == org_id)
    ).scalar_one_or_none()
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")

    raw_key, key_prefix, key_hash = APIKeyService.generate_key()
    db.execute(
        update(APIKey)
        .where(APIKey.id == key_id)
        .values(key_prefix=key_prefix, key_hash=key_hash)
    )
    db.commit()
    return success_response(
        {"id": key_id, "api_key": raw_key, "key_prefix": key_prefix},
        "API key rotated — save the new key, it won't be shown again",
    )


# ─── Usage Analytics ───────────────────────────────────────


@router.get("/usage")
async def get_usage_stats(
    days: int = Query(7, ge=1, le=90),
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Get API usage statistics for the current organization."""
    org_id = get_current_organization_id(current_user, db)
    since = datetime.now(timezone.utc) - timedelta(days=days)

    total = db.execute(
        select(sa_func.count(APIUsageLog.id)).where(
            APIUsageLog.organization_id == org_id,
            APIUsageLog.created_at >= since,
        )
    ).scalar() or 0

    by_endpoint = (
        db.execute(
            select(
                APIUsageLog.endpoint,
                sa_func.count(APIUsageLog.id).label("calls"),
                sa_func.avg(APIUsageLog.response_time_ms).label("avg_ms"),
            )
            .where(APIUsageLog.organization_id == org_id, APIUsageLog.created_at >= since)
            .group_by(APIUsageLog.endpoint)
            .order_by(sa_func.count(APIUsageLog.id).desc())
            .limit(20)
        )
        .all()
    )

    errors = db.execute(
        select(sa_func.count(APIUsageLog.id)).where(
            APIUsageLog.organization_id == org_id,
            APIUsageLog.created_at >= since,
            APIUsageLog.status_code >= 400,
        )
    ).scalar() or 0

    return success_response({
        "total_calls": total,
        "error_count": errors,
        "error_rate": round(errors / total * 100, 2) if total else 0,
        "top_endpoints": [
            {"endpoint": r.endpoint, "calls": r.calls, "avg_response_ms": int(r.avg_ms) if r.avg_ms else 0}
            for r in by_endpoint
        ],
    })


@router.get("/usage/by-key")
async def get_usage_by_key(
    days: int = Query(7, ge=1, le=90),
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Get API usage broken down by API key."""
    org_id = get_current_organization_id(current_user, db)
    since = datetime.now(timezone.utc) - timedelta(days=days)

    results = (
        db.execute(
            select(
                APIUsageLog.api_key_id,
                APIKey.name.label("key_name"),
                sa_func.count(APIUsageLog.id).label("calls"),
                sa_func.avg(APIUsageLog.response_time_ms).label("avg_ms"),
            )
            .outerjoin(APIKey, APIKey.id == APIUsageLog.api_key_id)
            .where(APIUsageLog.organization_id == org_id, APIUsageLog.created_at >= since)
            .group_by(APIUsageLog.api_key_id, APIKey.name)
            .order_by(sa_func.count(APIUsageLog.id).desc())
        )
        .all()
    )
    return success_response([
        {
            "api_key_id": r.api_key_id,
            "key_name": r.key_name or "Internal",
            "calls": r.calls,
            "avg_response_ms": int(r.avg_ms) if r.avg_ms else 0,
        }
        for r in results
    ])
