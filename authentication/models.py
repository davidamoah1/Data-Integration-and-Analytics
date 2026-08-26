"""SQLAlchemy ORM models for the Authentication domain.

Tables: users, roles, permissions, role_permissions, user_roles,
sessions, password_resets, api_tokens, login_history, activity_logs,
password_history.
"""

from sqlalchemy import (
    JSON,
    TIMESTAMP,
    BigInteger,
    Column,
    Integer,
    String,
    Text,
    func,
)

from shared.database import Base, BigInt


class User(Base):
    __tablename__ = "users"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    avatar_url = Column(String(500), nullable=True)
    phone = Column(String(50), nullable=True)
    organization_id = Column(BigInteger, nullable=True, index=True)
    department_id = Column(BigInteger, nullable=True, index=True)
    position = Column(String(200), nullable=True)
    language = Column(String(10), nullable=True, default="en")
    timezone = Column(String(50), nullable=True, default="UTC")
    is_active = Column(Integer, nullable=False, default=1)
    is_deleted = Column(Integer, nullable=False, default=0)
    deleted_at = Column(TIMESTAMP, nullable=True)
    last_login_at = Column(TIMESTAMP, nullable=True)
    email_verified_at = Column(TIMESTAMP, nullable=True)
    failed_login_count = Column(Integer, nullable=False, default=0)
    locked_until = Column(TIMESTAMP, nullable=True)
    onboarding_completed = Column(Integer, nullable=False, default=0)
    onboarding_data = Column(JSON, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)


class Role(Base):
    __tablename__ = "roles"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)
    display_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    level = Column(
        String(20), nullable=False, default="organization"
    )  # platform, organization, department, personal
    is_system = Column(Integer, nullable=False, default=0)
    is_assignable = Column(Integer, nullable=False, default=1)
    is_deleted = Column(Integer, nullable=False, default=0)
    deleted_at = Column(TIMESTAMP, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)


class Permission(Base):
    __tablename__ = "permissions"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    display_name = Column(String(200), nullable=False)
    module = Column(String(50), nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)


class RolePermission(Base):
    __tablename__ = "role_permissions"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    role_id = Column(BigInteger, nullable=False, index=True)
    permission_id = Column(BigInteger, nullable=False, index=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)


class UserRole(Base):
    __tablename__ = "user_roles"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    role_id = Column(BigInteger, nullable=False, index=True)
    scope_type = Column(String(20), nullable=True)  # platform, organization, department, resource
    scope_id = Column(BigInteger, nullable=True)  # org_id, dept_id, or resource_id
    assigned_by = Column(BigInteger, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)


class Session(Base):
    __tablename__ = "sessions"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    refresh_token = Column(String(500), unique=True, nullable=False)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    device = Column(String(200), nullable=True)
    expires_at = Column(TIMESTAMP, nullable=False)
    revoked_at = Column(TIMESTAMP, nullable=True)
    is_active = Column(Integer, nullable=False, default=1)
    last_activity_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)


class PasswordReset(Base):
    __tablename__ = "password_resets"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    token = Column(String(255), unique=True, nullable=False)
    expires_at = Column(TIMESTAMP, nullable=False)
    used_at = Column(TIMESTAMP, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)


class APIToken(Base):
    __tablename__ = "api_tokens"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    token_hash = Column(String(255), unique=True, nullable=False)
    scopes = Column(String(500), nullable=True)
    expires_at = Column(TIMESTAMP, nullable=True)
    last_used_at = Column(TIMESTAMP, nullable=True)
    is_active = Column(Integer, nullable=False, default=1)
    is_deleted = Column(Integer, nullable=False, default=0)
    deleted_at = Column(TIMESTAMP, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)


class LoginHistory(Base):
    __tablename__ = "login_history"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=True, index=True)
    email = Column(String(255), nullable=False)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    success = Column(Integer, nullable=False, default=0)
    failure_reason = Column(String(200), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(50), nullable=True)
    resource_id = Column(BigInteger, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    extra_data = Column(JSON, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)


class PasswordHistory(Base):
    __tablename__ = "password_history"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)


class Resource(Base):
    """Resource model for resource-level access control.

    Tracks individual resources (datasets, dashboards, reports, pipelines)
    and their ownership for fine-grained permission checks.
    """

    __tablename__ = "resources"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    resource_type = Column(
        String(50), nullable=False, index=True
    )  # dataset, dashboard, report, pipeline
    resource_id = Column(BigInteger, nullable=False, index=True)  # FK to the actual resource
    organization_id = Column(BigInteger, nullable=True, index=True)
    department_id = Column(BigInteger, nullable=True, index=True)
    owner_id = Column(BigInteger, nullable=True, index=True)  # user who owns the resource
    is_public = Column(Integer, nullable=False, default=0)  # 1 = visible to all org members
    access_level = Column(
        String(20), nullable=False, default="private"
    )  # private, department, organization, public
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)
