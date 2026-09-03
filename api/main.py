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

import asyncio
import os
import sys
from contextlib import asynccontextmanager
from datetime import date, datetime, timezone

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, JSONResponse

from audit.middleware import AuditMiddleware
from config import validate_config
from monitoring.middleware import MonitoringMiddleware
from monitoring.otel import init_otel, instrument_fastapi, record_pipeline_run
from monitoring.prometheus import metrics_registry
from monitoring.sentry_integration import capture_exception, init_sentry
from saas.tenant_middleware import TenantIsolationMiddleware
from shared.middleware import (
    RateLimitMiddleware,
    RequestSizeLimitMiddleware,
    SecurityHeadersMiddleware,
)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import etl.package_models  # noqa: F401 — register models with Base.metadata
from admin.routes import router as admin_router
from ai.enterprise_routes import router as ai_enterprise_router
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
from audit.routes import router as audit_enterprise_router
from audit.services import audit_router
from authentication.routes import mfa_router, roles_router, sso_router, users_router

# Phase 4 — Enterprise IAM
from authentication.routes import router as auth_router

# Phase 16 â€” Smart Data Capture & Intelligent Document Processing
from capture.routes import router as capture_router

# Certificate Intelligence module
from certificates.routes import router as certificates_router

# Phase 12.9 â€” Enterprise Integration Ecosystem
from connectors.routes import router as connectors_router
from database.repositories import PipelineRunRepository, SalesRepository
from database.routes import router as database_router
from dataset_library.routes import router as dataset_library_router
from ecosystem.monitoring_routes import monitoring_router
from ecosystem.plugin_routes import plugin_router
from ecosystem.public_routes import public_router
from ecosystem.routes import router as platform_router
from ecosystem.webhook_routes import webhook_router
from enterprise.routes import router as enterprise_router
from etl.logging_config import logger
from etl.package_routes import router as etl_package_router
from etl.routes import router as etl_router
from jobs.handlers import register_builtin_handlers

# Phase 11 â€” Background Processing & Job Queue
from jobs.routes import router as jobs_router
from ml.routes import router as ml_router

# Phase 18 â€” Production Monitoring
from monitoring.routes import router as phase18_monitoring_router
from notifications.routes import router as notifications_router
from organizations.invitation_routes import invitation_router, registration_router
from organizations.services import dept_router, org_router
from performance.routes import performance_router
from platform_features.routes import platform_router as platform_features_router
from saas.admin_routes import admin_router as saas_admin_router

# Phase 13 â€” Commercial SaaS Platform
from saas.routes import saas_router
from scheduler.report_scheduler import ReportScheduler
from scheduler.routes import router as scheduler_router
from semantic.routes import router as semantic_router
from services.dashboard_composition_routes import router as dashboard_composition_router
from services.dashboard_engine_routes import router as dashboard_engine_router
from services.dataset_workflow_routes import router as dataset_workflow_router
from services.etl_service import ETLService
from services.onboarding_routes import router as onboarding_router
from services.report_engine_routes import router as report_engine_router
from shared.database import Base, get_engine
from shared.dependencies import require_permissions

# Phase 12 â€” File Storage Architecture
from storage.routes import router as storage_router

# Phase 15 â€” AI Data Intelligence Operating System (Studios)
from studios.routes import router as studios_router
from validation.routes import router as validation_router
from workflows.routes import router as workflow_router

# â”€â”€ Deployment / cold-start helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


