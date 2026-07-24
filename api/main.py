"""FastAPI application for the DataFlow Enterprise Data Intelligence Platform.

Provides REST API endpoints for:
  - Authentication & Authorization (JWT-based IAM)
  - User, Role, Permission management
  - Organization & Department management
  - Audit logs & Security events
  - Health checks
  - Sales data queries (with filtering and pagination)
  - KPI aggregation
  - Filter options
  - Pipeline triggering and status
  - Pipeline run history

Run with:
    uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

Authentication:
    Phase 4 endpoints use JWT Bearer tokens (see /auth/login).
    Legacy endpoints support API key via X-API-Key header (backward compatible).
"""

# ruff: noqa: B008  # FastAPI Depends() calls in default arguments are intentional

import os
import sys
import uuid
from contextlib import asynccontextmanager
from datetime import date, datetime, timezone

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from config import validate_config
from shared.context import correlation_id, request_id
from shared.middleware import (
    RateLimitMiddleware,
    RequestLoggingMiddleware,
    SecurityHeadersMiddleware,
)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ai.routes import router as ai_router
from analytics.routes import router as analytics_router
from api.auth import get_api_key
from api.schemas import (
    FilterOptionsResponse,
    HealthResponse,
    KPIResponse,
    PipelineTriggerResponse,
    SalesListResponse,
    SalesRecordResponse,
)
from audit.services import audit_router
from authentication.routes import roles_router, users_router

# Phase 4 — Enterprise IAM
from authentication.routes import router as auth_router
from authentication.services import seed_default_data
from database.repositories import PipelineRunRepository, SalesRepository
from enterprise.routes import router as platform_router
from etl.logging_config import logger
from etl.routes import router as etl_router
from notifications.routes import router as notifications_router
from organizations.services import dept_router, org_router
from scheduler.report_scheduler import ReportScheduler
from scheduler.routes import router as scheduler_router
from semantic.routes import router as semantic_router
from services.etl_service import ETLService
from shared.database import Base, get_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Validate configuration, create tables, and seed data at startup."""
    validate_config()
    engine = get_engine()
    # Import all models so they register with Base.metadata
    import ai.models  # noqa: F401
    import analytics.models  # noqa: F401
    import audit.models  # noqa: F401
    import authentication.models  # noqa: F401
    import database.db_setup  # noqa: F401
    import enterprise.models  # noqa: F401
    import enterprise.subscription  # noqa: F401
    import etl.models  # noqa: F401
    import notifications.models  # noqa: F401
    import organizations.models  # noqa: F401
    import scheduler.models  # noqa: F401

    Base.metadata.create_all(engine)

    # Register system AI plugins
    from sqlalchemy.orm import Session as AIDbSession

    ai_db = AIDbSession(engine)
    try:
        from ai.plugins import register_system_plugins

        register_system_plugins(ai_db)
    except Exception as e:
        logger.error(f"AI plugin registration failed: {e}")
    finally:
        ai_db.close()

    # Seed default data
    from sqlalchemy.orm import Session as DbSession

    db = DbSession(engine)
    try:
        seed_default_data(db)
        # Seed demo data for pilot deployments
        from enterprise.demo_data import is_demo_seeded, seed_demo_data

        if not is_demo_seeded(db):
            seed_demo_data(db)
            logger.info(
                "Pilot demo data seeded (org, users, dashboards, KPIs, pipelines, AI conversations, reports)."
            )
        # Create trial subscriptions for all orgs without one
        from enterprise.subscription import SubscriptionService
        from organizations.models import Organization

        sub_svc = SubscriptionService(db)
        for org in db.query(Organization).filter(Organization.is_active == 1).all():
            if not sub_svc.get_subscription(org.id):
                sub_svc.create_trial(org.id)

        # Start background report scheduler (disabled during tests)
        try:
            report_scheduler = ReportScheduler()
            report_scheduler.start()
            app.state.report_scheduler = report_scheduler

            # Schedule daily database/config backups at 02:00 UTC
            try:
                from apscheduler.triggers.cron import CronTrigger

                from services.backup_service import BackupService

                report_scheduler.scheduler.add_job(
                    BackupService().create_backup,
                    trigger=CronTrigger(hour=2, minute=0),
                    id="daily_backup",
                    replace_existing=True,
                )
                logger.info("Daily backup scheduled for 02:00 UTC")
            except Exception as e:
                logger.error(f"Backup scheduler setup failed: {e}")
        except Exception as e:
            logger.error(f"Report scheduler failed to start: {e}")
    finally:
        db.close()
    logger.info("Auth tables created, default data seeded, subscriptions initialized.")

    yield


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Attach a request ID and optional correlation ID to every incoming request."""

    async def dispatch(self, request: Request, call_next):
        req_token = request_id.set(str(uuid.uuid4()))
        corr_value = request.headers.get("X-Correlation-ID")
        corr_token = correlation_id.set(corr_value or str(uuid.uuid4()))
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id.get()
            if corr_value:
                response.headers["X-Correlation-ID"] = corr_value
            return response
        finally:
            request_id.reset(req_token)
            correlation_id.reset(corr_token)


