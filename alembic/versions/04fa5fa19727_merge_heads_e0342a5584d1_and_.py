"""merge heads e0342a5584d1 and f1a2b3c4d5e6

Revision ID: 04fa5fa19727
Revises: e0342a5584d1, f1a2b3c4d5e6
Create Date: 2026-08-22 12:28:11.014708
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '04fa5fa19727'
down_revision: Union[str, None] = ('e0342a5584d1', 'f1a2b3c4d5e6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