def _is_serverless() -> bool:
    """Return True when running in a serverless/readonly environment.

    On Render (persistent process) this is False unless DISABLE_STARTUP_TASKS
    is explicitly set. On Vercel it is True because VERCEL=1 is set by the
    platform (or by api/index.py).
    """
    import config

    return getattr(config, "IS_SERVERLESS", False)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Validate configuration, create tables, and seed data at startup.

    Heavy DB operations (seeding, scheduler) are deferred to a background
    task so uvicorn binds to the port immediately — preventing Render's
    port scan timeout when the remote MySQL is slow to connect.
    """
    serverless = _is_serverless()

    # Initialise monitoring integrations (no-op if not configured)
    sentry_ok = init_sentry()
    otel_ok = init_otel()
    if sentry_ok:
        logger.info("Sentry error tracking initialised.")
    if otel_ok:
        logger.info("OpenTelemetry tracing initialised.")
    if not sentry_ok and not otel_ok:
        logger.info(
            "Monitoring integrations not configured (set SENTRY_DSN / OTEL_EXPORTER_OTLP_ENDPOINT to enable)."
        )

    # Import all models so they register with Base.metadata.
    # This is lightweight (no DB calls) and must happen before any DB work.
    import ai.models  # noqa: F401
    import analytics.models  # noqa: F401
    import audit.models  # noqa: F401
    import authentication.mfa_models  # noqa: F401
    import authentication.models  # noqa: F401
    import authentication.sso_models  # noqa: F401
    import capture.models  # noqa: F401
    import connectors.models  # noqa: F401
    import database.db_setup  # noqa: F401
    import ecosystem.models  # noqa: F401
    import ecosystem.plugin_models  # noqa: F401
    import ecosystem.webhooks  # noqa: F401
    import enterprise.models  # noqa: F401
    import enterprise.subscription  # noqa: F401
    import etl.models  # noqa: F401
    import jobs.models  # noqa: F401
    import ml.models  # noqa: F401
    import notifications.models  # noqa: F401
    import organizations.models  # noqa: F401
    import organizations.workspace_models  # noqa: F401
    import saas.models  # noqa: F401
    import scheduler.models  # noqa: F401
    import storage.models  # noqa: F401
    import studios.models  # noqa: F401
    import validation.models  # noqa: F401
    import workflows.models  # noqa: F401

    # Start background job worker (skip in serverless/test mode)
    job_worker_task = None
    startup_task = None

    if not serverless and not _is_test_env:
        # Defer heavy DB startup to a background task so the port binds immediately
        async def _deferred_startup():
            try:
                validate_config()
            except Exception as e:
                logger.error(f"Configuration validation failed: {e}")
                if os.getenv("APP_ENV", "development").lower() == "production":
                    raise
            try:
                engine = get_engine()
            except Exception as e:
                logger.error(f"Database engine creation failed: {e}")
                engine = None

            if engine is not None:
                import config as _config

                if _config.DB_TYPE == "mysql":
                    logger.info(
                        "DB_TYPE=mysql; skipping create_all(), relying on Alembic migrations."
                    )
                else:
                    try:
                        Base.metadata.create_all(engine)
                    except Exception as e:
                        logger.error(f"Database table creation failed: {e}")

                # Seed ecosystem marketplace data
                try:
                    from sqlalchemy.orm import Session as EcoDbSession

                    from ecosystem.seed import seed_ecosystem_data

                    eco_db = EcoDbSession(engine)
                    seed_ecosystem_data(eco_db)
                    eco_db.close()
                except Exception as e:
                    logger.error(f"Ecosystem seed failed: {e}")

                # Seed SaaS plans and feature flags
                try:
                    from saas.services import seed_saas_data

                    saas_db = EcoDbSession(engine)
                    seed_saas_data(saas_db)
                    saas_db.close()
                except Exception as e:
                    logger.error(f"SaaS seed failed: {e}")

                # Seed Studios industry data
                try:
                    from studios.seed import seed_studios_data

                    studios_db = EcoDbSession(engine)
                    seed_studios_data(studios_db)
                    studios_db.close()
                except Exception as e:
                    logger.error(f"Studios seed failed: {e}")

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

                from authentication.services import seed_default_data

                db = DbSession(engine)
                try:
                    seed_default_data(db)
                    from config import SEED_DEMO_DATA

                    if SEED_DEMO_DATA:
                        from enterprise.demo_data import is_demo_seeded, seed_demo_data

                        if not is_demo_seeded(db):
                            seed_demo_data(db)
                            logger.info(
                                "Pilot demo data seeded (org, users, dashboards, KPIs, pipelines, AI conversations, reports). "
                                "Set SEED_DEMO_DATA=false for production."
                            )
                    # Create trial subscriptions for all orgs without one
                    from enterprise.subscription import SubscriptionService
                    from organizations.models import Organization

                    sub_svc = SubscriptionService(db)
                    try:
                        for org in db.query(Organization).filter(Organization.is_active == 1).all():
                            if not sub_svc.get_subscription(org.id):
                                sub_svc.create_trial(org.id)
                    except Exception as e:
                        logger.error(f"Subscription initialization failed: {e}")

                    # Start background report scheduler
                    try:
                        report_scheduler = ReportScheduler()
                        report_scheduler.start()
                        app.state.report_scheduler = report_scheduler

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
                logger.info("Deferred startup tasks completed: seeding, scheduler, subscriptions.")

                # Mark module-level flags so get_db() skips redundant
                # ensure_tables()/ensure_default_data() calls on the first
                # request — those would otherwise add extra DB round trips
                # to the remote MySQL on Hostinger.
                import shared.database as _sd

                _sd._tables_initialized = True
                _sd._default_data_initialized = True
            logger.info("Deferred startup finished.")

        startup_task = asyncio.create_task(_deferred_startup())
        logger.info("Deferred startup task created — heavy DB operations will run in background.")

    elif _is_test_env:
        # Test mode: run seeding synchronously (no scheduler, no job worker)
        try:
            engine = get_engine()
        except Exception as e:
            logger.error(f"Database engine creation failed: {e}")
            engine = None

        if engine is not None:
            try:
                Base.metadata.create_all(engine)
            except Exception as e:
                logger.error(f"Database table creation failed: {e}")

            from sqlalchemy.orm import Session as TestDbSession

            from authentication.services import seed_default_data

            test_db = TestDbSession(engine)
            try:
                seed_default_data(test_db)

                from ecosystem.seed import seed_ecosystem_data

                seed_ecosystem_data(test_db)

                from saas.services import seed_saas_data

                seed_saas_data(test_db)

                from studios.seed import seed_studios_data

                seed_studios_data(test_db)
            except Exception as e:
                logger.error(f"Test seeding failed: {e}")
            finally:
                test_db.close()
            logger.info("Test mode seeding completed.")

            # Mark flags so get_db() skips redundant work
            import shared.database as _sd

            _sd._tables_initialized = True
            _sd._default_data_initialized = True

    elif serverless:
        # Serverless mode: run create_all and seed synchronously (needed for cold starts)
        try:
            engine = get_engine()
        except Exception as e:
            logger.error(f"Database engine creation failed: {e}")
            engine = None

        if engine is not None:
            try:
                Base.metadata.create_all(engine)
                logger.info("Serverless create_all() completed — missing tables created if any.")
            except Exception as e:
                logger.error(f"Serverless table creation failed: {e}")
            try:
                from sqlalchemy.orm import Session as SeedDbSession

                from authentication.services import seed_default_data

                seed_db = SeedDbSession(engine)
                try:
                    seed_default_data(seed_db)
                finally:
                    seed_db.close()
                logger.info("Serverless seed_default_data completed.")
            except Exception as e:
                logger.error(f"Serverless seed_default_data failed: {e}")
            # Mark flags so get_db() skips redundant work
            import shared.database as _sd

            _sd._tables_initialized = True
            _sd._default_data_initialized = True
        logger.info("Running in serverless mode; skipped heavy startup tasks.")

    # Start background job worker only when Redis is NOT configured.
    # When Redis is present, the dedicated worker container handles jobs.
    # Running a worker on the web service too would compete for the same
    # Redis queue, causing double-processing and wasted resources.
    watchdog_task = None
    if not serverless and not _is_test_env:
        from jobs.service import get_task_queue

        queue = get_task_queue()
        if not queue.is_redis_backend:

            async def _job_worker():
                """Background worker loop — dequeues and executes jobs."""
                logger.info("Background job worker started (in-memory mode).")
                while True:
                    try:
                        task = await queue.dequeue(timeout=5.0)
                        if task is not None:
                            logger.info("Worker picked up task: %s", task.name)
                            await queue.execute(task)
                    except asyncio.CancelledError:
                        logger.info("Background job worker stopping.")
                        break
                    except Exception as e:
                        logger.error("Job worker error: %s", e)
                        await asyncio.sleep(1)

            job_worker_task = asyncio.create_task(_job_worker())
            logger.info("Background job worker task created (in-memory mode).")
        else:
            logger.info("Redis detected — job processing handled by dedicated worker container.")

        # Always run the stale-job watchdog so stuck jobs are detected even
        # if the dedicated worker is down or has crashed.
        from jobs.watchdog import run_watchdog

        async def _watchdog_wrapper():
            try:
                await run_watchdog()
            except asyncio.CancelledError:
                logger.info("Stale-job watchdog stopping.")
                raise

        watchdog_task = asyncio.create_task(_watchdog_wrapper())
        logger.info("Stale-job watchdog task created on web service.")

    yield

    # Cancel watchdog
    if watchdog_task is not None and not watchdog_task.done():
        watchdog_task.cancel()
        try:
            await watchdog_task
        except asyncio.CancelledError:
            pass

    # Cancel deferred startup if still running
    if startup_task is not None and not startup_task.done():
        startup_task.cancel()
        try:
            await startup_task
        except asyncio.CancelledError:
            pass
        logger.info("Deferred startup task cancelled.")

    # Stop background job worker
    if job_worker_task is not None:
        job_worker_task.cancel()
        try:
            await job_worker_task
        except asyncio.CancelledError:
            pass
        logger.info("Background job worker stopped.")


_is_test_env = os.getenv("PYTEST_RUNNING", "").lower() in ("1", "true", "yes")
_is_vercel = os.getenv("VERCEL", "").lower() in ("1", "true", "yes")
# On Render (persistent process) this is False; on Vercel it is True.
_is_render = not _is_vercel and not _is_test_env

app = FastAPI(
    title="DataFlow â€” Enterprise Data Intelligence API",
    description="Enterprise REST API for ETL, analytics, IAM, and pipeline management.",
    version="1.0.0",
    lifespan=lifespan,
)


app.add_middleware(
    RequestSizeLimitMiddleware, max_bytes=int(os.getenv("MAX_REQUEST_BODY_BYTES") or "52428800")
)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(MonitoringMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(TenantIsolationMiddleware)
# Phase 13 â€” Enterprise audit middleware (auto-logs mutating requests)
app.add_middleware(AuditMiddleware)
if not _is_test_env:
    app.add_middleware(
        RateLimitMiddleware,
        requests_per_minute=int(os.getenv("RATE_LIMIT_RPM") or "120"),
        redis_url=os.getenv("REDIS_URL") or None,
    )

# Instrument FastAPI for OpenTelemetry (no-op if OTel not initialised)
instrument_fastapi(app)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Return consistent error JSON for HTTPExceptions."""
    from shared.context import request_id as req_id_ctx

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.detail,
            "data": None,
            "request_id": req_id_ctx.get() or None,
        },
    )


