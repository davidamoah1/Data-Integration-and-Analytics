"""add file_records table for Phase 12 file storage architecture

Creates the file_records table for storing file metadata separately
from file content. File content is stored in object storage (R2/S3/Supabase)
and only metadata is persisted in the database.

Revision ID: 0014_file_storage
Revises: 0013_background_jobs
Create Date: 2026-08-01
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0014_file_storage"
down_revision: str | None = "0013_background_jobs"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "file_records",
        sa.Column(
            "id",
            sa.BigInteger().with_variant(sa.Integer, "sqlite"),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column("file_id", sa.String(64), nullable=False, unique=True, index=True),
        sa.Column("organization_id", sa.BigInteger(), nullable=False, index=True),
        sa.Column("filename", sa.String(500), nullable=False),
        sa.Column("storage_backend", sa.String(32), nullable=False, server_default="local"),
        sa.Column("storage_bucket", sa.String(255), nullable=True),
        sa.Column("storage_key", sa.String(1000), nullable=False),
        sa.Column("storage_url", sa.String(2000), nullable=True),
        sa.Column("mime_type", sa.String(100), nullable=True),
        sa.Column("file_size", sa.Integer(), nullable=True),
        sa.Column("checksum", sa.String(64), nullable=True),
        sa.Column("file_metadata", sa.Text(), nullable=True),
        sa.Column("uploaded_by", sa.BigInteger(), nullable=True),
        sa.Column("is_public", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("accessed_at", sa.DateTime(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("file_records")
