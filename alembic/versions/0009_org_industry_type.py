"""add industry and organization_type columns to organizations table

These columns support adaptive UI navigation based on the user's
organization industry and type.

Revision ID: 0009_org_industry_type
Revises: 0008_missing_domain_tables
Create Date: 2026-07-31
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0009_org_industry_type"
down_revision: str | None = "0008_missing_domain_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("organizations", sa.Column("industry", sa.String(100), nullable=True))
    op.add_column("organizations", sa.Column("organization_type", sa.String(100), nullable=True))


def downgrade() -> None:
    op.drop_column("organizations", "organization_type")
    op.drop_column("organizations", "industry")
