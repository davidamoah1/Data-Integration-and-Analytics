"""Migrate data from SQLite to MySQL.

Usage:
    python database/migrate_to_mysql.py

Prerequisites:
    - Set DB_TYPE=sqlite in .env (source database)
    - Set MYSQL_* variables in .env (target database)
    - MySQL database must be empty or have the schema created via init_db()
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd
from sqlalchemy import create_engine

from config import BASE_DIR
from etl.logging_config import logger


def get_sqlite_url() -> str:
    """Build SQLite URL from config (used as source)."""
    sqlite_path = os.path.join(BASE_DIR, "database", "etl_database.db")
    return f"sqlite:///{sqlite_path}"


def get_mysql_url() -> str:
    """Build MySQL URL from environment variables (used as target)."""
    import os

    host = os.getenv("MYSQL_HOST", "localhost")
    port = os.getenv("MYSQL_PORT", "3306")
    db = os.getenv("MYSQL_DATABASE", "")
    user = os.getenv("MYSQL_USER", "")
    password = os.getenv("MYSQL_PASSWORD", "")

    return f"mysql+pymysql://{user}:{password}" f"@{host}:{port}/{db}?charset=utf8mb4"


def migrate():
    """Migrate all data from SQLite to MySQL."""
    sqlite_url = get_sqlite_url()
    mysql_url = get_mysql_url()

    logger.info(f"Migration: Source = {sqlite_url}")
    logger.info(f"Migration: Target = MySQL ({mysql_url.split('@')[1]})")

    source_engine = create_engine(sqlite_url)
    target_engine = create_engine(mysql_url, pool_pre_ping=True)

    logger.info("Migration: Creating schema on MySQL target...")
    from database.db_setup import Base

    Base.metadata.create_all(target_engine)

    tables = ["sales", "pipeline_runs"]
    for table in tables:
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
