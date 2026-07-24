"""add V3.1 audit and security log indexes

Revision ID: 0007_v31_audit_indexes
Revises: 0006_platform_tables
Create Date: 2026-07-18
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0007_v31_audit_indexes"
down_revision: str | None = "0006_platform_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add tenant column to security_logs for multi-tenant filtering.
    with op.batch_alter_table("security_logs", schema=None) as batch_op:
        batch_op.add_column(sa.Column("organization_id", sa.BigInteger(), nullable=True))
        batch_op.create_index("ix_security_logs_organization_id", ["organization_id"], unique=False)
        batch_op.create_index("idx_security_org_created", ["organization_id", "created_at"], unique=False)

    with op.batch_alter_table("audit_logs", schema=None) as batch_op:
        batch_op.create_index("ix_audit_logs_organization_id", ["organization_id"], unique=False)
        batch_op.create_index("idx_audit_org_created", ["organization_id", "created_at"], unique=False)

    with op.batch_alter_table("system_logs", schema=None) as batch_op:
        batch_op.create_index("idx_system_log_created", ["created_at"], unique=False)

    with op.batch_alter_table("user_activity", schema=None) as batch_op:
        batch_op.create_index("idx_activity_user_created", ["user_id", "created_at"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("user_activity", schema=None) as batch_op:
        batch_op.drop_index("idx_activity_user_created")

    with op.batch_alter_table("security_logs", schema=None) as batch_op:
        batch_op.drop_index("idx_security_org_created")
        batch_op.drop_index("ix_security_logs_organization_id")
        batch_op.drop_column("organization_id")

    with op.batch_alter_table("system_logs", schema=None) as batch_op:
        batch_op.drop_index("idx_system_log_created")

    with op.batch_alter_table("audit_logs", schema=None) as batch_op:
        batch_op.drop_index("idx_audit_org_created")
        batch_op.drop_index("ix_audit_logs_organization_id")