from fastapi.exceptions import RequestValidationError  # noqa: E402


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Return validation errors without reflecting raw user input."""
    from shared.context import request_id as req_id_ctx

    errors = []
    for err in exc.errors():
        # Strip the 'input' field to prevent XSS reflection
        errors.append(
            {
                "field": ".".join(str(loc) for loc in err.get("loc", [])),
                "message": err.get("msg", "Invalid value"),
            }
        )
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "message": "Validation error",
            "data": errors,
            "request_id": req_id_ctx.get() or None,
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch unhandled exceptions and return a safe response.

    In debug mode (DEBUG=1) the real message is returned to ease diagnostics
    on Vercel and other serverless platforms.
    """
    from shared.context import request_id as req_id_ctx

    logger.exception("Unhandled exception")
    capture_exception(exc)
    metrics_registry.record_error(error_type=type(exc).__name__, component="api")
    message = "Internal server error"
    if os.getenv("DEBUG", "").lower() in ("1", "true", "yes"):
        message = f"Internal server error: {exc}"
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": message,
            "data": None,
            "request_id": req_id_ctx.get() or None,
        },
    )


_raw_cors = os.getenv("CORS_ORIGINS", "")
allow_origins = [origin.strip() for origin in _raw_cors.split(",") if origin.strip()]

