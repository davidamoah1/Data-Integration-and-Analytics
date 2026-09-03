"""add etl_packages and etl_package_files tables for ZIP package ETL ingestion

Creates two new tables:
  - etl_packages: Tracks ZIP packages uploaded for bulk ETL processing
  - etl_package_files: Tracks individual files discovered inside each package

Revision ID: d7e8f9a0b1c2
Revises: c5d6e7f8a9b0
Create Date: 2026-09-15 10:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "d7e8f9a0b1c2"
down_revision: str | None = "c5d6e7f8a9b0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "etl_packages",
        sa.Column(
            "id",
            sa.BigInteger().with_variant(sa.Integer, "sqlite"),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column(
            "organization_id",
            sa.BigInteger().with_variant(sa.Integer, "sqlite"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "uploaded_by",
            sa.BigInteger().with_variant(sa.Integer, "sqlite"),
            nullable=True,
            index=True,
        ),
        sa.Column("filename", sa.String(500), nullable=False),
        sa.Column("storage_key", sa.String(1000), nullable=False),
        sa.Column("storage_backend", sa.String(50), nullable=False, server_default="local"),
        sa.Column("checksum", sa.String(64), nullable=False, index=True),
        sa.Column("file_size_bytes", sa.BigInteger().with_variant(sa.Integer, "sqlite"), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="uploaded", index=True),
        sa.Column("current_stage", sa.String(50), nullable=True),
        sa.Column("total_files", sa.Integer, nullable=False, server_default="0"),
        sa.Column("discovered_files", sa.Integer, nullable=False, server_default="0"),
        sa.Column("queued_files", sa.Integer, nullable=False, server_default="0"),
        sa.Column("processing_files", sa.Integer, nullable=False, server_default="0"),
        sa.Column("completed_files", sa.Integer, nullable=False, server_default="0"),
        sa.Column("failed_files", sa.Integer, nullable=False, server_default="0"),
        sa.Column("skipped_files", sa.Integer, nullable=False, server_default="0"),
        sa.Column("duplicate_files", sa.Integer, nullable=False, server_default="0"),
        sa.Column("unsupported_files", sa.Integer, nullable=False, server_default="0"),
        sa.Column(
            "total_rows_extracted",
            sa.BigInteger().with_variant(sa.Integer, "sqlite"),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "total_rows_loaded",
            sa.BigInteger().with_variant(sa.Integer, "sqlite"),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "total_rows_rejected",
            sa.BigInteger().with_variant(sa.Integer, "sqlite"),
            nullable=False,
            server_default="0",
        ),
        sa.Column("overall_quality_score", sa.Integer, nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("error_report_path", sa.String(1000), nullable=True),
        sa.Column(
            "job_id",
            sa.BigInteger().with_variant(sa.Integer, "sqlite"),
            nullable=True,
            index=True,
        ),
        sa.Column("started_at", sa.TIMESTAMP, nullable=True),
        sa.Column("completed_at", sa.TIMESTAMP, nullable=True),
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
    op.create_index(
        "ix_etl_packages_org_status",
        "etl_packages",
        ["organization_id", "status"],
    )

    op.create_table(
        "etl_package_files",
        sa.Column(
            "id",
            sa.BigInteger().with_variant(sa.Integer, "sqlite"),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column(
            "package_id",
            sa.BigInteger().with_variant(sa.Integer, "sqlite"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "organization_id",
            sa.BigInteger().with_variant(sa.Integer, "sqlite"),
            nullable=False,
            index=True,
        ),
        sa.Column("original_path", sa.String(1000), nullable=False),
        sa.Column("sanitized_filename", sa.String(500), nullable=False),
        sa.Column("file_extension", sa.String(20), nullable=True),
        sa.Column("mime_type", sa.String(100), nullable=True),
        sa.Column(
            "file_size_bytes",
            sa.BigInteger().with_variant(sa.Integer, "sqlite"),
            nullable=True,
        ),
        sa.Column("checksum", sa.String(64), nullable=True, index=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="discovered", index=True),
        sa.Column("stage", sa.String(50), nullable=True),
        sa.Column("row_count", sa.Integer, nullable=True),
        sa.Column("column_count", sa.Integer, nullable=True),
        sa.Column("quality_score", sa.Integer, nullable=True),
        sa.Column("profile_data", sa.JSON, nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("error_stage", sa.String(50), nullable=True),
        sa.Column(
            "duplicate_of_id",
            sa.BigInteger().with_variant(sa.Integer, "sqlite"),
            nullable=True,
        ),
        sa.Column("target_table", sa.String(200), nullable=True),
        sa.Column("rows_loaded", sa.Integer, nullable=True),
        sa.Column("retry_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("last_retry_at", sa.TIMESTAMP, nullable=True),
        sa.Column(
            "job_id",
            sa.BigInteger().with_variant(sa.Integer, "sqlite"),
            nullable=True,
            index=True,
        ),
        sa.Column(
            "discovered_at",
            sa.TIMESTAMP,
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("processing_started_at", sa.TIMESTAMP, nullable=True),
        sa.Column("completed_at", sa.TIMESTAMP, nullable=True),
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
    op.create_index(
        "ix_etl_pkg_files_pkg_status",
        "etl_package_files",
        ["package_id", "status"],
    )
    op.create_index(
        "ix_etl_pkg_files_org_ext",
        "etl_package_files",
        ["organization_id", "file_extension"],
    )


def downgrade() -> None:
    op.drop_index("ix_etl_pkg_files_org_ext", table_name="etl_package_files")
    op.drop_index("ix_etl_pkg_files_pkg_status", table_name="etl_package_files")
    op.drop_table("etl_package_files")
    op.drop_index("ix_etl_packages_org_status", table_name="etl_packages")
    op.drop_table("etl_packages")
