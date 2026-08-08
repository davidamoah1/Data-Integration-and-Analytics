"""Monitoring API routes.

Provides endpoints for:
- Prometheus metrics scraping (/metrics)
- Enhanced health checks (/health/live, /health/ready, /health/detailed)
- Monitoring status (/monitoring/status)
"""

import os
from datetime import datetime, timezone

from fastapi import APIRouter
from fastapi.responses import JSONResponse, PlainTextResponse

from monitoring.otel import is_initialised as otel_ready
from monitoring.prometheus import metrics_registry
from monitoring.sentry_integration import is_initialised as sentry_ready

router = APIRouter(prefix="/monitoring", tags=["Monitoring"])


@router.get("/metrics")
async def prometheus_metrics():
    """Prometheus-compatible metrics endpoint.

    Returns metrics in text exposition format for scraping by Prometheus
    or compatible systems (Grafana Agent, VictoriaMetrics, etc.).
    """
    content = metrics_registry.render()
    return PlainTextResponse(content, media_type="text/plain; version=0.0.4; charset=utf-8")


@router.get("/status")
async def monitoring_status():
    """Return the status of monitoring integrations."""
    return JSONResponse(
        content={
            "sentry": {"enabled": sentry_ready()},
            "opentelemetry": {"enabled": otel_ready()},
            "prometheus": {"enabled": True},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )


@router.get("/health/live")
async def liveness():
    """Liveness probe — returns 200 if the process is running.

    This probe indicates the application process has not deadlocked
    or crashed. It does NOT check dependencies.
    """
    return JSONResponse(
        content={
            "status": "alive",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )


@router.get("/health/ready")
async def readiness():
    """Readiness probe — returns 200 if the app can serve traffic.

    Checks database connectivity. Returns 503 if the database is unreachable.
    """
    checks: dict[str, dict] = {}
    overall = True

    # Database check
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

    # Redis check (if configured)
    redis_url = os.getenv("REDIS_URL", "")
    if redis_url:
        try:
            import redis as redis_lib

            r = redis_lib.from_url(redis_url, socket_timeout=2)
            r.ping()
            checks["redis"] = {"status": "ready"}
        except ImportError:
            checks["redis"] = {"status": "not_checked", "reason": "redis library not installed"}
        except Exception as e:
            checks["redis"] = {"status": "not_ready", "error": str(e)}
            overall = False

    # Sentry check
    checks["sentry"] = {"status": "ready" if sentry_ready() else "not_configured"}

    # OpenTelemetry check
    checks["opentelemetry"] = {"status": "ready" if otel_ready() else "not_configured"}

    status_code = 200 if overall else 503
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "ready" if overall else "not_ready",
            "checks": checks,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


@router.get("/health/detailed")
async def detailed_health():
    """Detailed health check for all subsystems."""
    from monitoring.health_check import run_full_health_check

    report = run_full_health_check()

    # Add monitoring integration status
    report["monitoring"] = {
        **report.get("monitoring", {}),
        "sentry": sentry_ready(),
        "opentelemetry": otel_ready(),
        "prometheus": True,
    }

    return JSONResponse(content=report)
