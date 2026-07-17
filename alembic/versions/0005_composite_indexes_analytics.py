"""add composite indexes and analytics tables

Revision ID: 0005_composite_indexes_analytics
Revises: 3ab0de986206
Create Date: 2026-07-17
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0005_composite_indexes_analytics"
down_revision: str | None = "3ab0de986206"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- Analytics tables ---
    op.create_table(
        "analytics_dashboards",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("organization_id", sa.BigInteger(), nullable=True),
        sa.Column("owner_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("theme", sa.String(50), nullable=False, server_default="default"),
        sa.Column("layout", sa.JSON(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.TIMESTAMP(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(), server_default=sa.func.now(), nullable=False),
    )
    with op.batch_alter_table("analytics_dashboards", schema=None) as batch_op:
        batch_op.create_index("ix_analytics_dashboards_organization_id", ["organization_id"])
        batch_op.create_index("ix_analytics_dashboards_owner_id", ["owner_id"])

    op.create_table(
        "analytics_dashboard_widgets",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("dashboard_id", sa.BigInteger(), nullable=False),
        sa.Column("widget_type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("configuration", sa.JSON(), nullable=False),
        sa.Column("position", sa.JSON(), nullable=False),
        sa.Column("group_name", sa.String(100), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(), server_default=sa.func.now(), nullable=False),
    )
    with op.batch_alter_table("analytics_dashboard_widgets", schema=None) as batch_op:
        batch_op.create_index("ix_analytics_dashboard_widgets_dashboard_id", ["dashboard_id"])

    op.create_table(
        "analytics_dashboard_favorites",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("dashboard_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(), server_default=sa.func.now(), nullable=False),
    )
    with op.batch_alter_table("analytics_dashboard_favorites", schema=None) as batch_op:
        batch_op.create_index("ix_analytics_dashboard_favorites_dashboard_id", ["dashboard_id"])
        batch_op.create_index("ix_analytics_dashboard_favorites_user_id", ["user_id"])

    op.create_table(
        "analytics_kpis",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("organization_id", sa.BigInteger(), nullable=True),
        sa.Column("owner_id", sa.BigInteger(), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("formula", sa.Text(), nullable=False),
        sa.Column("target_value", sa.Float(), nullable=True),
        sa.Column("warning_threshold", sa.Float(), nullable=True),
        sa.Column("critical_threshold", sa.Float(), nullable=True),
        sa.Column("unit", sa.String(50), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.TIMESTAMP(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(), server_default=sa.func.now(), nullable=False),
    )
    with op.batch_alter_table("analytics_kpis", schema=None) as batch_op:
        batch_op.create_index("ix_analytics_kpis_organization_id", ["organization_id"])
        batch_op.create_index("ix_analytics_kpis_owner_id", ["owner_id"])
        batch_op.create_index("ix_analytics_kpis_category", ["category"])

    op.create_table(
        "analytics_kpi_history",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("kpi_id", sa.BigInteger(), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="healthy"),
        sa.Column("recorded_at", sa.TIMESTAMP(), server_default=sa.func.now(), nullable=False),
    )
    with op.batch_alter_table("analytics_kpi_history", schema=None) as batch_op:
        batch_op.create_index("ix_analytics_kpi_history_kpi_id", ["kpi_id"])

    op.create_table(
        "analytics_alerts",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("organization_id", sa.BigInteger(), nullable=True),
        sa.Column("alert_type", sa.String(50), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False, server_default="warning"),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("source_type", sa.String(50), nullable=True),
        sa.Column("source_id", sa.BigInteger(), nullable=True),
        sa.Column("acknowledged_by", sa.BigInteger(), nullable=True),
        sa.Column("acknowledged_at", sa.TIMESTAMP(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(), server_default=sa.func.now(), nullable=False),
    )
    with op.batch_alter_table("analytics_alerts", schema=None) as batch_op:
        batch_op.create_index("ix_analytics_alerts_organization_id", ["organization_id"])
        batch_op.create_index("ix_analytics_alerts_alert_type", ["alert_type"])

    # --- Composite indexes on existing tables ---
    with op.batch_alter_table("ai_conversations", schema=None) as batch_op:
        batch_op.create_index("idx_conv_user_active", ["user_id", "is_active"])

    with op.batch_alter_table("ai_messages", schema=None) as batch_op:
        batch_op.create_index("idx_msg_conv_created", ["conversation_id", "created_at"])

    with op.batch_alter_table("etl_jobs", schema=None) as batch_op:
        batch_op.create_index("idx_job_status_created", ["status", "created_at"])
        batch_op.create_index("idx_job_pipeline_status", ["pipeline_id", "status"])


def downgrade() -> None:
    with op.batch_alter_table("etl_jobs", schema=None) as batch_op:
        batch_op.drop_index("idx_job_pipeline_status")
        batch_op.drop_index("idx_job_status_created")

    with op.batch_alter_table("ai_messages", schema=None) as batch_op:
        batch_op.drop_index("idx_msg_conv_created")

    with op.batch_alter_table("ai_conversations", schema=None) as batch_op:
        batch_op.drop_index("idx_conv_user_active")

    op.drop_table("analytics_alerts")
    op.drop_table("analytics_kpi_history")
    op.drop_table("analytics_kpis")
    op.drop_table("analytics_dashboard_favorites")
    op.drop_table("analytics_dashboard_widgets")
    op.drop_table("analytics_dashboards")
