"""add dataset_workflow_runs table for durable workflow state (C3)

Persists a snapshot of DatasetWorkflowOrchestrator state (services/
dataset_workflow.py) so workflow status/results survive a process restart
and are visible across worker processes, instead of living only in an
in-process dict.

Revision ID: 0018_dataset_workflow_runs
Revises: ab3669d60d26
Create Date: 2026-08-12
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0018_dataset_workflow_runs"
down_revision: str | None = "ab3669d60d26"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "dataset_workflow_runs",
        sa.Column(
            "id",
            sa.BigInteger().with_variant(sa.Integer, "sqlite"),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column("workflow_id", sa.String(64), nullable=False, unique=True, index=True),
        sa.Column("dataset_name", sa.String(255), nullable=False),
        sa.Column(
            "created_by",
            sa.BigInteger().with_variant(sa.Integer, "sqlite"),
            nullable=True,
            index=True,
        ),
        sa.Column(
            "organization_id",
            sa.BigInteger().with_variant(sa.Integer, "sqlite"),
            nullable=True,
            index=True,
        ),
        sa.Column("current_stage", sa.String(64), nullable=False),
        # JSON columns must not carry a literal server_default on MySQL
        # (BLOB/TEXT/JSON columns can't have a DEFAULT value) — Python-side
        # default=dict on the ORM model supplies the value on insert instead.
        sa.Column("stages", sa.JSON(), nullable=False),
        sa.Column("is_complete", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("has_errors", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("dataset_workflow_runs")
