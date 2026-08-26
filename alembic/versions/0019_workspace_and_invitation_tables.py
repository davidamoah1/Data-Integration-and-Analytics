"""Add workspaces and invitations tables.

These tables were defined as ORM models in organizations/workspace_models.py
but were never included in an Alembic migration. On Vercel serverless with
MySQL, create_all() is skipped, so these tables were missing from the
production database, causing signup-v2 to fail with HTTP 500.

Revision ID: a1b2c3d4e5f6
Revises: 04fa5fa19727
Create Date: 2026-08-25 12:50:00.000000
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "04fa5fa19727"
branch_labels = None
depends_on = None


def _table_exists(bind, table_name: str) -> bool:
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    bind = op.get_bind()

    if not _table_exists(bind, "workspaces"):
        op.create_table(
            "workspaces",
            sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
            sa.Column("organization_id", sa.BigInteger, nullable=True, index=True),
            sa.Column("user_id", sa.BigInteger, nullable=True, index=True),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("type", sa.String(30), nullable=False, server_default="organization"),
            sa.Column("is_active", sa.Integer, nullable=False, server_default="1"),
            sa.Column("is_deleted", sa.Integer, nullable=False, server_default="0"),
            sa.Column("deleted_at", sa.TIMESTAMP, nullable=True),
            sa.Column(
                "created_at",
                sa.TIMESTAMP,
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.TIMESTAMP,
                server_default=sa.func.now(),
                nullable=False,
            ),
        )

    if not _table_exists(bind, "invitations"):
        op.create_table(
            "invitations",
            sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
            sa.Column("organization_id", sa.BigInteger, nullable=False, index=True),
            sa.Column("email", sa.String(255), nullable=False, index=True),
            sa.Column("role_id", sa.BigInteger, nullable=True),
            sa.Column("department_id", sa.BigInteger, nullable=True),
            sa.Column("token", sa.String(255), unique=True, nullable=False),
            sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
            sa.Column("expires_at", sa.TIMESTAMP, nullable=False),
            sa.Column("accepted_at", sa.TIMESTAMP, nullable=True),
            sa.Column("accepted_by_user_id", sa.BigInteger, nullable=True),
            sa.Column("created_by", sa.BigInteger, nullable=False),
            sa.Column(
                "created_at",
                sa.TIMESTAMP,
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.TIMESTAMP,
                server_default=sa.func.now(),
                nullable=False,
            ),
        )


def downgrade() -> None:
    op.drop_table("invitations")
    op.drop_table("workspaces")
