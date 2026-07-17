"""Shared database infrastructure — Base, engine, session factory.

All ORM models across the platform import Base from here to ensure
a single metadata registry for create_all and Alembic autogenerate.
"""

from sqlalchemy import BigInteger, Integer, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from config import DB_TYPE, DB_URL

Base = declarative_base()

# SQLite doesn't support BigInteger autoincrement; use Integer variant for SQLite.
BigInt = BigInteger().with_variant(Integer, "sqlite")


def get_engine(**kwargs):
    """Create a SQLAlchemy engine with appropriate pooling settings.

    Returns:
        SQLAlchemy Engine instance.
    """
    defaults = {"pool_pre_ping": True}
    if DB_TYPE == "mysql":
        defaults["pool_size"] = 10
        defaults["pool_recycle"] = 3600
        defaults["max_overflow"] = 20
    defaults.update(kwargs)
    return create_engine(DB_URL, **defaults)


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
