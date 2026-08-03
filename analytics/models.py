from sqlalchemy import (
    JSON,
    TIMESTAMP,
    BigInteger,
    Boolean,
    Column,
    Float,
    Integer,
    String,
    Text,
    func,
)

from shared.database import Base, BigInt


class Dashboard(Base):
    __tablename__ = "analytics_dashboards"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    organization_id = Column(BigInteger, nullable=True, index=True)
    owner_id = Column(BigInteger, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    theme = Column(String(50), nullable=False, default="default")
    layout = Column(JSON, nullable=False, default=list)
    version = Column(Integer, nullable=False, default=1)
    is_public = Column(Boolean, nullable=False, default=False)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)


class DashboardWidget(Base):
    __tablename__ = "analytics_dashboard_widgets"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    organization_id = Column(BigInteger, nullable=False, index=True)
    dashboard_id = Column(BigInteger, nullable=False, index=True)
    widget_type = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    configuration = Column(JSON, nullable=False, default=dict)
    position = Column(JSON, nullable=False, default=dict)
    group_name = Column(String(100), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)


class DashboardFavorite(Base):
    __tablename__ = "analytics_dashboard_favorites"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    organization_id = Column(BigInteger, nullable=False, index=True)
    dashboard_id = Column(BigInteger, nullable=False, index=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)


class KPI(Base):
    __tablename__ = "analytics_kpis"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    organization_id = Column(BigInteger, nullable=True, index=True)
    owner_id = Column(BigInteger, nullable=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True, index=True)
    formula = Column(Text, nullable=False)
    target_value = Column(Float, nullable=True)
    warning_threshold = Column(Float, nullable=True)
    critical_threshold = Column(Float, nullable=True)
    unit = Column(String(50), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)


class KPIHistory(Base):
    __tablename__ = "analytics_kpi_history"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    kpi_id = Column(BigInteger, nullable=False, index=True)
    value = Column(Float, nullable=False)
    status = Column(String(20), nullable=False, default="healthy")
    recorded_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)


class AnalyticsAlert(Base):
    __tablename__ = "analytics_alerts"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    organization_id = Column(BigInteger, nullable=True, index=True)
    alert_type = Column(String(50), nullable=False, index=True)
    severity = Column(String(20), nullable=False, default="warning")
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    source_type = Column(String(50), nullable=True)
    source_id = Column(BigInteger, nullable=True)
    acknowledged_by = Column(BigInteger, nullable=True)
    acknowledged_at = Column(TIMESTAMP, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
