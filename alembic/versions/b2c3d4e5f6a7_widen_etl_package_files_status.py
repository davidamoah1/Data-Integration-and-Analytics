"""widen etl_package_files status column for document statuses

Revision ID: b2c3d4e5f6a7
Revises: e3f4a5b6c7d8
Create Date: 2026-09-03 18:30:00.000000

Widens the `status` column on `etl_package_files` from VARCHAR(20) to
VARCHAR(40) to accommodate new document processing statuses such as
'document_extraction_pending' (28 chars) and 'certificate_detected' (21 chars).
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "b2c3d4e5f6a7"
down_revision: str | None = "e3f4a5b6c7d8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "etl_package_files",
        "status",
        existing_type=sa.String(length=20),
        type_=sa.String(length=40),
        existing_nullable=False,
        existing_server_default="discovered",
    )


def downgrade() -> None:
    op.alter_column(
        "etl_package_files",
        "status",
        existing_type=sa.String(length=40),
        type_=sa.String(length=20),
        existing_nullable=False,
        existing_server_default="discovered",
    )
