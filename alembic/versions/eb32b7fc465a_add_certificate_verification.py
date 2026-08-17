"""add_certificate_verification

Revision ID: eb32b7fc465a
Revises: 0018_dataset_workflow_runs
Create Date: 2026-08-17 16:26:06.914301

Adds certificate verification support:
  - certificate_verifications table (verification attempt records)
  - capture_documents.verification_status column
  - capture_documents.verification_method column
  - capture_documents.verified_at column
  - capture_documents.verified_by column
  - index on capture_documents.verification_status
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

revision: str = 'eb32b7fc465a'
down_revision: Union[str, None] = '0018_dataset_workflow_runs'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create certificate_verifications table
    op.create_table(
        'certificate_verifications',
        sa.Column('id', sa.BigInteger().with_variant(sa.Integer(), 'sqlite'), autoincrement=True, nullable=False),
        sa.Column('organization_id', sa.BigInteger().with_variant(sa.Integer(), 'sqlite'), nullable=False),
        sa.Column('document_id', sa.BigInteger().with_variant(sa.Integer(), 'sqlite'), nullable=False),
        sa.Column('method', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False),
        sa.Column('verified_by', sa.BigInteger().with_variant(sa.Integer(), 'sqlite'), nullable=True),
        sa.Column('verification_source', sa.String(length=255), nullable=True),
        sa.Column('reference_number', sa.String(length=255), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('verified_fields', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_certificate_verifications_document_id'),
        'certificate_verifications',
        ['document_id'],
        unique=False,
    )
    op.create_index(
        op.f('ix_certificate_verifications_organization_id'),
        'certificate_verifications',
        ['organization_id'],
        unique=False,
    )

    # 2. Add verification columns to capture_documents
    op.add_column(
        'capture_documents',
        sa.Column('verification_status', sa.String(length=30), server_default='not_verified', nullable=False),
    )
    op.add_column(
        'capture_documents',
        sa.Column('verification_method', sa.String(length=100), nullable=True),
    )
    op.add_column(
        'capture_documents',
        sa.Column('verified_at', sa.TIMESTAMP(), nullable=True),
    )
    op.add_column(
        'capture_documents',
        sa.Column('verified_by', sa.BigInteger().with_variant(sa.Integer(), 'sqlite'), nullable=True),
    )
    op.create_index(
        op.f('ix_capture_documents_verification_status'),
        'capture_documents',
        ['verification_status'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_capture_documents_verification_status'), table_name='capture_documents')
    op.drop_column('capture_documents', 'verified_by')
    op.drop_column('capture_documents', 'verified_at')
    op.drop_column('capture_documents', 'verification_method')
    op.drop_column('capture_documents', 'verification_status')
    op.drop_index(op.f('ix_certificate_verifications_organization_id'), table_name='certificate_verifications')
    op.drop_index(op.f('ix_certificate_verifications_document_id'), table_name='certificate_verifications')
    op.drop_table('certificate_verifications')
