"""add composite indexes and analytics tables

Redundant migration — all tables and indexes were already created by
revision 3ab0de986206. Kept as a no-op placeholder to preserve the
migration chain integrity (0006 depends on this revision).

Revision ID: 0005_composite_indexes_analytics
Revises: 3ab0de986206
Create Date: 2026-07-17
"""

from collections.abc import Sequence

revision: str = "0005_composite_indexes_analytics"
down_revision: str | None = "3ab0de986206"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
