"""SQLAlchemy ORM models for the Audit domain."""

from sqlalchemy import JSON, TIMESTAMP, BigInteger, Column, Index, Integer, String, Text, func

from shared.database import Base, BigInt


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=True, index=True)
    organization_id = Column(BigInteger, nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(50), nullable=True)
    resource_id = Column(BigInteger, nullable=True)
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    request_id = Column(String(100), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)

    __table_args__ = (Index("idx_audit_org_created", "organization_id", "created_at"),)


class SystemLog(Base):
    __tablename__ = "system_logs"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    log_level = Column(String(20), nullable=False, index=True)
    logger_name = Column(String(200), nullable=True)
    message = Column(Text, nullable=False)
    module = Column(String(200), nullable=True)
    function = Column(String(200), nullable=True)
    line_number = Column(Integer, nullable=True)
    stack_trace = Column(Text, nullable=True)
    extra_data = Column(JSON, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)

    __table_args__ = (Index("idx_system_log_created", "created_at"),)


class SecurityLog(Base):
    __tablename__ = "security_logs"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=True, index=True)
    organization_id = Column(BigInteger, nullable=True, index=True)
    event_type = Column(String(50), nullable=False, index=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    resource = Column(String(200), nullable=True)
    details = Column(JSON, nullable=True)
    severity = Column(String(20), nullable=False, default="info")
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)

    __table_args__ = (Index("idx_security_org_created", "organization_id", "created_at"),)


class UserActivity(Base):
    __tablename__ = "user_activity"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    activity_type = Column(String(50), nullable=False, index=True)
    resource_type = Column(String(50), nullable=True)
    resource_id = Column(BigInteger, nullable=True)
    session_id = Column(String(100), nullable=True)
    ip_address = Column(String(45), nullable=True)
    extra_data = Column(JSON, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)

    __table_args__ = (Index("idx_activity_user_created", "user_id", "created_at"),)
