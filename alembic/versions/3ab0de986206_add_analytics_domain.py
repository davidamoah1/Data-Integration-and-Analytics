"""add analytics domain

Revision ID: 3ab0de986206
Revises: 84a96d4ff144
Create Date: 2026-07-16 00:46:32.918340
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "3ab0de986206"
down_revision: str | None = "84a96d4ff144"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "analytics_dashboards",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("organization_id", sa.BigInteger(), nullable=True, index=True),
        sa.Column("owner_id", sa.BigInteger(), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("theme", sa.String(50), nullable=False, server_default="default"),
        # MySQL does not allow literal DEFAULT values on JSON/TEXT/BLOB
        # columns (raises errno 1101). The ORM model (analytics/models.py)
        # already supplies a Python-side default=list on insert, so no
        # server_default is needed here.
        sa.Column("layout", sa.JSON(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.TIMESTAMP(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "analytics_dashboard_widgets",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("dashboard_id", sa.BigInteger(), nullable=False, index=True),
        sa.Column("widget_type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        # See note above: MySQL forbids literal defaults on JSON columns.
        # ORM defaults (default=dict) cover these at insert time.
        sa.Column("configuration", sa.JSON(), nullable=False),
        sa.Column("position", sa.JSON(), nullable=False),
        sa.Column("group_name", sa.String(100), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "analytics_dashboard_favorites",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("dashboard_id", sa.BigInteger(), nullable=False, index=True),
        sa.Column("user_id", sa.BigInteger(), nullable=False, index=True),
        sa.Column("created_at", sa.TIMESTAMP(), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "analytics_kpis",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("organization_id", sa.BigInteger(), nullable=True, index=True),
        sa.Column("owner_id", sa.BigInteger(), nullable=True, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(100), nullable=True, index=True),
        sa.Column("formula", sa.Text(), nullable=False),
        sa.Column("target_value", sa.Float(), nullable=True),
        sa.Column("warning_threshold", sa.Float(), nullable=True),
        sa.Column("critical_threshold", sa.Float(), nullable=True),
        sa.Column("unit", sa.String(50), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.TIMESTAMP(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "analytics_kpi_history",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("kpi_id", sa.BigInteger(), nullable=False, index=True),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="healthy"),
        sa.Column("recorded_at", sa.TIMESTAMP(), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "analytics_alerts",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("organization_id", sa.BigInteger(), nullable=True, index=True),
        sa.Column("alert_type", sa.String(50), nullable=False, index=True),
        sa.Column("severity", sa.String(20), nullable=False, server_default="warning"),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("source_type", sa.String(50), nullable=True),
        sa.Column("source_id", sa.BigInteger(), nullable=True),
        sa.Column("acknowledged_by", sa.BigInteger(), nullable=True),
        sa.Column("acknowledged_at", sa.TIMESTAMP(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(), server_default=sa.func.now(), nullable=False),
    )
    with op.batch_alter_table("ai_conversations", schema=None) as batch_op:
        batch_op.create_index("idx_conv_user_active", ["user_id", "is_active"])
    with op.batch_alter_table("ai_messages", schema=None) as batch_op:
        batch_op.create_index("idx_msg_conv_created", ["conversation_id", "created_at"])
    with op.batch_alter_table("etl_jobs", schema=None) as batch_op:
        batch_op.create_index("idx_job_status_created", ["status", "created_at"])
        batch_op.create_index("idx_job_pipeline_status", ["pipeline_id", "status"])


def downgrade() -> None:
    op.drop_table("analytics_alerts")
    op.drop_table("analytics_kpi_history")
    op.drop_table("analytics_kpis")
    op.drop_table("analytics_dashboard_favorites")
    op.drop_table("analytics_dashboard_widgets")
    op.drop_table("analytics_dashboards")
    with op.batch_alter_table("ai_conversations", schema=None) as batch_op:
        batch_op.drop_index("idx_conv_user_active")
    with op.batch_alter_table("ai_messages", schema=None) as batch_op:
        batch_op.drop_index("idx_msg_conv_created")
    with op.batch_alter_table("etl_jobs", schema=None) as batch_op:
        batch_op.drop_index("idx_job_status_created")
        batch_op.drop_index("idx_job_pipeline_status")
