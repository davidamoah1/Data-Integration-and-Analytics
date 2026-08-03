"""Alembic migration environment for AEDIP."""

import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config, pool

from alembic import context

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import ai.models  # noqa: F401, E402
import analytics.models  # noqa: F401, E402
import audit.models  # noqa: F401, E402
import authentication.models  # noqa: F401, E402
import capture.models  # noqa: F401, E402
import database.db_setup  # noqa: F401, E402
import enterprise.models  # noqa: F401, E402
import enterprise.subscription  # noqa: F401, E402
import etl.models  # noqa: F401, E402
import jobs.models  # noqa: F401, E402
import notifications.models  # noqa: F401, E402
import organizations.models  # noqa: F401, E402
import organizations.workspace_models  # noqa: F401, E402
import scheduler.models  # noqa: F401, E402
import storage.models  # noqa: F401, E402
from config import DB_TYPE, DB_URL, validate_config  # noqa: E402
from shared.database import Base  # noqa: E402

config = context.config
validate_config()
config.set_main_option("sqlalchemy.url", DB_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _migration_options() -> dict:
    return {
        "target_metadata": target_metadata,
        "compare_type": True,
        "compare_server_default": True,
        "render_as_batch": DB_TYPE == "sqlite",
    }


def run_migrations_offline() -> None:
    """Run migrations in offline mode."""
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        **_migration_options(),
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against the configured database."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, **_migration_options())

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
