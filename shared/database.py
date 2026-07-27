"""Shared database infrastructure — Base, engine, session factory.

All ORM models across the platform import Base from here to ensure
a single metadata registry for create_all and Alembic autogenerate.
"""

from sqlalchemy import BigInteger, Integer, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

# SQLite doesn't support BigInteger autoincrement; use Integer variant for SQLite.
BigInt = BigInteger().with_variant(Integer, "sqlite")

_engine = None


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
    return _engine


def reset_engine():
    """Dispose and clear the cached engine. Useful for tests."""
    global _engine
    if _engine is not None:
        _engine.dispose()
        _engine = None


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

    Yields:
        Session: SQLAlchemy session, auto-closed after request.
    """
    factory = get_session_factory()
    db = factory()
    try:
        yield db
    finally:
        db.close()
