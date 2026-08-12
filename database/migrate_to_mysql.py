"""Migrate data from SQLite to MySQL.

Usage:
    python database/migrate_to_mysql.py

Prerequisites:
    - Set DB_TYPE=sqlite in .env (source database)
    - Set MYSQL_* variables in .env (target database)
    - The MySQL target schema must already exist, created via
      `alembic upgrade head` against MYSQL_* — this script only copies data,
      it does not create or alter schema.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd
from sqlalchemy import create_engine

from config import BASE_DIR
from etl.logging_config import logger
from shared.database import get_engine


def get_sqlite_url() -> str:
    """Build SQLite URL from config (used as source)."""
    sqlite_path = os.path.join(BASE_DIR, "database", "etl_database.db")
    return f"sqlite:///{sqlite_path}"


def get_mysql_url() -> str:
    """Build MySQL URL from environment variables (used as target)."""
    host = os.getenv("MYSQL_HOST", "localhost")
    port = os.getenv("MYSQL_PORT", "3306")
    db = os.getenv("MYSQL_DATABASE", "")
    user = os.getenv("MYSQL_USER", "")
    password = os.getenv("MYSQL_PASSWORD", "")

    return f"mysql+pymysql://{user}:{password}" f"@{host}:{port}/{db}?charset=utf8mb4"


def _get_all_table_names(metadata) -> list[str]:
    """Get all table names from metadata, ordered by dependency."""
    return (
        list(metadata.sorted_tables.keys())
        if hasattr(metadata, "sorted_tables")
        else list(metadata.tables.keys())
    )


def migrate():
    """Migrate all data from SQLite to MySQL."""
    sqlite_url = get_sqlite_url()
    mysql_url = get_mysql_url()

    logger.info(f"Migration: Source = {sqlite_url}")
    logger.info(f"Migration: Target = MySQL ({mysql_url.split('@')[1]})")

    source_engine = create_engine(sqlite_url)
    target_engine = get_engine()

    logger.info(
        "Migration: assuming MySQL target schema already exists "
        "(created via 'alembic upgrade head'); this script only copies data."
    )
    # Import all model modules so Base.metadata reflects the full table set
    # for ordering/copying purposes only — schema itself is NOT created here.
    import ai.models  # noqa: F401
    import analytics.models  # noqa: F401
    import audit.models  # noqa: F401
    import authentication.models  # noqa: F401
    import enterprise.models  # noqa: F401
    import enterprise.subscription  # noqa: F401
    import etl.models  # noqa: F401
    import notifications.models  # noqa: F401
    import organizations.models  # noqa: F401
    import scheduler.models  # noqa: F401
    from database.db_setup import Base

    # Migrate all tables in dependency order
    all_tables = [t.name for t in Base.metadata.sorted_tables]
    logger.info(f"Migration: Found {len(all_tables)} tables to migrate: {all_tables}")

    for table in all_tables:
        try:
            df = pd.read_sql_table(table, source_engine)
            if df.empty:
                logger.info(f"Migration: Table '{table}' is empty, skipping.")
                continue
            df.to_sql(table, con=target_engine, if_exists="append", index=False, method="multi")
            logger.info(f"Migration: Migrated {len(df)} rows from '{table}'.")
            print(f"  Migrated {len(df)} rows from '{table}'.")
        except Exception as e:
            logger.warning(f"Migration: Could not migrate table '{table}': {e}")
            print(f"  Skipped '{table}': {e}")

    logger.info("Migration completed successfully.")
    print("\nMigration completed successfully.")


if __name__ == "__main__":
    migrate()
