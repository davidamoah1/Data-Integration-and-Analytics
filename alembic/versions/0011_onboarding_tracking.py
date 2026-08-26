"""add onboarding tracking table for Phase 7 smart onboarding

Creates a table for tracking role-specific onboarding step completion.

Note: The User model already has onboarding_completed (int) and onboarding_data (JSON)
columns from a previous migration. This migration adds a dedicated table for
structured step tracking and audit trail.

Revision ID: 0011_onboarding_tracking
Revises: 0010_dashboard_composition
Create Date: 2026-07-31
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0011_onboarding_tracking"
down_revision: str | None = "0010_dashboard_composition"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "onboarding_progress",
        sa.Column(
            "id",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column("user_id", sa.BigInteger, nullable=False, index=True),
        sa.Column("organization_id", sa.BigInteger, nullable=True, index=True),
        sa.Column("role", sa.String(100), nullable=False),
        sa.Column("flow_title", sa.String(255), nullable=False),
        sa.Column("total_steps", sa.Integer, nullable=False, default=0),
        sa.Column("completed_steps", sa.JSON, nullable=False, default=list),
        sa.Column("current_step", sa.String(100), nullable=True),
        sa.Column("current_step_index", sa.Integer, nullable=False, default=0),
        sa.Column("percentage", sa.Integer, nullable=False, default=0),
        sa.Column("is_complete", sa.Boolean, nullable=False, default=False),
        sa.Column("is_skipped", sa.Boolean, nullable=False, default=False),
        sa.Column("completed_at", sa.TIMESTAMP, nullable=True),
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
        "ix_onboarding_progress_user_org",
        "onboarding_progress",
        ["user_id", "organization_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_onboarding_progress_user_org", table_name="onboarding_progress")
    op.drop_table("onboarding_progress")