if allow_origins:
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
elif not _is_test_env:
    logger.warning(
        "CORS_ORIGINS is not set. No CORS middleware will be applied. "
        "Set CORS_ORIGINS to your frontend domain(s) for production, "
        "e.g. 'https://app.example.com'."
    )

# Include Phase 4 routers
app.include_router(auth_router)
app.include_router(mfa_router)
app.include_router(sso_router)
app.include_router(users_router)
app.include_router(roles_router)
app.include_router(org_router)
app.include_router(dept_router)
app.include_router(invitation_router)
app.include_router(registration_router)
app.include_router(admin_router)
app.include_router(audit_router)
app.include_router(audit_enterprise_router)
app.include_router(database_router)
app.include_router(etl_router)
app.include_router(etl_package_router)
app.include_router(ai_router)
app.include_router(ai_enterprise_router)
app.include_router(analytics_router)
app.include_router(enterprise_router)
app.include_router(platform_features_router)
app.include_router(performance_router)
app.include_router(notifications_router)
app.include_router(scheduler_router)
app.include_router(semantic_router)
app.include_router(validation_router)
app.include_router(dataset_library_router)
app.include_router(dataset_workflow_router)
app.include_router(dashboard_engine_router)
app.include_router(dashboard_composition_router)
app.include_router(onboarding_router)
app.include_router(report_engine_router)
app.include_router(workflow_router)
app.include_router(ml_router)

