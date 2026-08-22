"""merge heads e0342a5584d1 and f1a2b3c4d5e6

Revision ID: 04fa5fa19727
Revises: e0342a5584d1, f1a2b3c4d5e6
Create Date: 2026-08-22 12:28:11.014708
"""
from collections.abc import Sequence

revision: str = '04fa5fa19727'
down_revision: str | None = ('e0342a5584d1', 'f1a2b3c4d5e6')
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
