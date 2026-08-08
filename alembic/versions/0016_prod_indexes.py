"""Phase 15 — Production database indexes

Adds comprehensive indexes across all major tables for production query
performance. Uses conditional creation to handle environments where some
tables/columns may not exist (e.g., dev SQLite vs production MySQL).

Revision ID: 0016_prod_indexes
Revises: 0015_audit_enhancements
Create Date: 2026-08-01
"""

import contextlib
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0016_prod_indexes"
down_revision: str | None = "0015_audit_enhancements"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    ins = sa.inspect(bind)
    return table_name in ins.get_table_names()


def _column_exists(table_name: str, column_name: str) -> bool:
    if not _table_exists(table_name):
        return False
    bind = op.get_bind()
    ins = sa.inspect(bind)
    columns = [c["name"] for c in ins.get_columns(table_name)]
    return column_name in columns


def _safe_create_index(name: str, table: str, columns: list[str]) -> None:
    if not _table_exists(table):
        return
    for col in columns:
        if not _column_exists(table, col):
            return
    op.create_index(name, table, columns, if_not_exists=True)


def upgrade() -> None:
    _safe_create_index("idx_users_org_active", "users", ["organization_id", "is_deleted"])
    _safe_create_index("idx_users_email", "users", ["email"])
    _safe_create_index("idx_users_status", "users", ["is_active", "is_deleted"])
    _safe_create_index("idx_user_roles_user", "user_roles", ["user_id"])
    _safe_create_index("idx_user_roles_role", "user_roles", ["role_id"])
    _safe_create_index("idx_role_permissions_role", "role_permissions", ["role_id"])
    _safe_create_index("idx_role_permissions_perm", "role_permissions", ["permission_id"])
    _safe_create_index("idx_activity_user_date", "activity_logs", ["user_id", "created_at"])
    _safe_create_index("idx_activity_action", "activity_logs", ["action"])
    _safe_create_index("idx_org_slug", "organizations", ["slug"])
    _safe_create_index("idx_org_status", "organizations", ["is_active"])
    _safe_create_index("idx_invitations_org_status", "invitations", ["organization_id", "status"])
    _safe_create_index("idx_invitations_email", "invitations", ["email"])
    _safe_create_index("idx_invitations_token", "invitations", ["token"])
    _safe_create_index("idx_workspaces_org", "workspaces", ["organization_id"])
    _safe_create_index("idx_audit_org_date", "audit_logs", ["organization_id", "created_at"])
    _safe_create_index("idx_audit_user", "audit_logs", ["user_id"])
    _safe_create_index("idx_audit_action", "audit_logs", ["action"])
    _safe_create_index("idx_audit_created", "audit_logs", ["created_at"])
    _safe_create_index("idx_security_org_date", "security_logs", ["organization_id", "created_at"])
    _safe_create_index("idx_security_severity", "security_logs", ["severity"])
    _safe_create_index("idx_security_event_type", "security_logs", ["event_type"])
    _safe_create_index("idx_etl_jobs_status", "etl_jobs", ["status"])
    _safe_create_index("idx_etl_jobs_org", "etl_jobs", ["organization_id"])
    _safe_create_index("idx_etl_pipelines_org", "etl_pipelines", ["organization_id"])
    _safe_create_index("idx_etl_schedules_next_run", "etl_schedules", ["next_run_at"])
    _safe_create_index("idx_etl_transformations_job", "etl_transformations", ["job_id"])
    _safe_create_index("idx_etl_quality_job", "etl_quality_reports", ["job_id"])
    _safe_create_index("idx_etl_profiles_job", "etl_data_profiles", ["job_id"])
    _safe_create_index("idx_sales_date", "sales", ["order_date"])
    _safe_create_index("idx_sales_region", "sales", ["region"])
    _safe_create_index("idx_sales_category", "sales", ["category"])
    _safe_create_index("idx_sales_customer", "sales", ["customer_name"])
    _safe_create_index("idx_sales_order_date_region", "sales", ["order_date", "region"])
    _safe_create_index("idx_pipeline_runs_date", "pipeline_runs", ["started_at"])
    _safe_create_index("idx_pipeline_runs_status", "pipeline_runs", ["status"])
    _safe_create_index(
        "idx_capture_docs_org_status", "capture_documents", ["organization_id", "status"]
    )
    _safe_create_index("idx_capture_docs_batch", "capture_documents", ["batch_id"])
    _safe_create_index("idx_capture_batches_org", "capture_batches", ["organization_id"])
    _safe_create_index("idx_capture_batches_status", "capture_batches", ["status"])
    _safe_create_index("idx_ai_conversations_user", "ai_conversations", ["user_id"])
    _safe_create_index("idx_ai_conversations_org", "ai_conversations", ["organization_id"])
    _safe_create_index("idx_ai_messages_conv", "ai_messages", ["conversation_id"])
    _safe_create_index("idx_ai_reports_org", "ai_reports", ["organization_id"])
    _safe_create_index("idx_notifications_user_read", "notifications", ["user_id", "read"])
    _safe_create_index("idx_notifications_org", "notifications", ["organization_id"])
    _safe_create_index("idx_notifications_created", "notifications", ["created_at"])
    _safe_create_index("idx_jobs_status", "background_jobs", ["status"])
    _safe_create_index("idx_jobs_org", "background_jobs", ["organization_id"])
    _safe_create_index("idx_jobs_created", "background_jobs", ["created_at"])
    _safe_create_index("idx_jobs_scheduled", "background_jobs", ["scheduled_at"])
    _safe_create_index("idx_files_org", "file_records", ["organization_id"])
    _safe_create_index("idx_files_owner", "file_records", ["uploaded_by"])
    _safe_create_index("idx_files_created", "file_records", ["created_at"])
    _safe_create_index("idx_subscriptions_org", "subscriptions", ["organization_id"])
    _safe_create_index("idx_subscriptions_status", "subscriptions", ["status"])


