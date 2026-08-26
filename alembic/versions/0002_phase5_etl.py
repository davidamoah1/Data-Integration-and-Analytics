"""Phase 5 â€” ETL Engine tables

Revision ID: 0002_phase5_etl
Revises: 0001_phase4_iam
Create Date: 2026-07-11
"""

import sqlalchemy as sa

from alembic import op

revision = "0002_phase5_etl"
down_revision = "0001_phase4_iam"
branch_labels = None
depends_on = None


def upgrade():
    # etl_pipelines
    op.create_table(
        "etl_pipelines",
        sa.Column(
            "id",
            sa.BigInteger().with_variant(sa.Integer, "sqlite"),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column("name", sa.String(200), nullable=False, index=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("current_version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("created_by", sa.BigInteger, nullable=True),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP, server_default=sa.func.now(), nullable=False),
    )

    # etl_pipeline_versions
    op.create_table(
        "etl_pipeline_versions",
        sa.Column(
            "id",
            sa.BigInteger().with_variant(sa.Integer, "sqlite"),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column("pipeline_id", sa.BigInteger, nullable=False, index=True),
        sa.Column("version_number", sa.Integer, nullable=False),
        sa.Column("step_config", sa.JSON, nullable=False),
        sa.Column("created_by", sa.BigInteger, nullable=True),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.func.now(), nullable=False),
        sa.Column("is_active", sa.Integer, nullable=False, server_default="1"),
    )

    # etl_pipeline_steps
    op.create_table(
        "etl_pipeline_steps",
        sa.Column(
            "id",
            sa.BigInteger().with_variant(sa.Integer, "sqlite"),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column("job_id", sa.BigInteger, nullable=False, index=True),
        sa.Column("step_name", sa.String(100), nullable=False),
        sa.Column("step_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("config", sa.JSON, nullable=True),
        sa.Column("started_at", sa.TIMESTAMP, nullable=True),
        sa.Column("completed_at", sa.TIMESTAMP, nullable=True),
        sa.Column("duration_seconds", sa.Integer, nullable=True),
        sa.Column("retry_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("rows_processed", sa.Integer, nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.func.now(), nullable=False),
    )

    # etl_jobs
    op.create_table(
        "etl_jobs",
        sa.Column(
            "id",
            sa.BigInteger().with_variant(sa.Integer, "sqlite"),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column("pipeline_id", sa.BigInteger, nullable=True, index=True),
        sa.Column("job_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="queued"),
        sa.Column("trigger_type", sa.String(30), nullable=False, server_default="manual"),
        sa.Column("rows_extracted", sa.Integer, nullable=False, server_default="0"),
        sa.Column("rows_transformed", sa.Integer, nullable=False, server_default="0"),
        sa.Column("rows_loaded", sa.Integer, nullable=False, server_default="0"),
        sa.Column("rows_rejected", sa.Integer, nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("extra_data", sa.JSON, nullable=True),
        sa.Column("started_at", sa.TIMESTAMP, nullable=True),
        sa.Column("completed_at", sa.TIMESTAMP, nullable=True),
        sa.Column("duration_seconds", sa.Integer, nullable=True),
        sa.Column("created_by", sa.BigInteger, nullable=True),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.func.now(), nullable=False),
    )

    # etl_import_templates
    op.create_table(
        "etl_import_templates",
        sa.Column(
            "id",
            sa.BigInteger().with_variant(sa.Integer, "sqlite"),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("source_config", sa.JSON, nullable=False),
        sa.Column("column_mapping", sa.JSON, nullable=True),
        sa.Column("transformations", sa.JSON, nullable=True),
        sa.Column("validation_rules", sa.JSON, nullable=True),
        sa.Column("created_by", sa.BigInteger, nullable=True),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP, server_default=sa.func.now(), nullable=False),
    )

    # etl_data_profiles
    op.create_table(
        "etl_data_profiles",
        sa.Column(
            "id",
            sa.BigInteger().with_variant(sa.Integer, "sqlite"),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column("job_id", sa.BigInteger, nullable=True, index=True),
        sa.Column("source_name", sa.String(255), nullable=False),
        sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("row_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("column_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("profile_data", sa.JSON, nullable=False),
        sa.Column("quality_score", sa.Integer, nullable=True),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.func.now(), nullable=False),
    )

    # etl_quality_reports
    op.create_table(
        "etl_quality_reports",
        sa.Column(
            "id",
            sa.BigInteger().with_variant(sa.Integer, "sqlite"),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column("job_id", sa.BigInteger, nullable=True, index=True),
        sa.Column("source_name", sa.String(255), nullable=False),
        sa.Column("overall_score", sa.Integer, nullable=False, server_default="0"),
        sa.Column("checks_passed", sa.Integer, nullable=False, server_default="0"),
        sa.Column("checks_failed", sa.Integer, nullable=False, server_default="0"),
        sa.Column("checks_warning", sa.Integer, nullable=False, server_default="0"),
        sa.Column("report_data", sa.JSON, nullable=False),
        sa.Column("recommendations", sa.JSON, nullable=True),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.func.now(), nullable=False),
    )

    # etl_data_lineage
    op.create_table(
        "etl_data_lineage",
        sa.Column(
            "id",
            sa.BigInteger().with_variant(sa.Integer, "sqlite"),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column("job_id", sa.BigInteger, nullable=True, index=True),
        sa.Column("pipeline_id", sa.BigInteger, nullable=True, index=True),
        sa.Column("source_name", sa.String(255), nullable=False),
        sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("transformation", sa.Text, nullable=True),
        sa.Column("destination_name", sa.String(255), nullable=True),
        sa.Column("destination_type", sa.String(50), nullable=True),
        sa.Column("user_id", sa.BigInteger, nullable=True),
        sa.Column("extra_data", sa.JSON, nullable=True),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.func.now(), nullable=False),
    )

    # etl_schedules
    op.create_table(
        "etl_schedules",
        sa.Column(
            "id",
            sa.BigInteger().with_variant(sa.Integer, "sqlite"),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column("pipeline_id", sa.BigInteger, nullable=False, index=True),
        sa.Column("schedule_type", sa.String(30), nullable=False),
        sa.Column("cron_expr", sa.String(100), nullable=True),
        sa.Column("is_active", sa.Integer, nullable=False, server_default="1"),
        sa.Column("last_run_at", sa.TIMESTAMP, nullable=True),
        sa.Column("next_run_at", sa.TIMESTAMP, nullable=True),
        sa.Column("created_by", sa.BigInteger, nullable=True),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP, server_default=sa.func.now(), nullable=False),
    )

    # etl_transformations
    op.create_table(
        "etl_transformations",
        sa.Column(
            "id",
            sa.BigInteger().with_variant(sa.Integer, "sqlite"),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("transformation_type", sa.String(50), nullable=False),
        sa.Column("config", sa.JSON, nullable=False),
        sa.Column("is_builtin", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_by", sa.BigInteger, nullable=True),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP, server_default=sa.func.now(), nullable=False),
    )


def downgrade():
    op.drop_table("etl_transformations")
    op.drop_table("etl_schedules")
    op.drop_table("etl_data_lineage")
    op.drop_table("etl_quality_reports")
    op.drop_table("etl_data_profiles")
    op.drop_table("etl_import_templates")
    op.drop_table("etl_jobs")
    op.drop_table("etl_pipeline_steps")
    op.drop_table("etl_pipeline_versions")
    op.drop_table("etl_pipelines")