app = FastAPI(
    title="DataFlow — Enterprise Data Intelligence API",
    description="Enterprise REST API for ETL, analytics, IAM, and pipeline management.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(RequestContextMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware)
_is_test_env = os.getenv("PYTEST_RUNNING", "").lower() in ("1", "true", "yes")
if not _is_test_env:
    app.add_middleware(
        RateLimitMiddleware,
        requests_per_minute=int(os.getenv("RATE_LIMIT_RPM", "120")),
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Return consistent error JSON for HTTPExceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "message": exc.detail, "data": None},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch unhandled exceptions and return a safe response without stack traces."""
    logger.exception("Unhandled exception")
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": "Internal server error", "data": None},
    )


_raw_cors = os.getenv("CORS_ORIGINS", "*")
allow_origins = [origin.strip() for origin in _raw_cors.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "X-API-Key",
        "X-Correlation-ID",
        "X-Request-ID",
    ],
)

# Include Phase 4 routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(roles_router)
app.include_router(org_router)
app.include_router(dept_router)
app.include_router(audit_router)
app.include_router(etl_router)
app.include_router(ai_router)
app.include_router(analytics_router)
app.include_router(platform_router)
app.include_router(notifications_router)
app.include_router(scheduler_router)
app.include_router(semantic_router)


# ──────────────────────────────────────────────
# Dependencies
# ──────────────────────────────────────────────
def get_sales_repo() -> SalesRepository:
    """FastAPI dependency for SalesRepository."""
    return SalesRepository()


def get_run_repo() -> PipelineRunRepository:
    """FastAPI dependency for PipelineRunRepository."""
    return PipelineRunRepository()


# ──────────────────────────────────────────────
# Health
# ──────────────────────────────────────────────
@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check(repo: SalesRepository = Depends(get_sales_repo)):
    """Check API and database health.

    Returns database connection status and record count. This endpoint is
    intentionally public so load balancers and monitoring tools can reach it.
    """
    try:
        count = repo.get_record_count()
        return HealthResponse(
            status="healthy",
            database_connected=True,
            record_count=count,
            timestamp=datetime.now(timezone.utc),
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            database_connected=False,
            record_count=0,
            timestamp=datetime.now(timezone.utc),
        )


@app.get("/ready", tags=["System"])
async def readiness_check():
    """Check readiness of all subsystems (database, ETL, AI).

    Returns 200 if all critical subsystems are operational, 503 otherwise.
    Intentionally public for orchestration probes.
    """
    checks: dict[str, dict] = {}
    overall = True

    try:
        from sqlalchemy import text

        from shared.database import get_engine

        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        checks["database"] = {"status": "ready"}
    except Exception as e:
        checks["database"] = {"status": "not_ready", "error": str(e)}
        overall = False

    try:
        from etl.models import ETLPipeline
        from shared.database import get_session_factory

        factory = get_session_factory()
        db = factory()
        try:
            db.query(ETLPipeline).limit(1).count()
            checks["etl"] = {"status": "ready"}
        finally:
            db.close()
    except Exception as e:
        checks["etl"] = {"status": "not_ready", "error": str(e)}
        overall = False

    try:
        from ai.models import AIProviderConfig
        from shared.database import get_session_factory

        factory = get_session_factory()
        db = factory()
        try:
            db.query(AIProviderConfig).limit(1).count()
            checks["ai"] = {"status": "ready"}
        finally:
            db.close()
    except Exception as e:
        checks["ai"] = {"status": "not_ready", "error": str(e)}
        overall = False

    status_code = 200 if overall else 503
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "ready" if overall else "not_ready",
            "checks": checks,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


@app.get("/health/detailed", tags=["System"])
async def detailed_health_check():
    """Return detailed health status for all subsystems.

    Exposes readiness for database, ETL, AI, scheduler, email, SMS, WhatsApp,
    push notifications, storage, and internal monitoring.
    """
    from monitoring.health_check import run_full_health_check

    return JSONResponse(content=run_full_health_check())


@app.get("/metrics", tags=["System"])
async def metrics():
    """Expose basic platform metrics for monitoring.

    Returns counts for key entities. Intentionally public (no sensitive data).
    """
    from sqlalchemy import text

    from shared.database import get_engine

    metrics_data: dict[str, int] = {}
    engine = get_engine()
    try:
        with engine.connect() as conn:
            for table_name in [
                "etl_pipelines",
                "etl_jobs",
                "ai_conversations",
                "ai_messages",
                "users",
                "audit_logs",
            ]:
                try:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                    metrics_data[table_name] = result.scalar() or 0
                except Exception:
                    metrics_data[table_name] = -1
    except Exception:
        pass

    return JSONResponse(
        content={
            "metrics": metrics_data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )


# ──────────────────────────────────────────────
# Sales Data
# ──────────────────────────────────────────────
@app.get("/api/v1/sales", response_model=SalesListResponse, tags=["Sales"])
async def get_sales(
    region: str | None = Query(None, description="Filter by region"),
    category: str | None = Query(None, description="Filter by category"),
    date_from: date | None = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: date | None = Query(None, description="End date (YYYY-MM-DD)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=500, description="Records per page"),
    repo: SalesRepository = Depends(get_sales_repo),
    _api_key: str = Depends(get_api_key),
):
    """Retrieve sales records with optional filtering and pagination.

    Args:
        region: Filter by region name.
        category: Filter by category name.
        date_from: Filter orders from this date (inclusive).
        date_to: Filter orders up to this date (inclusive).
        page: Page number (1-indexed).
        page_size: Number of records per page (max 500).

    Returns:
        Paginated list of sales records.
    """
    df, total = repo.get_sales_paginated(
        region=region,
        category=category,
        date_from=date_from,
        date_to=date_to,
        page=page,
        page_size=page_size,
    )

    records = []
    for _, row in df.iterrows():
        record = SalesRecordResponse(
            order_id=str(row.get("order_id", "")),
            order_date=row.get("order_date"),
            ship_date=row.get("ship_date"),
            customer_name=row.get("customer_name"),
            segment=row.get("segment"),
            region=row.get("region"),
            category=row.get("category"),
            sub_category=row.get("sub_category"),
            product_name=row.get("product_name"),
            sales=float(row.get("sales", 0)),
            quantity=int(row.get("quantity", 0)),
            discount=float(row.get("discount", 0)),
            profit=float(row.get("profit", 0)),
        )
        records.append(record)

    return SalesListResponse(records=records, total=total, page=page, page_size=page_size)


# ──────────────────────────────────────────────
# KPIs
# ──────────────────────────────────────────────
@app.get("/api/v1/kpis", response_model=KPIResponse, tags=["Analytics"])
async def get_kpis(
    region: str | None = Query(None, description="Filter by region"),
    category: str | None = Query(None, description="Filter by category"),
    date_from: date | None = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: date | None = Query(None, description="End date (YYYY-MM-DD)"),
    repo: SalesRepository = Depends(get_sales_repo),
    _api_key: str = Depends(get_api_key),
):
    """Get aggregate KPIs with optional filters.

    Returns total sales, profit, order count, average order value, and margin.
    """
    kpis = repo.get_kpis(region=region, category=category, date_from=date_from, date_to=date_to)
    return KPIResponse(**kpis)


# ──────────────────────────────────────────────
# Filter Options
# ──────────────────────────────────────────────
@app.get("/api/v1/filters", response_model=FilterOptionsResponse, tags=["Analytics"])
async def get_filter_options(
    repo: SalesRepository = Depends(get_sales_repo),
    _api_key: str = Depends(get_api_key),
):
    """Get available filter values (regions, categories, date range)."""
    opts = repo.get_distinct_values("region")
    cats = repo.get_distinct_values("category")
    min_date, max_date = repo.get_date_range()
    return FilterOptionsResponse(
        regions=opts,
        categories=cats,
        date_range={
            "min": str(min_date) if min_date else None,
            "max": str(max_date) if max_date else None,
        },
    )


# ──────────────────────────────────────────────
# Pipeline
# ──────────────────────────────────────────────
@app.post("/api/v1/pipeline/trigger", response_model=PipelineTriggerResponse, tags=["Pipeline"])
async def trigger_pipeline(
    background_tasks: BackgroundTasks,
    _api_key: str = Depends(get_api_key),
):
    """Trigger an ETL pipeline run asynchronously.

    The pipeline runs in the background. Check status via /api/v1/pipeline/runs.
    """
    service = ETLService()

    def run_in_background():
        try:
            service.run_pipeline()
        except Exception as e:
            logger.error(f"Background pipeline run failed: {e}")

    background_tasks.add_task(run_in_background)

    return PipelineTriggerResponse(
        run_id=f"api_triggered_{datetime.now(timezone.utc).replace(tzinfo=None).strftime('%Y%m%d_%H%M%S')}",
        status="triggered",
        message="Pipeline execution started in background. Check /api/v1/pipeline/runs for status.",
    )


@app.get("/api/v1/pipeline/runs", tags=["Pipeline"])
async def get_pipeline_runs(
    limit: int = Query(10, ge=1, le=100, description="Number of recent runs"),
    repo: PipelineRunRepository = Depends(get_run_repo),
    _api_key: str = Depends(get_api_key),
):
    """Get recent pipeline run history."""
    df = repo.get_recent_runs(limit=limit)
    return df.to_dict(orient="records")


# ──────────────────────────────────────────────
# Root
# ──────────────────────────────────────────────
@app.get("/", tags=["System"])
async def root():
    """API root — basic info."""
    return {
        "name": "AEDIP Enterprise Data Intelligence API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.main:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", "8000")),
        reload=True,
    )
