"""add approved certificate analytics indexes

Revision ID: a1b2c3d4e5f6
Revises: 04fa5fa19727
Create Date: 2026-08-23 10:00:00.000000

Adds composite indexes to support approved certificate analytics queries.
All indexes include organization_id as the leading column for tenant isolation.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: str | None = "04fa5fa19727"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Composite index for approved certificate analytics:
    # WHERE organization_id = ? AND status = 'approved' AND document_type IN (...)
    op.create_index(
        "ix_capture_documents_org_status_type",
        "capture_documents",
        ["organization_id", "status", "document_type"],
        unique=False,
    )

    # Index for approved_at sorting (analytics records default sort)
    op.create_index(
        "ix_capture_documents_org_status_approved_at",
        "capture_documents",
        ["organization_id", "status", "approved_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_capture_documents_org_status_approved_at",
        table_name="capture_documents",
    )
    op.drop_index(
        "ix_capture_documents_org_status_type",
        table_name="capture_documents",
    )