def downgrade() -> None:
    indexes = [
        ("idx_subscriptions_status", "subscriptions"),
        ("idx_subscriptions_org", "subscriptions"),
        ("idx_files_created", "file_records"),
        ("idx_files_owner", "file_records"),
        ("idx_files_org", "file_records"),
        ("idx_jobs_scheduled", "background_jobs"),
        ("idx_jobs_created", "background_jobs"),
        ("idx_jobs_org", "background_jobs"),
        ("idx_jobs_status", "background_jobs"),
        ("idx_notifications_created", "notifications"),
        ("idx_notifications_org", "notifications"),
        ("idx_notifications_user_read", "notifications"),
        ("idx_ai_reports_org", "ai_reports"),
        ("idx_ai_messages_conv", "ai_messages"),
        ("idx_ai_conversations_org", "ai_conversations"),
        ("idx_ai_conversations_user", "ai_conversations"),
        ("idx_capture_batches_status", "capture_batches"),
        ("idx_capture_batches_org", "capture_batches"),
        ("idx_capture_docs_batch", "capture_documents"),
        ("idx_capture_docs_org_status", "capture_documents"),
        ("idx_pipeline_runs_status", "pipeline_runs"),
        ("idx_pipeline_runs_date", "pipeline_runs"),
        ("idx_sales_order_date_region", "sales"),
        ("idx_sales_customer", "sales"),
        ("idx_sales_category", "sales"),
        ("idx_sales_region", "sales"),
        ("idx_sales_date", "sales"),
        ("idx_etl_profiles_job", "etl_data_profiles"),
        ("idx_etl_quality_job", "etl_quality_reports"),
        ("idx_etl_transformations_job", "etl_transformations"),
        ("idx_etl_schedules_next_run", "etl_schedules"),
        ("idx_etl_pipelines_org", "etl_pipelines"),
        ("idx_etl_jobs_org", "etl_jobs"),
        ("idx_etl_jobs_status", "etl_jobs"),
        ("idx_security_event_type", "security_logs"),
        ("idx_security_severity", "security_logs"),
        ("idx_security_org_date", "security_logs"),
        ("idx_audit_created", "audit_logs"),
        ("idx_audit_action", "audit_logs"),
        ("idx_audit_user", "audit_logs"),
        ("idx_audit_org_date", "audit_logs"),
        ("idx_workspaces_org", "workspaces"),
        ("idx_invitations_token", "invitations"),
        ("idx_invitations_email", "invitations"),
        ("idx_invitations_org_status", "invitations"),
        ("idx_org_status", "organizations"),
        ("idx_org_slug", "organizations"),
        ("idx_activity_action", "activity_logs"),
        ("idx_activity_user_date", "activity_logs"),
        ("idx_role_permissions_perm", "role_permissions"),
        ("idx_role_permissions_role", "role_permissions"),
        ("idx_user_roles_role", "user_roles"),
        ("idx_user_roles_user", "user_roles"),
        ("idx_users_status", "users"),
        ("idx_users_email", "users"),
        ("idx_users_org_active", "users"),
    ]
    for name, table in indexes:
        if _table_exists(table):
            with contextlib.suppress(Exception):
                op.drop_index(name, table_name=table)
