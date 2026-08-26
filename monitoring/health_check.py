"""Health check and monitoring utilities.

Provides functions for:
  - Database connectivity checks
  - Pipeline status monitoring
  - Data freshness validation
  - System health reporting

Can be run standalone:
    python monitoring/health_check.py
"""

import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from etl.logging_config import logger


def check_database_connection() -> dict:
    """Check if the database is accessible.

    Returns:
        Dict with 'connected' (bool) and 'record_count' (int).
    """
    try:
        from database.repositories import SalesRepository

        repo = SalesRepository()
        count = repo.get_record_count()
        return {"connected": True, "record_count": count}
    except Exception as e:
        logger.error(f"Health check: Database connection failed: {e}")
        return {"connected": False, "record_count": 0, "error": str(e)}


def check_database_pool() -> dict:
    """Check connection pool status and database metadata.

    Returns:
        Dict with pool config, active connections, and database type info.
    """
    try:
        from config import DB_TYPE, MAX_OVERFLOW, POOL_RECYCLE, POOL_SIZE, POOL_TIMEOUT
        from shared.database import get_engine

        engine = get_engine()
        pool = engine.pool
        result = {
            "db_type": DB_TYPE,
            "pool_size": POOL_SIZE,
            "max_overflow": MAX_OVERFLOW,
            "pool_timeout": POOL_TIMEOUT,
            "pool_recycle": POOL_RECYCLE,
            "checked_out": pool.checkedout() if hasattr(pool, "checkedout") else None,
            "size": pool.size() if hasattr(pool, "size") else None,
        }

        if DB_TYPE == "mysql":
            from sqlalchemy import text

            with engine.connect() as conn:
                version = conn.execute(text("SELECT VERSION()")).scalar()
                result["mysql_version"] = version

                db_name = conn.execute(text("SELECT DATABASE()")).scalar()
                result["database"] = db_name

                threads = conn.execute(text("SHOW STATUS LIKE 'Threads_connected'")).fetchone()
                result["threads_connected"] = threads[1] if threads else None

                uptime = conn.execute(text("SHOW STATUS LIKE 'Uptime'")).fetchone()
                result["uptime_seconds"] = int(uptime[1]) if uptime else None

        return result
    except Exception as e:
        logger.error(f"Health check: Database pool check failed: {e}")
        return {"error": str(e)}


def check_data_freshness(max_age_hours: int = 48) -> dict:
    """Check if the data in the database is fresh.

    Args:
        max_age_hours: Maximum acceptable age in hours since the last
            pipeline run.

    Returns:
        Dict with 'fresh' (bool), 'last_run' (str), and 'age_hours' (float).
    """
    try:
        from database.repositories import PipelineRunRepository

        repo = PipelineRunRepository()
        runs = repo.get_recent_runs(limit=1)
        if runs.empty:
            return {"fresh": False, "last_run": None, "age_hours": None}

        last_run = runs.iloc[0]
        started_at = pd.Timestamp(last_run["started_at"])
        if started_at.tzinfo is None:
            started_at = started_at.tz_localize("UTC")
        age = (datetime.now(timezone.utc) - started_at).total_seconds() / 3600

        return {
            "fresh": age <= max_age_hours,
            "last_run": str(last_run["started_at"]),
            "age_hours": round(age, 1),
            "status": last_run["status"],
        }
    except Exception as e:
        logger.error(f"Health check: Data freshness check failed: {e}")
        return {"fresh": False, "error": str(e)}


def check_pipeline_health() -> dict:
    """Check recent pipeline run health.

    Returns:
        Dict with 'total_runs', 'successful', 'failed', and 'last_5_statuses'.
    """
    try:
        from database.repositories import PipelineRunRepository

        repo = PipelineRunRepository()
        runs = repo.get_recent_runs(limit=10)
        if runs.empty:
            return {"total_runs": 0, "successful": 0, "failed": 0, "last_5_statuses": []}

        successful = (runs["status"] == "completed").sum()
        failed = (runs["status"] == "failed").sum()

        return {
            "total_runs": len(runs),
            "successful": int(successful),
            "failed": int(failed),
            "last_5_statuses": runs["status"].head(5).tolist(),
        }
    except Exception as e:
        logger.error(f"Health check: Pipeline health check failed: {e}")
        return {"error": str(e)}


def check_scheduler_health() -> dict:
    """Check whether the background report scheduler is running."""
    try:
        from scheduler.report_scheduler import ReportScheduler

        return {"status": "ready" if ReportScheduler.is_running() else "not_ready"}
    except Exception as e:
        logger.error(f"Health check: Scheduler health check failed: {e}")
        return {"status": "not_ready", "error": str(e)}


def check_email_health() -> dict:
    """Check whether SMTP email is configured."""
    host = os.getenv("SMTP_HOST")
    port = os.getenv("SMTP_PORT")
    return {
        "status": "ready" if host and port else "not_configured",
        "host": host,
        "port": port,
    }


def check_sms_health() -> dict:
    """Check whether an SMS provider is configured."""
    ready = bool(os.getenv("SMS_PROVIDER") or os.getenv("TWILIO_SID"))
    return {"status": "ready" if ready else "not_configured"}


def check_whatsapp_health() -> dict:
    """Check whether a WhatsApp provider is configured."""
    ready = bool(
        os.getenv("WHATSAPP_PROVIDER")
        or os.getenv("WHATSAPP_BUSINESS_ID")
        or os.getenv("TWILIO_SID")
    )
    return {"status": "ready" if ready else "not_configured"}


def check_push_health() -> dict:
    """Check whether a push notification provider is configured."""
    ready = bool(
        os.getenv("PUSH_PROVIDER")
        or os.getenv("FIREBASE_CREDENTIALS_PATH")
        or os.getenv("FIREBASE_CREDENTIALS")
    )
    return {"status": "ready" if ready else "not_configured"}


def check_storage_health() -> dict:
    """Check whether the configured storage paths are usable."""
    try:
        raw_path = os.getenv("RAW_DATA_PATH", "dataset")
        raw_dir = Path(raw_path).parent if Path(raw_path).suffix else Path(raw_path)
        raw_dir.mkdir(parents=True, exist_ok=True)
        test_file = raw_dir / ".health_check"
        test_file.write_text("ok")
        test_file.unlink()
        return {"status": "ready", "path": str(raw_dir)}
    except Exception as e:
        logger.error(f"Health check: Storage health check failed: {e}")
        return {"status": "not_ready", "error": str(e)}


def check_monitoring_health() -> dict:
    """Check internal monitoring/logging readiness."""
    return {"status": "ready"}


def run_full_health_check() -> dict:
    """Run all health checks and return a combined report.

    Returns:
        Dict with all health check results and an overall status.
    """
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database": check_database_connection(),
        "database_pool": check_database_pool(),
        "data_freshness": check_data_freshness(),
        "pipeline": check_pipeline_health(),
        "scheduler": check_scheduler_health(),
        "email": check_email_health(),
        "sms": check_sms_health(),
        "whatsapp": check_whatsapp_health(),
        "push": check_push_health(),
        "storage": check_storage_health(),
        "monitoring": check_monitoring_health(),
    }

    db_ok = report["database"].get("connected", False)
    data_ok = report["data_freshness"].get("fresh", False)
    pipeline_ok = report["pipeline"].get("failed", 1) < 3

    report["overall_status"] = "healthy" if (db_ok and data_ok and pipeline_ok) else "degraded"
    return report


if __name__ == "__main__":
    import json

    report = run_full_health_check()
    print(json.dumps(report, indent=2))
    sys.exit(0 if report["overall_status"] == "healthy" else 1)
