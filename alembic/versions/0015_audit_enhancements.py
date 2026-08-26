"""add metadata column and indexes to audit_logs for Phase 13

Adds a `metadata` JSON column to the audit_logs table for tracking
extra context (file size, export format, role names, etc.). Also adds
composite indexes for action+resource_type and resource_type+resource_id
to support enterprise-grade audit log querying.

Revision ID: 0015_audit_enhancements
Revises: 0014_file_storage
Create Date: 2026-08-01
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0015_audit_enhancements"
down_revision: str | None = "0014_file_storage"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add metadata column
    op.add_column("audit_logs", sa.Column("metadata", sa.JSON(), nullable=True))

    # Add composite indexes for enterprise querying
    op.create_index("idx_audit_action_resource", "audit_logs", ["action", "resource_type"])
    op.create_index("idx_audit_resource", "audit_logs", ["resource_type", "resource_id"])


def downgrade() -> None:
    op.drop_index("idx_audit_resource", table_name="audit_logs")
    op.drop_index("idx_audit_action_resource", table_name="audit_logs")
    op.drop_column("audit_logs", "metadata")
