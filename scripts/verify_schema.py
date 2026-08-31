#!/usr/bin/env python
"""Pre-start schema verification safeguard.

Runs on every Render deployment BEFORE the application starts accepting
traffic. Verifies:
  1. Database connectivity
  2. Alembic version matches the migration head
  3. No schema drift for critical tables

If any check fails, the process exits with a non-zero code, preventing
the application from starting with a mismatched schema.

This script is designed to be called from the Docker CMD or Render
start script, e.g.:

    python scripts/verify_schema.py && uvicorn api.main:app ...

Environment variables:
  DATABASE_URL  — SQLAlchemy URL for the production database
  DB_TYPE       — Database type (mysql, sqlite)
  APP_ENV       — Application environment (production, development)
"""

import logging
import os
import sys

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("schema_check")


def main() -> int:
    # Ensure we can import project modules
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    try:
        # Import all models to populate metadata
        import ai.models  # noqa: F401
        import analytics.models  # noqa: F401
        import audit.models  # noqa: F401
        import authentication.mfa_models  # noqa: F401
        import authentication.models  # noqa: F401
        import authentication.sso_models  # noqa: F401
        import capture.models  # noqa: F401
        import config
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
        import services.dataset_workflow_models  # noqa: F401
        import storage.models  # noqa: F401
        import studios.models  # noqa: F401
        import validation.models  # noqa: F401
        import workflows.models  # noqa: F401
    except Exception as e:
        logger.error("Failed to import models: %s", e)
        return 1

    # 1. Check database connectivity
    from sqlalchemy import create_engine, text

    db_url = config.DB_URL
    if not db_url:
        logger.error("DATABASE_URL is not set")
        return 1

    # Don't log the URL (may contain credentials)
    db_type = db_url.split("://")[0]
    logger.info("Database type: %s", db_type)

    try:
        engine = create_engine(db_url, pool_pre_ping=True, connect_args={"connect_timeout": 10})
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database connectivity: OK")
    except Exception as e:
        logger.error("Database connectivity check FAILED: %s", type(e).__name__)
        return 1

    # 2. Check Alembic version
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version_num FROM alembic_version"))
            current_version = result.scalar()
        logger.info("Current Alembic version: %s", current_version)
    except Exception as e:
        logger.error("Failed to read alembic_version table: %s", type(e).__name__)
        return 1

    # 3. Get expected head from Alembic
    try:
        from alembic.config import Config
        from alembic.script import ScriptDirectory

        alembic_cfg = Config(
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "alembic.ini")
        )
        script_dir = ScriptDirectory.from_config(alembic_cfg)
        heads = script_dir.get_heads()
        if len(heads) > 1:
            logger.error("Multiple Alembic heads detected: %s", heads)
            return 1
        expected_head = heads[0]
        logger.info("Expected Alembic head: %s", expected_head)
    except Exception as e:
        logger.warning("Could not determine Alembic head: %s", e)
        # Non-fatal — continue with column checks
        expected_head = None

    if expected_head and current_version != expected_head:
        logger.error(
            "SCHEMA DRIFT: Database is at %s but code expects %s. "
            "Run 'alembic upgrade head' before starting the application.",
            current_version,
            expected_head,
        )
        return 1

    # 4. Check critical columns exist
    critical_checks = [
        ("background_jobs", "idempotency_key"),
        ("background_jobs", "status"),
        ("background_jobs", "organization_id"),
    ]

    from sqlalchemy import inspect

    inspector = inspect(engine)

    all_ok = True
    for table, column in critical_checks:
        if table not in inspector.get_table_names():
            logger.error("MISSING TABLE: %s", table)
            all_ok = False
            continue
        columns = [c["name"] for c in inspector.get_columns(table)]
        if column not in columns:
            logger.error("MISSING COLUMN: %s.%s", table, column)
            all_ok = False
        else:
            logger.info("OK: %s.%s exists", table, column)

    if not all_ok:
        logger.error("Schema verification FAILED — refusing to start")
        return 1

    logger.info("Schema verification PASSED — all checks OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
