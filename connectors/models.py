"""SQLAlchemy models for the Enterprise Connector Framework."""

from sqlalchemy import JSON, TIMESTAMP, Boolean, Column, Integer, String, Text, func

from shared.database import Base, BigInt


class Connector(Base):
    """Registered data connector instance."""

    __tablename__ = "ecosystem_connectors"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    organization_id = Column(BigInt, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    connector_type = Column(String(100), nullable=False)  # postgresql, mysql, s3, rest_api, etc.
    category = Column(String(50), nullable=False)  # database, file, cloud_storage, api
    description = Column(Text, nullable=True)
    configuration = Column(JSON, nullable=True)  # connection params (credentials stored encrypted)
    auth_config = Column(JSON, nullable=True)  # auth method + credentials
    status = Column(
        String(20), nullable=False, default="inactive"
    )  # active, inactive, error, testing
    last_tested_at = Column(TIMESTAMP, nullable=True)
    last_test_result = Column(JSON, nullable=True)
    is_public = Column(Boolean, default=False, nullable=False)
    created_by = Column(BigInt, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)


class ConnectorExecution(Base):
    """Log of connector data extraction executions."""

    __tablename__ = "ecosystem_connector_executions"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    connector_id = Column(BigInt, nullable=False, index=True)
    organization_id = Column(BigInt, nullable=False, index=True)
    status = Column(String(20), nullable=False)  # running, success, failed, cancelled
    rows_extracted = Column(Integer, nullable=True)
    bytes_transferred = Column(BigInt, nullable=True)
    error_message = Column(Text, nullable=True)
    started_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    completed_at = Column(TIMESTAMP, nullable=True)
    extra_metadata = Column(JSON, nullable=True)


class ConnectorType(Base):
    """Catalog of available connector types (for marketplace discovery)."""

    __tablename__ = "ecosystem_connector_types"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    type_code = Column(String(100), unique=True, nullable=False)  # postgresql, mysql, s3, etc.
    display_name = Column(String(200), nullable=False)
    category = Column(String(50), nullable=False)  # database, file, cloud_storage, api
    description = Column(Text, nullable=True)
    icon = Column(String(100), nullable=True)
    config_schema = Column(JSON, nullable=True)  # JSON schema for configuration fields
    auth_schema = Column(JSON, nullable=True)  # JSON schema for auth fields
    is_available = Column(Boolean, default=True, nullable=False)
    is_africa_first = Column(Boolean, default=False, nullable=False)
    region = Column(String(50), nullable=True)  # africa, global
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
