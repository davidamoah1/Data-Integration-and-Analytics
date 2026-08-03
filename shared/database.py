"""Shared database infrastructure — Base, engine, session factory.

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
                duration_ms, threshold_ms, stmt_preview,
            )


def ensure_tables(engine):
    """Create all tables if they do not exist. Idempotent via module flag."""
    global _tables_initialized
    if _tables_initialized:
        return
    Base.metadata.create_all(engine)
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
    global _engine, _tables_initialized, _default_data_initialized
    if _engine is not None:
        _engine.dispose()
        _engine = None
    _tables_initialized = False
    _default_data_initialized = False


def get_session_factory(engine=None) -> sessionmaker:
    """Create a sessionmaker bound to the given engine (or default).

    Returns:
        sessionmaker instance.
    """
    if engine is None:
        engine = get_engine()
    return sessionmaker(bind=engine, expire_on_commit=False)


def get_db():
    """FastAPI dependency that yields a database session.

    Lazily creates tables and seeds default data on the first request in a
    process. This is especially important on serverless platforms where startup
    tasks are skipped.
    """
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
