"""Add last_heartbeat_at column to background_jobs for worker heartbeat tracking.

Changes:
  1. background_jobs.last_heartbeat_at — DATETIME, nullable.
     Updated periodically by the worker while a job is running. Used by the
     stale-job watchdog to detect crashed workers and mark orphaned jobs as
     failed instead of leaving them stuck in "running" or "pending" forever.

Revision ID: c5d6e7f8a9b0
Revises: b3c4d5e6f7a8
Create Date: 2026-09-01 12:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "c5d6e7f8a9b0"
down_revision: str | None = "b3c4d5e6f7a8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "background_jobs",
        sa.Column("last_heartbeat_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("background_jobs", "last_heartbeat_at")
