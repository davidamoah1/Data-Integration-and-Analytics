"""add missing domain tables â€” notifications, scheduled_reports, subscriptions, feature_flags

These tables are defined in ORM models but were not included in earlier
migrations. This migration creates them for both SQLite and MySQL.

Revision ID: 0008_missing_domain_tables
Revises: 0007_v31_audit_indexes
Create Date: 2026-07-19
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0008_missing_domain_tables"
down_revision: str | None = "0007_v31_audit_indexes"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- Notifications ---
    op.create_table(
        "notifications",
        sa.Column(
            "id",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column("user_id", sa.BigInteger(), nullable=True),
        sa.Column("organization_id", sa.BigInteger(), nullable=True),
        sa.Column("channel", sa.String(20), nullable=False),
        sa.Column("subject", sa.String(255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("read", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(), server_default=sa.func.now(), nullable=False),
        sa.Column("sent_at", sa.TIMESTAMP(), nullable=True),
    )
    with op.batch_alter_table("notifications", schema=None) as batch_op:
        batch_op.create_index("ix_notifications_user_id", ["user_id"])
        batch_op.create_index("ix_notifications_organization_id", ["organization_id"])

    # --- Scheduled Reports ---
    op.create_table(
        "scheduled_reports",
        sa.Column(
            "id",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("report_type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(500), nullable=True),
        sa.Column("cron", sa.String(100), nullable=False, server_default="0 8 * * *"),
        sa.Column("parameters", sa.JSON(), nullable=True),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("organization_id", sa.BigInteger(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("last_run_at", sa.TIMESTAMP(), nullable=True),
        sa.Column("next_run_at", sa.TIMESTAMP(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(), server_default=sa.func.now(), nullable=False),
    )
    with op.batch_alter_table("scheduled_reports", schema=None) as batch_op:
        batch_op.create_index("ix_scheduled_reports_user_id", ["user_id"])
        batch_op.create_index("ix_scheduled_reports_organization_id", ["organization_id"])

    # --- Subscriptions ---
    op.create_table(
        "subscriptions",
        sa.Column(
            "id",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column("organization_id", sa.BigInteger(), nullable=False, unique=True),
        sa.Column("plan", sa.String(50), nullable=False, server_default="free_trial"),
        sa.Column("status", sa.String(20), nullable=False, server_default="trialing"),
        sa.Column("trial_started_at", sa.TIMESTAMP(), nullable=True),
        sa.Column("trial_ends_at", sa.TIMESTAMP(), nullable=True),
        sa.Column("subscription_started_at", sa.TIMESTAMP(), nullable=True),
        sa.Column("subscription_ends_at", sa.TIMESTAMP(), nullable=True),
        sa.Column("canceled_at", sa.TIMESTAMP(), nullable=True),
        sa.Column("max_users", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("max_dashboards", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("max_pipelines", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("max_ai_queries_per_month", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("max_upload_mb", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("features", sa.JSON(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(), server_default=sa.func.now(), nullable=False),
    )
    with op.batch_alter_table("subscriptions", schema=None) as batch_op:
        batch_op.create_index("ix_subscriptions_organization_id", ["organization_id"], unique=True)

    # --- Feature Flags ---
    op.create_table(
        "feature_flags",
        sa.Column(
            "id",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column("organization_id", sa.BigInteger(), nullable=False),
        sa.Column("feature_key", sa.String(100), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.TIMESTAMP(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(), server_default=sa.func.now(), nullable=False),
    )
    with op.batch_alter_table("feature_flags", schema=None) as batch_op:
        batch_op.create_index("ix_feature_flags_organization_id", ["organization_id"])
        batch_op.create_index("ix_feature_flags_feature_key", ["feature_key"])


def downgrade() -> None:
    op.drop_table("feature_flags")
    op.drop_table("subscriptions")
    op.drop_table("scheduled_reports")
    op.drop_table("notifications")
