"""add report engine tables for Phase 8 reporting & presentation engine

Creates tables for structured report compositions with sections, KPIs,
charts, tables, insights, and recommendations.

Revision ID: 0012_report_engine
Revises: 0011_onboarding_tracking
Create Date: 2026-07-31
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0012_report_engine"
down_revision: str | None = "0011_onboarding_tracking"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "report_compositions",
        sa.Column(
            "id",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column("report_id", sa.String(100), nullable=False, unique=True, index=True),
        sa.Column("organization_id", sa.BigInteger, nullable=True, index=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("subtitle", sa.String(500), nullable=True),
        sa.Column("organization_name", sa.String(255), nullable=True),
        sa.Column("author_name", sa.String(255), nullable=True),
        sa.Column("template", sa.String(50), nullable=False, default="executive"),
        sa.Column("industry", sa.String(100), nullable=True),
        sa.Column("dataset_id", sa.BigInteger, nullable=True),
        sa.Column("analysis_id", sa.BigInteger, nullable=True),
        sa.Column("sections", sa.JSON, nullable=True),
        sa.Column("executive_summary", sa.Text, nullable=True),
        sa.Column("tags", sa.JSON, nullable=True),
        sa.Column("status", sa.String(20), nullable=False, default="draft"),
        sa.Column("created_by", sa.BigInteger, nullable=True),
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
        "report_exports",
        sa.Column(
            "id",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column("report_id", sa.String(100), nullable=False, index=True),
        sa.Column("organization_id", sa.BigInteger, nullable=True, index=True),
        sa.Column("format", sa.String(20), nullable=False),
        sa.Column("file_size", sa.Integer, nullable=True),
        sa.Column("downloaded_by", sa.BigInteger, nullable=True),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("report_exports")
    op.drop_table("report_compositions")