# Phase 12.9 â€” Enterprise Integration Ecosystem
app.include_router(connectors_router)
app.include_router(platform_router)
app.include_router(webhook_router)
app.include_router(plugin_router)
app.include_router(public_router)
app.include_router(monitoring_router)

# Phase 13 â€” Commercial SaaS Platform
app.include_router(saas_router)
app.include_router(saas_admin_router)

# Phase 15 â€” AI Data Intelligence Operating System (Studios)
app.include_router(studios_router)

# Phase 16 â€” Smart Data Capture & Intelligent Document Processing
app.include_router(capture_router)
app.include_router(certificates_router)

# Phase 11 â€” Background Processing & Job Queue
app.include_router(jobs_router)
register_builtin_handlers()

# Phase 12 â€” File Storage Architecture
app.include_router(storage_router)

# Phase 18 â€” Production Monitoring
app.include_router(phase18_monitoring_router)


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Landing Page
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@app.get("/", include_in_schema=False)
async def landing_page():
    """Serve the DataFlow landing page."""
    static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return JSONResponse(
        {"message": "DataFlow API â€” visit /docs for API documentation"}, status_code=200
    )


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Dependencies
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def get_sales_repo() -> SalesRepository:
    """FastAPI dependency for SalesRepository."""
    return SalesRepository()


def get_run_repo() -> PipelineRunRepository:
    """FastAPI dependency for PipelineRunRepository."""
    return PipelineRunRepository()


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Health
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Lightweight liveness health check.

    Returns immediately without any database or external service calls.
    Use /ready for database connectivity checks. This endpoint is polled
    by Render's health checker and must respond in < 10ms.
    """
    return HealthResponse(
        status="healthy",
        database_connected=True,
        record_count=0,
        timestamp=datetime.now(timezone.utc),
    )


@app.get("/ready", tags=["System"])
async def readiness_check():
    """Check readiness of critical subsystems.

    Returns 200 if the database is reachable, 503 otherwise. Keep this check
    lightweight to avoid cold-start overhead.
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
        logger.error("Readiness check database probe failed: %s", e)
        checks["database"] = {"status": "not_ready"}
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
async def detailed_health_check(
    _current_user: dict = Depends(require_permissions("system.admin")),
):
    """Return detailed health status for all subsystems.

    Requires system.admin permission. Exposes readiness for database, ETL,
    AI, scheduler, email, SMS, WhatsApp, push notifications, storage, and
    internal monitoring.
    """
    from monitoring.health_check import run_full_health_check

    return JSONResponse(content=run_full_health_check())


@app.get("/health/db", tags=["System"])
async def db_health_check(
    _current_user: dict = Depends(require_permissions("system.admin")),
):
    """Check database connectivity, migration version, and pool status.

    Requires system.admin permission.
    """
    try:
        from sqlalchemy import text

        from shared.database import get_engine

        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            # Get current alembic migration version
            try:
                result = conn.execute(text("SELECT version_num FROM alembic_version LIMIT 1"))
                migration_version = result.scalar() or "unknown"
            except Exception:
                migration_version = "unknown"

        pool = engine.pool
        return JSONResponse(
            content={
                "status": "ready",
                "database": "connected",
                "migration_version": migration_version,
                "pool_size": pool.size(),
                "pool_checked_in": pool.checkedin(),
                "pool_checked_out": pool.checkedout(),
            }
        )
    except Exception as e:
        return JSONResponse(status_code=503, content={"status": "not_ready", "error": str(e)})


