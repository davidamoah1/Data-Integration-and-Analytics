"""add_file_checksum_to_capture_documents

Revision ID: f1a2b3c4d5e6
Revises: eb32b7fc465a
Create Date: 2026-08-21 11:00:00.000000

Adds file_checksum column to capture_documents for checksum-based
duplicate detection. The column stores a SHA-256 hash of the uploaded
file content, enabling fast exact-duplicate detection within an
organization.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "f1a2b3c4d5e6"
down_revision: str | None = "eb32b7fc465a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "capture_documents",
        sa.Column("file_checksum", sa.String(length=64), nullable=True),
    )
    op.create_index(
        op.f("ix_capture_documents_file_checksum"),
        "capture_documents",
        ["file_checksum"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_capture_documents_file_checksum"), table_name="capture_documents")
    op.drop_column("capture_documents", "file_checksum")
