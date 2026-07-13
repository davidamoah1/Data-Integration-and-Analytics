from datetime import datetime

from sqlalchemy import (
    Column,
    Date,
    Float,
    Index,
    Integer,
    String,
    TIMESTAMP,
    create_engine,
    func,
)
from sqlalchemy.orm import declarative_base

from config import DB_URL

# Keep a separate Base for existing tables (sales, pipeline_runs).
# New Phase 4 tables use shared.database.Base.
Base = declarative_base()


class SalesRecord(Base):
    """ORM model for the sales fact table."""

    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(String(50), unique=True, nullable=False, index=True)
    order_date = Column(Date, nullable=True, index=True)
    ship_date = Column(Date, nullable=True)
    customer_name = Column(String(255), nullable=True, index=True)
    segment = Column(String(100), nullable=True)
    region = Column(String(100), nullable=True, index=True)
    category = Column(String(100), nullable=True, index=True)
    sub_category = Column(String(100), nullable=True)
    product_name = Column(String(500), nullable=True)
    sales = Column(Float, nullable=False, default=0.0)
    quantity = Column(Integer, nullable=False, default=0)
    discount = Column(Float, nullable=False, default=0.0)
    profit = Column(Float, nullable=False, default=0.0)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(
        TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    __table_args__ = (
        Index("idx_region_category", "region", "category"),
        Index("idx_order_date_region", "order_date", "region"),
    )


class PipelineRun(Base):
    """ORM model for tracking pipeline execution metadata."""

    __tablename__ = "pipeline_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(50), unique=True, nullable=False, index=True)
    started_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    completed_at = Column(TIMESTAMP, nullable=True)
    status = Column(String(20), nullable=False, default="running")
    rows_extracted = Column(Integer, default=0)
    rows_transformed = Column(Integer, default=0)
    rows_loaded = Column(Integer, default=0)
    duplicates_removed = Column(Integer, default=0)
    error_message = Column(String(1000), nullable=True)


def init_db():
    """Create database tables if they do not exist.

    Creates both existing tables (sales, pipeline_runs) and Phase 4
    authentication/organization/audit tables, then seeds default data.

    Returns:
        SQLAlchemy Engine instance.
    """
    engine = create_engine(DB_URL, pool_pre_ping=True)
    Base.metadata.create_all(engine)

    # Create Phase 4 tables and seed defaults
    from shared.database import Base as SharedBase, get_engine
    from authentication.services import seed_default_data
    import authentication.models  # noqa: F401
    import organizations.models  # noqa: F401
    import audit.models  # noqa: F401
    import etl.models  # noqa: F401
    import ai.models  # noqa: F401

    shared_engine = get_engine()
    SharedBase.metadata.create_all(shared_engine)

    from sqlalchemy.orm import Session as DbSession
    db = DbSession(shared_engine)
    try:
        seed_default_data(db)
    finally:
        db.close()

    print("Database and tables created successfully. Default data seeded.")
    return engine


if __name__ == "__main__":
    import sys
    import os

    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    init_db()
