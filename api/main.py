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

import sys
import os
from datetime import date, datetime
from typing import Optional

from fastapi import FastAPI, Depends, Query, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from api.schemas import (
    KPIResponse,
    SalesListResponse,
    SalesRecordResponse,
    FilterOptionsResponse,
    PipelineRunResponse,
    PipelineTriggerResponse,
    HealthResponse,
)
from api.auth import get_api_key
from database.repositories import SalesRepository, PipelineRunRepository
from services.etl_service import ETLService
from etl.logging_config import logger

# Phase 4 — Enterprise IAM
from authentication.routes import router as auth_router, users_router, roles_router
from organizations.services import org_router, dept_router
from audit.services import audit_router
from shared.database import get_db, get_engine, Base
from authentication.services import seed_default_data
from etl.routes import router as etl_router
from ai.routes import router as ai_router

app = FastAPI(
    title="DataFlow — Enterprise Data Intelligence API",
    description="Enterprise REST API for ETL, analytics, IAM, and pipeline management.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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


@app.on_event("startup")
async def startup_event():
    """Create auth tables and seed default roles/permissions/admin on startup."""
    try:
        engine = get_engine()
        # Import all models so they register with Base.metadata
        import authentication.models  # noqa: F401
        import organizations.models  # noqa: F401
        import audit.models  # noqa: F401
        import etl.models  # noqa: F401
        import ai.models  # noqa: F401
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
        finally:
            db.close()
        logger.info("Auth tables created and default data seeded.")
    except Exception as e:
        logger.error(f"Startup seeding failed: {e}")


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
async def health_check(
    repo: SalesRepository = Depends(get_sales_repo),
    _api_key: str = Depends(get_api_key),
):
    """Check API and database health.

    Returns database connection status and record count.
    """
    try:
        count = repo.get_record_count()
        return HealthResponse(
            database_connected=True,
            record_count=count,
            timestamp=datetime.utcnow(),
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            database_connected=False,
            record_count=0,
            timestamp=datetime.utcnow(),
        )


# ──────────────────────────────────────────────
# Sales Data
# ──────────────────────────────────────────────
@app.get("/api/v1/sales", response_model=SalesListResponse, tags=["Sales"])
async def get_sales(
    region: Optional[str] = Query(None, description="Filter by region"),
    category: Optional[str] = Query(None, description="Filter by category"),
    date_from: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
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
    df = repo.get_sales_filtered(
        region=region, category=category, date_from=date_from, date_to=date_to
    )
    total = len(df)
    start = (page - 1) * page_size
    end = start + page_size
    page_df = df.iloc[start:end]

    records = []
    for _, row in page_df.iterrows():
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
    region: Optional[str] = Query(None, description="Filter by region"),
    category: Optional[str] = Query(None, description="Filter by category"),
    date_from: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    repo: SalesRepository = Depends(get_sales_repo),
    _api_key: str = Depends(get_api_key),
):
    """Get aggregate KPIs with optional filters.

    Returns total sales, profit, order count, average order value, and margin.
    """
    kpis = repo.get_kpis(
        region=region, category=category, date_from=date_from, date_to=date_to
    )
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
        date_range={"min": str(min_date) if min_date else None, "max": str(max_date) if max_date else None},
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
        run_id=f"api_triggered_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
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
        "name": "ETL Data Intelligence API",
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