@app.get("/health/ocr", tags=["System"])
async def ocr_health_check(
    _current_user: dict = Depends(require_permissions("system.admin")),
):
    """Check OCR (Tesseract) availability and version."""
    try:
        from capture.ocr_engine import is_ocr_available

        available = is_ocr_available()
        version = None
        if available:
            try:
                import pytesseract

                version = str(pytesseract.get_tesseract_version())
            except Exception:
                pass
        return JSONResponse(
            content={
                "status": "available" if available else "unavailable",
                "available": available,
                "version": version,
                "engine": "tesseract",
                "error": None if available else "Tesseract binary not found on PATH",
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "unavailable", "available": False, "error": str(e)},
        )


@app.get("/health/storage", tags=["System"])
async def storage_health_check(
    _current_user: dict = Depends(require_permissions("system.admin")),
):
    """Check file storage availability."""
    try:
        from monitoring.health_check import check_storage_health

        result = check_storage_health()
        return JSONResponse(content=result)
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "error": str(e)},
        )


@app.get("/health/ai", tags=["System"])
async def ai_health_check(
    _current_user: dict = Depends(require_permissions("system.admin")),
):
    """Check AI provider availability."""
    try:
        ai_provider = os.getenv("AI_PROVIDER", "").lower()
        ai_api_key = os.getenv("AI_API_KEY") or os.getenv("OPENAI_API_KEY")
        configured = bool(ai_provider and ai_api_key)
        return JSONResponse(
            content={
                "status": "ready" if configured else "not_configured",
                "provider": ai_provider or None,
                "configured": configured,
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "error": str(e)},
        )


@app.get("/health/workers", tags=["System"])
async def workers_health_check(
    _current_user: dict = Depends(require_permissions("system.admin")),
):
    """Check background job worker status."""
    try:
        from jobs.service import get_task_queue

        queue = get_task_queue()
        stats = queue.get_stats()
        return JSONResponse(
            content={
                "status": "ready",
                "pending_tasks": queue.pending_count,
                "total_enqueued": stats.total_enqueued,
                "total_completed": stats.total_completed,
                "total_failed": stats.total_failed,
                "dead_letter_count": stats.dead_letter_count,
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "error": str(e)},
        )


@app.get("/health/queue", tags=["System"])
async def queue_health_check():
    """Safe, unauthenticated queue/Redis health check.

    Returns only safe information — no passwords, connection strings, or
    secrets. Used by monitoring and the frontend to determine if background
    processing is available.
    """
    try:
        from jobs.service import get_task_queue

        queue = get_task_queue()
        redis_connected = queue.is_redis_backend
        pending = queue.pending_count

        if redis_connected:
            return JSONResponse(
                content={
                    "status": "healthy",
                    "redis": "connected",
                    "queue": "available",
                    "pending_tasks": pending,
                }
            )
        else:
            return JSONResponse(
                content={
                    "status": "degraded",
                    "redis": "not_configured",
                    "queue": "in_memory",
                    "pending_tasks": pending,
                }
            )
    except Exception:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "redis": "disconnected",
                "queue": "unavailable",
            },
        )


@app.get("/metrics", tags=["System"])
async def prometheus_metrics(
    _current_user: dict = Depends(require_permissions("system.admin")),
):
    """Expose Prometheus-compatible metrics for scraping.

    Returns metrics in text exposition format with counters, histograms,
    and gauges for HTTP requests, database queries, pipeline runs, errors,
    session counts, and process uptime.
    """
    from fastapi.responses import PlainTextResponse

    return PlainTextResponse(
        metrics_registry.render(),
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Sales Data
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# KPIs
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Filter Options
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Pipeline
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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
            metrics_registry.record_pipeline_run(status="completed")
            record_pipeline_run(status="completed")
        except Exception as e:
            logger.error(f"Background pipeline run failed: {e}")
            metrics_registry.record_pipeline_run(status="failed")
            record_pipeline_run(status="failed")
            capture_exception(e)

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


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Root
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@app.get("/", tags=["System"])
async def root():
    """API root â€” basic info."""
    return {
        "name": "AEDIP Enterprise Data Intelligence API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn

    _default_host = (
        "0.0.0.0"  # nosec B104 â€” production containers and serverless platforms require 0.0.0.0 binding; dev default is 127.0.0.1; API_HOST env var always takes precedence
        if _is_vercel or os.getenv("APP_ENV", "").lower() == "production"
        else "127.0.0.1"
    )
    uvicorn.run(
        "api.main:app",
        host=os.getenv("API_HOST", _default_host),
        port=int(os.getenv("API_PORT") or "8000"),
        reload=True,
    )
