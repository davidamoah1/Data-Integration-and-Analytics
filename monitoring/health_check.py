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
from datetime import datetime, timedelta

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
        age = (datetime.utcnow() - started_at.tz_localize(None)).total_seconds() / 3600

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


def run_full_health_check() -> dict:
    """Run all health checks and return a combined report.

    Returns:
        Dict with all health check results and an overall status.
    """
    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "database": check_database_connection(),
        "data_freshness": check_data_freshness(),
        "pipeline": check_pipeline_health(),
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
