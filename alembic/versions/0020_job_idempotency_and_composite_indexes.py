"""Add job idempotency_key column and composite indexes for certificate queries.

Changes:
  1. background_jobs.idempotency_key — VARCHAR(255), indexed, nullable.
     Used to prevent duplicate job submissions (e.g. processing the same
     document twice if the user double-clicks or the network retries).

  2. Composite indexes on capture_documents for the most common certificate
     search/dashboard query patterns:
       - ix_capture_documents_org_type (organization_id, document_type)
       - ix_capture_documents_org_status (organization_id, status)

     These cover the certificate search route's WHERE clauses which filter
     by organization_id + document_type IN (...) and optionally status, and
     the dashboard route which loads all certificate documents for an org.

Revision ID: b3c4d5e6f7a8
Revises: a1b2c3d4e5f6
Create Date: 2026-08-28 10:00:00.000000
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "b3c4d5e6f7a8"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def _column_exists(bind, table_name: str, column_name: str) -> bool:
    inspector = sa.inspect(bind)
    if table_name not in inspector.get_table_names():
        return False
    columns = [c["name"] for c in inspector.get_columns(table_name)]
    return column_name in columns


def _index_exists(bind, table_name: str, index_name: str) -> bool:
    inspector = sa.inspect(bind)
    if table_name not in inspector.get_table_names():
        return False
    indexes = [idx["name"] for idx in inspector.get_indexes(table_name)]
    return index_name in indexes


def upgrade() -> None:
    bind = op.get_bind()

    # 1. Add idempotency_key column to background_jobs
    if not _column_exists(bind, "background_jobs", "idempotency_key"):
        op.add_column(
            "background_jobs",
            sa.Column("idempotency_key", sa.String(255), nullable=True),
        )
        op.create_index(
            "ix_background_jobs_idempotency_key",
            "background_jobs",
            ["idempotency_key"],
        )

    # 2. Composite indexes for certificate search/dashboard queries
    if not _index_exists(bind, "capture_documents", "ix_capture_documents_org_type"):
        op.create_index(
            "ix_capture_documents_org_type",
            "capture_documents",
            ["organization_id", "document_type"],
        )

    if not _index_exists(bind, "capture_documents", "ix_capture_documents_org_status"):
        op.create_index(
            "ix_capture_documents_org_status",
            "capture_documents",
            ["organization_id", "status"],
        )


def downgrade() -> None:
    bind = op.get_bind()

    if _index_exists(bind, "capture_documents", "ix_capture_documents_org_status"):
        op.drop_index("ix_capture_documents_org_status", table_name="capture_documents")

    if _index_exists(bind, "capture_documents", "ix_capture_documents_org_type"):
        op.drop_index("ix_capture_documents_org_type", table_name="capture_documents")

    if _column_exists(bind, "background_jobs", "idempotency_key"):
        op.drop_index("ix_background_jobs_idempotency_key", table_name="background_jobs")
        op.drop_column("background_jobs", "idempotency_key")
