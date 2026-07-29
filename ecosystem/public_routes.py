"""Public API routes for external developers.

These endpoints are accessible via API key authentication (X-API-Key header)
and provide programmatic access to platform features.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile
from sqlalchemy import select, update
from sqlalchemy.orm import Session as DbSession

from ecosystem.models import APIKey, APIKeyService, APIUsageLog
from shared.database import get_db
from shared.response import success_response

public_router = APIRouter(prefix="/public", tags=["Public API"])


# ─── API Key Authentication ────────────────────────────────


def _get_api_key_from_request(request: Request) -> str | None:
    """Extract API key from X-API-Key header or Authorization: Bearer."""
    key = request.headers.get("X-API-Key")
    if key:
        return key
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer dfk_"):
        return auth[7:]
    return None


def _log_usage(
    db: DbSession,
    api_key_id: int | None,
    org_id: int | None,
    request: Request,
    status_code: int,
    response_time_ms: int,
    error: str | None = None,
):
    """Log API usage."""
    log = APIUsageLog(
        api_key_id=api_key_id,
        organization_id=org_id,
        endpoint=str(request.url.path),
        method=request.method,
        status_code=status_code,
        response_time_ms=response_time_ms,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        error_message=error,
    )
    db.add(log)
    db.execute(
        update(APIKey)
        .where(APIKey.id == api_key_id)
        .values(last_used_at=datetime.now(timezone.utc))
    )
    db.commit()


async def verify_api_key(request: Request, db: DbSession = Depends(get_db)) -> dict:
    """Verify API key and return key info."""
    import time as _time
    start = _time.time()

    raw_key = _get_api_key_from_request(request)
    if not raw_key:
        _log_usage(db, None, None, request, 401, 0, "Missing API key")
        raise HTTPException(status_code=401, detail="API key required. Provide via X-API-Key header.")

    key_hash = APIKeyService.hash_key(raw_key)
    api_key = db.execute(
        select(APIKey).where(APIKey.key_hash == key_hash, APIKey.is_active == True)  # noqa: E712
    ).scalar_one_or_none()

    if not api_key:
        _log_usage(db, None, None, request, 401, 0, "Invalid API key")
        raise HTTPException(status_code=401, detail="Invalid or revoked API key")

    if api_key.expires_at and api_key.expires_at < datetime.now(timezone.utc):
        _log_usage(db, api_key.id, api_key.organization_id, request, 401, 0, "Expired API key")
        raise HTTPException(status_code=401, detail="API key has expired")

    # Store on request state for logging after response
    request.state.api_key_id = api_key.id
    request.state.org_id = api_key.organization_id
    request.state.scopes = api_key.scopes or []

    return {
        "api_key_id": api_key.id,
        "organization_id": api_key.organization_id,
        "scopes": api_key.scopes or [],
        "rate_limit_per_hour": api_key.rate_limit_per_hour,
    }


def require_scope(scope: str):
    """Dependency that checks if the API key has the required scope."""
    async def scope_checker(api_key_info: dict = Depends(verify_api_key)) -> dict:
        if scope not in api_key_info["scopes"]:
            raise HTTPException(status_code=403, detail=f"API key lacks required scope: {scope}")
        return api_key_info
    return scope_checker


# ─── Dataset APIs ──────────────────────────────────────────


@public_router.post("/datasets/upload")
async def public_upload_dataset(
    file: UploadFile = File(...),
    api_key_info: dict = Depends(require_scope("datasets")),
    db: DbSession = Depends(get_db),
):
    """Upload a dataset via API."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    # Delegate to existing ETL upload
    from services.etl_service import ETLService
    etl = ETLService(db)
    result = etl.upload_file(file.file, file.filename, organization_id=api_key_info["organization_id"])
    return success_response(result, "Dataset uploaded")


@public_router.get("/datasets")
async def public_list_datasets(
    api_key_info: dict = Depends(require_scope("datasets")),
    db: DbSession = Depends(get_db),
):
    """List datasets for the organization."""
    from etl.models import DatasetMeta
    datasets = db.execute(
        select(DatasetMeta)
        .where(DatasetMeta.organization_id == api_key_info["organization_id"])
        .order_by(DatasetMeta.created_at.desc())
    ).scalars().all()
    return success_response([
        {"id": d.id, "name": d.table_name, "rows": d.row_count, "created_at": str(d.created_at) if d.created_at else None}
        for d in datasets
    ])


# ─── Analytics APIs ────────────────────────────────────────


@public_router.get("/analytics/dashboards")
async def public_list_dashboards(
    api_key_info: dict = Depends(require_scope("analytics")),
    db: DbSession = Depends(get_db),
):
    """List dashboards for the organization."""
    from analytics.models import Dashboard
    dashboards = db.execute(
        select(Dashboard)
        .where(Dashboard.organization_id == api_key_info["organization_id"])
        .order_by(Dashboard.updated_at.desc())
    ).scalars().all()
    return success_response([
        {"id": d.id, "name": d.name, "description": d.description, "theme": d.theme}
        for d in dashboards
    ])


@public_router.get("/analytics/kpis")
async def public_list_kpis(
    api_key_info: dict = Depends(require_scope("analytics")),
    db: DbSession = Depends(get_db),
):
    """List KPIs for the organization."""
    from analytics.models import KPI
    kpis = db.execute(
        select(KPI)
        .where(KPI.organization_id == api_key_info["organization_id"])
        .order_by(KPI.created_at.desc())
    ).scalars().all()
    return success_response([
        {"id": k.id, "name": k.name, "category": k.category, "target_value": k.target_value, "unit": k.unit}
        for k in kpis
    ])


# ─── AI APIs ───────────────────────────────────────────────


@public_router.post("/ai/ask")
async def public_ai_ask(
    body: dict,
    api_key_info: dict = Depends(require_scope("ai")),
    db: DbSession = Depends(get_db),
):
    """Ask the AI Copilot a question."""
    question = body.get("question", "")
    if not question:
        raise HTTPException(status_code=400, detail="question is required")
    from ai.services import AICopilotService
    service = AICopilotService(db)
    result = service.ask(question, user_id=api_key_info["api_key_id"], organization_id=api_key_info["organization_id"])
    return success_response(result)


# ─── Workflow APIs ─────────────────────────────────────────


@public_router.get("/workflows")
async def public_list_workflows(
    api_key_info: dict = Depends(require_scope("workflows")),
    db: DbSession = Depends(get_db),
):
    """List workflows for the organization."""
    from workflows.models import Workflow
    workflows = db.execute(
        select(Workflow)
        .where(Workflow.organization_id == api_key_info["organization_id"])
        .order_by(Workflow.created_at.desc())
    ).scalars().all()
    return success_response([
        {"id": w.id, "name": w.name, "status": w.status, "created_at": str(w.created_at) if w.created_at else None}
        for w in workflows
    ])


# ─── Reports APIs ──────────────────────────────────────────


@public_router.get("/reports")
async def public_list_reports(
    api_key_info: dict = Depends(require_scope("analytics")),
    db: DbSession = Depends(get_db),
):
    """List AI-generated reports."""
    from ai.models import AIReportGeneration
    reports = db.execute(
        select(AIReportGeneration)
        .where(AIReportGeneration.user_id == api_key_info["api_key_id"])
        .order_by(AIReportGeneration.created_at.desc())
        .limit(50)
    ).scalars().all()
    return success_response([
        {"id": r.id, "title": r.title, "report_type": r.report_type, "summary": r.summary, "created_at": str(r.created_at) if r.created_at else None}
        for r in reports
    ])
