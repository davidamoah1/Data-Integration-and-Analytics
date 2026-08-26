"""add dashboard widget data source tables for Phase 6 composition engine

Creates tables for composed dashboards and widget data source bindings.

Revision ID: 0010_dashboard_composition
Revises: 0009_org_industry_type
Create Date: 2026-07-31
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0010_dashboard_composition"
down_revision: str | None = "0009_org_industry_type"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "dashboard_compositions",
        sa.Column(
            "id",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column("dashboard_id", sa.String(255), nullable=False, unique=True, index=True),
        sa.Column("organization_id", sa.BigInteger, nullable=True, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("industry", sa.String(100), nullable=False, default="generic", index=True),
        sa.Column("widgets", sa.JSON, nullable=False, default=list),
        sa.Column("layout", sa.JSON, nullable=False, default=dict),
        sa.Column("created_by", sa.BigInteger, nullable=True, index=True),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_table(
        "dashboard_widget_data_sources",
        sa.Column(
            "id",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column("organization_id", sa.BigInteger, nullable=True, index=True),
        sa.Column("dashboard_id", sa.String(255), nullable=False, index=True),
        sa.Column("widget_key", sa.String(255), nullable=False, index=True),
        sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("source_id", sa.String(255), nullable=True),
        sa.Column("query", sa.Text, nullable=True),
        sa.Column("filters", sa.JSON, nullable=False, default=dict),
        sa.Column("aggregation", sa.String(50), nullable=False, default="sum"),
        sa.Column("group_by", sa.String(255), nullable=True),
        sa.Column("time_field", sa.String(255), nullable=True),
        sa.Column("limit", sa.Integer, nullable=True),
        sa.Column("config", sa.JSON, nullable=False, default=dict),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_index(
        "ix_dashboard_widget_data_sources_dashboard_widget",
        "dashboard_widget_data_sources",
        ["dashboard_id", "widget_key"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_dashboard_widget_data_sources_dashboard_widget",
        table_name="dashboard_widget_data_sources",
    )
    op.drop_table("dashboard_widget_data_sources")
    op.drop_table("dashboard_compositions")
