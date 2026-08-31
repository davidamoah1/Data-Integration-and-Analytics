"""Shared database infrastructure â€” Base, engine, session factory.

All ORM models across the platform import Base from here to ensure
a single metadata registry for create_all and Alembic autogenerate.
"""

import logging
import time

from sqlalchemy import BigInteger, Integer, create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker

logger = logging.getLogger("database")

Base = declarative_base()

# SQLite doesn't support BigInteger autoincrement; use Integer variant for SQLite.
BigInt = BigInteger().with_variant(Integer, "sqlite")

_engine = None
_tables_initialized = False
_default_data_initialized = False


def _attach_slow_query_listener(engine, threshold_ms: int):
    """Attach a before/after cursor event listener that logs slow queries."""

    @event.listens_for(engine, "before_cursor_execute")
    def _before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        context._query_start_time = time.perf_counter()

    @event.listens_for(engine, "after_cursor_execute")
    def _after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        start = getattr(context, "_query_start_time", None)
        if start is None:
            return
        duration_ms = (time.perf_counter() - start) * 1000
        if duration_ms >= threshold_ms:
            stmt_preview = statement[:200].replace("\n", " ")
            logger.warning(
                "Slow query %.1fms (threshold %dms): %s",
                duration_ms,
                threshold_ms,
                stmt_preview,
            )


def ensure_tables(engine):
    """Create all tables if they do not exist. Idempotent via module flag.

    For both SQLite and MySQL, create_all() is used with checkfirst=True
    (the default) which only creates tables that don't already exist.
    This is safe even for production MySQL — it won't modify existing
    tables or cause schema drift. Alembic migrations remain the primary
    schema management tool; this is a safety net for missing tables.
    """
    global _tables_initialized
    if _tables_initialized:
        return

    import config

    # Create any missing tables (checkfirst=True is the default, so
    # existing tables are never modified or recreated).
    Base.metadata.create_all(engine)

    # Add missing columns to existing SQLite tables
    if config.DB_TYPE == "sqlite":
        from sqlalchemy import inspect as _inspect
        from sqlalchemy import text as _text
        from sqlalchemy.types import (
            JSON,
            TIMESTAMP,
            BigInteger,
            Boolean,
            DateTime,
            Float,
            Integer,
            Numeric,
            String,
            Text,
        )

        insp = _inspect(engine)
        existing_tables = set(insp.get_table_names())

        # Map SQLAlchemy column types to MySQL DDL
        def _col_ddl(col):
            col_type = col.type
            if isinstance(col_type, (BigInteger, Integer)):
                return "BIGINT" if isinstance(col_type, BigInteger) else "INTEGER"
            elif isinstance(col_type, Boolean):
                return "INTEGER"
            elif isinstance(col_type, String):
                length = col_type.length or 255
                return f"VARCHAR({length})"
            elif isinstance(col_type, Text):
                return "TEXT"
            elif isinstance(col_type, JSON):
                return "JSON"
            elif isinstance(col_type, (TIMESTAMP, DateTime)):
                return "TIMESTAMP"
            elif isinstance(col_type, (Float, Numeric)):
                return "DECIMAL(20,4)"
            else:
                return "TEXT"

        # Check every ORM model's table for missing columns
        for table_name, table_obj in Base.metadata.tables.items():
            if table_name not in existing_tables:
                continue
            existing_cols = {c["name"] for c in insp.get_columns(table_name)}
            with engine.begin() as conn:
                for col in table_obj.columns:
                    if col.name not in existing_cols:
                        ddl_type = _col_ddl(col)
                        nullable = "" if col.nullable else " NOT NULL"
                        default = ""
                        if (
                            col.default is not None
                            and hasattr(col.default, "arg")
                            and col.default.arg is not None
                        ):
                            default_val = col.default.arg
                            if isinstance(default_val, (int, float)):
                                default = f" DEFAULT {default_val}"
                            elif isinstance(default_val, bool):
                                default = f" DEFAULT {1 if default_val else 0}"
                        logger.info("Adding missing column %s.%s", table_name, col.name)
                        conn.execute(
                            _text(
                                f"ALTER TABLE {table_name} ADD COLUMN {col.name} {ddl_type}{nullable}{default}"
                            )
                        )

    _tables_initialized = True


def ensure_default_data(db):
    """Seed default roles, permissions, and super admin if missing."""
    global _default_data_initialized
    if _default_data_initialized:
        return
    from authentication.services import seed_default_data

    seed_default_data(db)
    _default_data_initialized = True


def get_engine(**kwargs):
    """Create a SQLAlchemy engine with appropriate pooling settings.

    Reads DB_URL and DB_TYPE from config at call time so that test
    monkeypatching of config attributes takes effect. The engine is cached
    per process to avoid repeated connection setup.

    Returns:
        SQLAlchemy Engine instance, or raises if configuration is invalid.
    """
    global _engine
    if _engine is not None:
        return _engine

    import config

    defaults = {"pool_pre_ping": True}
    if config.DB_TYPE == "mysql":
        defaults["pool_size"] = config.POOL_SIZE
        defaults["pool_recycle"] = config.POOL_RECYCLE
        defaults["max_overflow"] = config.MAX_OVERFLOW
        defaults["pool_timeout"] = config.POOL_TIMEOUT
    defaults.update(kwargs)

    if not config.DB_URL:
        raise RuntimeError("DB_URL is not configured. Set DB_TYPE and connection variables.")

    _engine = create_engine(config.DB_URL, **defaults)

    # Attach slow query logging
    threshold = getattr(config, "SLOW_QUERY_THRESHOLD_MS", 500)
    _attach_slow_query_listener(_engine, threshold)

    return _engine


def reset_engine():
    """Dispose and clear the cached engine. Useful for tests."""
    global _engine, _tables_initialized, _default_data_initialized, _session_factory
    if _engine is not None:
        _engine.dispose()
        _engine = None
    _tables_initialized = False
    _default_data_initialized = False
    _session_factory = None


_session_factory: sessionmaker | None = None


def get_session_factory(engine=None) -> sessionmaker:
    """Create a sessionmaker bound to the given engine (or default).

    The sessionmaker is cached per process to avoid repeated construction.

    Returns:
        sessionmaker instance.
    """
    global _session_factory
    if _session_factory is not None and engine is None:
        return _session_factory
    if engine is None:
        engine = get_engine()
    _session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    return _session_factory


def get_db():
    """FastAPI dependency that yields a database session.

    Lazily creates tables and seeds default data on the first request in a
    process. This is especially important on serverless platforms where startup
    tasks are skipped.
    """
    try:
        engine = get_engine()
        ensure_tables(engine)
        factory = get_session_factory(engine)
        db = factory()
        try:
            ensure_default_data(db)
            db.commit()
            yield db
        finally:
            db.close()
    except Exception as e:
        import logging

        logging.getLogger("database").error(
            "get_db() failed: %s: %s", type(e).__name__, e, exc_info=True
        )
        from fastapi import HTTPException

        raise HTTPException(
            status_code=500,
            detail=f"Database initialization error: {type(e).__name__}: {e}",
        ) from e
