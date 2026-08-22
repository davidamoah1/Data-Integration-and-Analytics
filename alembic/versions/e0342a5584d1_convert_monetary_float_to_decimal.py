"""convert_monetary_float_to_decimal

Revision ID: e0342a5584d1
Revises: eb32b7fc465a
Create Date: 2026-08-18 00:49:32.562302

Converts monetary columns from FLOAT to DECIMAL(18,2) for exact
arithmetic precision. FLOAT is unsuitable for financial amounts
because it introduces rounding errors. DECIMAL(18,2) stores up to
16 digits before the decimal point and 2 after, sufficient for
currency values up to 999,999,999,999,999.99.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "e0342a5584d1"
down_revision: str | None = "eb32b7fc465a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("saas_subscription_plans", schema=None) as batch_op:
        batch_op.alter_column(
            "price_monthly",
            existing_type=sa.FLOAT(),
            type_=sa.Numeric(precision=18, scale=2),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "price_yearly",
            existing_type=sa.FLOAT(),
            type_=sa.Numeric(precision=18, scale=2),
            existing_nullable=False,
        )

    with op.batch_alter_table("sales", schema=None) as batch_op:
        batch_op.alter_column(
            "sales",
            existing_type=sa.FLOAT(),
            type_=sa.Numeric(precision=18, scale=2),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "discount",
            existing_type=sa.FLOAT(),
            type_=sa.Numeric(precision=18, scale=2),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "profit",
            existing_type=sa.FLOAT(),
            type_=sa.Numeric(precision=18, scale=2),
            existing_nullable=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("sales", schema=None) as batch_op:
        batch_op.alter_column(
            "profit",
            existing_type=sa.Numeric(precision=18, scale=2),
            type_=sa.FLOAT(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "discount",
            existing_type=sa.Numeric(precision=18, scale=2),
            type_=sa.FLOAT(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "sales",
            existing_type=sa.Numeric(precision=18, scale=2),
            type_=sa.FLOAT(),
            existing_nullable=False,
        )

    with op.batch_alter_table("saas_subscription_plans", schema=None) as batch_op:
        batch_op.alter_column(
            "price_yearly",
            existing_type=sa.Numeric(precision=18, scale=2),
            type_=sa.FLOAT(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "price_monthly",
            existing_type=sa.Numeric(precision=18, scale=2),
            type_=sa.FLOAT(),
            existing_nullable=False,
        )
