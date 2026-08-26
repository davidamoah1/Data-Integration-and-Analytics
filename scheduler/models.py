"""Models for scheduled report jobs."""

from datetime import datetime, timezone

from sqlalchemy import JSON, TIMESTAMP, BigInteger, Boolean, Column, String

from shared.database import Base, BigInt


class ScheduledReport(Base):
    """A scheduled report definition with cron-like recurrence."""

    __tablename__ = "scheduled_reports"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    report_type = Column(String(50), nullable=False)
    title = Column(String(500), nullable=True)
    # Cron expression: minute hour day month day_of_week
    # e.g. "0 8 * * 1" for weekly Monday 08:00
    cron = Column(String(100), nullable=False, default="0 8 * * *")
    parameters = Column(JSON, nullable=True, default=dict)
    user_id = Column(BigInteger, nullable=False, index=True)
    organization_id = Column(BigInteger, nullable=True, index=True)
    is_active = Column(Boolean, nullable=False, default=True)
    last_run_at = Column(TIMESTAMP, nullable=True)
    next_run_at = Column(TIMESTAMP, nullable=True)
    created_at = Column(TIMESTAMP, default=datetime.now(timezone.utc), nullable=False)
