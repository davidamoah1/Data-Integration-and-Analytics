from sqlalchemy import TIMESTAMP, Column, Date, Float, Index, Integer, String, func

from etl.logging_config import logger
from shared.database import Base, get_engine

# Sales and pipeline-run models share the application's authoritative metadata
# registry so Alembic can discover the complete schema.


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
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_region_category", "region", "category"),
        Index("idx_order_date_region", "order_date", "region"),
    )


class PipelineRun(Base):
    """ORM model for tracking pipeline execution metadata."""

    __tablename__ = "pipeline_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(50), unique=True, nullable=False, index=True)
    started_at = Column(TIMESTAMP, server_default=func.now(), nullable=False, index=True)
    completed_at = Column(TIMESTAMP, nullable=True)
    status = Column(String(20), nullable=False, default="running", index=True)
    rows_extracted = Column(Integer, default=0)
    rows_transformed = Column(Integer, default=0)
    rows_loaded = Column(Integer, default=0)
    duplicates_removed = Column(Integer, default=0)
    error_message = Column(String(1000), nullable=True)

    __table_args__ = (Index("idx_pipeline_status_started", "status", "started_at"),)


def init_db():
    """Create database tables if they do not exist.

    Creates both existing tables (sales, pipeline_runs) and Phase 4
    authentication/organization/audit tables, then seeds default data.

    This is a manual dev/test convenience script only. Production MySQL
    schema must be created exclusively via `alembic upgrade head` — running
    this against a MySQL DB_TYPE raises instead of calling create_all(),
    to avoid schema drift from migration history.

    Returns:
        SQLAlchemy Engine instance.
    """
    import config

    if config.DB_TYPE == "mysql":
        raise RuntimeError(
            "init_db() uses Base.metadata.create_all() and must not be run against "
            "MySQL. Use 'alembic upgrade head' to create/update the production schema."
        )

    engine = get_engine()
    Base.metadata.create_all(engine)

    # Create application tables and seed defaults
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
    from authentication.services import seed_default_data

    Base.metadata.create_all(engine)

    from sqlalchemy.orm import Session as DbSession

    db = DbSession(engine)
    try:
        seed_default_data(db)
    finally:
        db.close()

    logger.info("Database and tables created successfully. Default data seeded.")
    return engine


if __name__ == "__main__":
    import os
    import sys

    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    init_db()
