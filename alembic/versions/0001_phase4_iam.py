"""Initial Phase 4 migration — authentication, organization, and audit tables.

Creates all new tables for the Enterprise IAM system:
- Authentication: users, roles, permissions, role_permissions, user_roles,
  sessions, password_resets, api_tokens, login_history, activity_logs,
  password_history
- Organization: organizations, branches, departments, teams
- Audit: audit_logs, system_logs, security_logs, user_activity

Revision ID: 0001_phase4_iam
Revises:
Create Date: 2025-01-15 00:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0001_phase4_iam"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- Authentication domain ---
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("avatar_url", sa.String(500), nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("organization_id", sa.BigInteger, nullable=True, index=True),
        sa.Column("department_id", sa.BigInteger, nullable=True, index=True),
        sa.Column("position", sa.String(200), nullable=True),
        sa.Column("language", sa.String(10), nullable=True, server_default="en"),
        sa.Column("timezone", sa.String(50), nullable=True, server_default="UTC"),
        sa.Column("is_active", sa.Integer, nullable=False, server_default="1"),
        sa.Column("is_deleted", sa.Integer, nullable=False, server_default="0"),
        sa.Column("deleted_at", sa.TIMESTAMP, nullable=True),
        sa.Column("last_login_at", sa.TIMESTAMP, nullable=True),
        sa.Column("email_verified_at", sa.TIMESTAMP, nullable=True),
        sa.Column("failed_login_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("locked_until", sa.TIMESTAMP, nullable=True),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP, server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "roles",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(50), unique=True, nullable=False),
        sa.Column("display_name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("is_system", sa.Integer, nullable=False, server_default="0"),
        sa.Column("is_deleted", sa.Integer, nullable=False, server_default="0"),
        sa.Column("deleted_at", sa.TIMESTAMP, nullable=True),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP, server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "permissions",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(100), unique=True, nullable=False),
        sa.Column("display_name", sa.String(200), nullable=False),
        sa.Column("module", sa.String(50), nullable=False, index=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP, server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "role_permissions",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("role_id", sa.BigInteger, nullable=False, index=True),
        sa.Column("permission_id", sa.BigInteger, nullable=False, index=True),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),
    )

    op.create_table(
        "user_roles",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger, nullable=False, index=True),
        sa.Column("role_id", sa.BigInteger, nullable=False, index=True),
        sa.Column("assigned_by", sa.BigInteger, nullable=True),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "role_id", name="uq_user_role"),
    )

    op.create_table(
        "sessions",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger, nullable=False, index=True),
        sa.Column("refresh_token", sa.String(500), unique=True, nullable=False),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("device", sa.String(200), nullable=True),
        sa.Column("expires_at", sa.TIMESTAMP, nullable=False),
        sa.Column("revoked_at", sa.TIMESTAMP, nullable=True),
        sa.Column("is_active", sa.Integer, nullable=False, server_default="1"),
        sa.Column("last_activity_at", sa.TIMESTAMP, server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP, server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "password_resets",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger, nullable=False, index=True),
        sa.Column("token", sa.String(255), unique=True, nullable=False),
        sa.Column("expires_at", sa.TIMESTAMP, nullable=False),
        sa.Column("used_at", sa.TIMESTAMP, nullable=True),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "api_tokens",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger, nullable=False, index=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("token_hash", sa.String(255), unique=True, nullable=False),
        sa.Column("scopes", sa.String(500), nullable=True),
        sa.Column("expires_at", sa.TIMESTAMP, nullable=True),
        sa.Column("last_used_at", sa.TIMESTAMP, nullable=True),
        sa.Column("is_active", sa.Integer, nullable=False, server_default="1"),
        sa.Column("is_deleted", sa.Integer, nullable=False, server_default="0"),
        sa.Column("deleted_at", sa.TIMESTAMP, nullable=True),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP, server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "login_history",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger, nullable=True, index=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("success", sa.Integer, nullable=False, server_default="0"),
        sa.Column("failure_reason", sa.String(200), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "activity_logs",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger, nullable=True, index=True),
        sa.Column("action", sa.String(100), nullable=False, index=True),
        sa.Column("resource_type", sa.String(50), nullable=True),
        sa.Column("resource_id", sa.BigInteger, nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("extra_data", sa.JSON, nullable=True),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "password_history",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger, nullable=False, index=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.func.now(), nullable=False),
    )

    # --- Organization domain ---
    op.create_table(
        "organizations",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(100), unique=True, nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("logo_url", sa.String(500), nullable=True),
        sa.Column("contact_email", sa.String(255), nullable=True),
        sa.Column("contact_phone", sa.String(50), nullable=True),
        sa.Column("address", sa.Text, nullable=True),
        sa.Column("is_active", sa.Integer, nullable=False, server_default="1"),
        sa.Column("is_deleted", sa.Integer, nullable=False, server_default="0"),
        sa.Column("deleted_at", sa.TIMESTAMP, nullable=True),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP, server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "branches",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("organization_id", sa.BigInteger, nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("code", sa.String(50), nullable=True),
        sa.Column("address", sa.Text, nullable=True),
        sa.Column("contact_email", sa.String(255), nullable=True),
        sa.Column("contact_phone", sa.String(50), nullable=True),
        sa.Column("is_active", sa.Integer, nullable=False, server_default="1"),
        sa.Column("is_deleted", sa.Integer, nullable=False, server_default="0"),
        sa.Column("deleted_at", sa.TIMESTAMP, nullable=True),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP, server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "departments",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("organization_id", sa.BigInteger, nullable=False, index=True),
        sa.Column("branch_id", sa.BigInteger, nullable=True, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("code", sa.String(50), nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("head_user_id", sa.BigInteger, nullable=True),
        sa.Column("parent_id", sa.BigInteger, nullable=True),
        sa.Column("is_active", sa.Integer, nullable=False, server_default="1"),
        sa.Column("is_deleted", sa.Integer, nullable=False, server_default="0"),
        sa.Column("deleted_at", sa.TIMESTAMP, nullable=True),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP, server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "teams",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("department_id", sa.BigInteger, nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("lead_user_id", sa.BigInteger, nullable=True),
        sa.Column("is_active", sa.Integer, nullable=False, server_default="1"),
        sa.Column("is_deleted", sa.Integer, nullable=False, server_default="0"),
        sa.Column("deleted_at", sa.TIMESTAMP, nullable=True),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP, server_default=sa.func.now(), nullable=False),
    )

    # --- Audit domain ---
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger, nullable=True, index=True),
        sa.Column("organization_id", sa.BigInteger, nullable=True),
        sa.Column("action", sa.String(100), nullable=False, index=True),
        sa.Column("resource_type", sa.String(50), nullable=True),
        sa.Column("resource_id", sa.BigInteger, nullable=True),
        sa.Column("old_values", sa.JSON, nullable=True),
        sa.Column("new_values", sa.JSON, nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("request_id", sa.String(100), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "system_logs",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("log_level", sa.String(20), nullable=False, index=True),
        sa.Column("logger_name", sa.String(200), nullable=True),
        sa.Column("message", sa.Text, nullable=False),
        sa.Column("module", sa.String(200), nullable=True),
        sa.Column("function", sa.String(200), nullable=True),
        sa.Column("line_number", sa.Integer, nullable=True),
        sa.Column("stack_trace", sa.Text, nullable=True),
        sa.Column("extra_data", sa.JSON, nullable=True),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "security_logs",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger, nullable=True, index=True),
        sa.Column("event_type", sa.String(50), nullable=False, index=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("resource", sa.String(200), nullable=True),
        sa.Column("details", sa.JSON, nullable=True),
        sa.Column("severity", sa.String(20), nullable=False, server_default="info"),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "user_activity",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger, nullable=False, index=True),
        sa.Column("activity_type", sa.String(50), nullable=False, index=True),
        sa.Column("resource_type", sa.String(50), nullable=True),
        sa.Column("resource_id", sa.BigInteger, nullable=True),
        sa.Column("session_id", sa.String(100), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("extra_data", sa.JSON, nullable=True),
        sa.Column("duration_seconds", sa.Integer, nullable=True),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("user_activity")
    op.drop_table("security_logs")
    op.drop_table("system_logs")
    op.drop_table("audit_logs")
    op.drop_table("teams")
    op.drop_table("departments")
    op.drop_table("branches")
    op.drop_table("organizations")
    op.drop_table("password_history")
    op.drop_table("activity_logs")
    op.drop_table("login_history")
    op.drop_table("api_tokens")
    op.drop_table("password_resets")
    op.drop_table("sessions")
    op.drop_table("user_roles")
    op.drop_table("role_permissions")
    op.drop_table("permissions")
    op.drop_table("roles")
    op.drop_table("users")
