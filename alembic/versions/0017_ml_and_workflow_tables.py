"""add ML platform and workflow engine tables

Creates tables for the ML platform (model registry, training runs,
predictions, forecasts, anomaly jobs, drift records) and the workflow
engine (definitions, versions, executions, jobs, lineage, templates).
These models were defined in code but never imported, so their tables
were not created by migrations or Base.metadata.create_all().

Revision ID: 0017_ml_and_workflow_tables
Revises: 0016_prod_indexes
Create Date: 2026-08-09
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0017_ml_and_workflow_tables"
down_revision: str | None = "0016_prod_indexes"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- ML platform tables ---
    op.create_table(
        "ml_models",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("model_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="draft"),
        sa.Column("target_column", sa.String(255), nullable=True),
        sa.Column("feature_columns", sa.JSON, nullable=False),
        sa.Column("algorithm", sa.String(100), nullable=True),
        sa.Column("hyperparameters", sa.JSON, nullable=False),
        sa.Column("metrics", sa.JSON, nullable=False),
        sa.Column("artifact_path", sa.String(500), nullable=True),
        sa.Column("dataset_source", sa.String(500), nullable=True),
        sa.Column(
            "organization_id",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            sa.ForeignKey("organizations.id"),
            nullable=False,
        ),
        sa.Column(
            "created_by",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("parent_model_id", sa.String(64), sa.ForeignKey("ml_models.id"), nullable=True),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column(
            "deployment_status", sa.String(50), nullable=False, server_default="not_deployed"
        ),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_ml_models_organization_id", "ml_models", ["organization_id"])

    op.create_table(
        "ml_training_runs",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column(
            "model_id",
            sa.String(64),
            sa.ForeignKey("ml_models.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("algorithm", sa.String(100), nullable=True),
        sa.Column("hyperparameters", sa.JSON, nullable=False),
        sa.Column("feature_columns", sa.JSON, nullable=False),
        sa.Column("target_column", sa.String(255), nullable=True),
        sa.Column("train_metrics", sa.JSON, nullable=False),
        sa.Column("test_metrics", sa.JSON, nullable=False),
        sa.Column("comparison_metrics", sa.JSON, nullable=False),
        sa.Column("artifact_path", sa.String(500), nullable=True),
        sa.Column("dataset_source", sa.String(500), nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("started_at", sa.DateTime, nullable=True),
        sa.Column("completed_at", sa.DateTime, nullable=True),
        sa.Column(
            "created_by",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column(
            "organization_id",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            sa.ForeignKey("organizations.id"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_ml_training_runs_model_id", "ml_training_runs", ["model_id"])
    op.create_index("ix_ml_training_runs_organization_id", "ml_training_runs", ["organization_id"])

    op.create_table(
        "ml_predictions",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column(
            "model_id",
            sa.String(64),
            sa.ForeignKey("ml_models.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("input_features", sa.JSON, nullable=False),
        sa.Column("prediction", sa.JSON, nullable=False),
        sa.Column("probability", sa.Float, nullable=True),
        sa.Column("confidence_interval", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_ml_predictions_model_id", "ml_predictions", ["model_id"])

    op.create_table(
        "ml_forecasts",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column(
            "model_id",
            sa.String(64),
            sa.ForeignKey("ml_models.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("horizon", sa.Integer, nullable=False),
        sa.Column("frequency", sa.String(20), nullable=False),
        sa.Column("forecast_values", sa.JSON, nullable=False),
        sa.Column("confidence_intervals", sa.JSON, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_ml_forecasts_model_id", "ml_forecasts", ["model_id"])

    op.create_table(
        "ml_anomaly_jobs",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("dataset_source", sa.String(500), nullable=True),
        sa.Column("algorithm", sa.String(100), nullable=False, server_default="isolation_forest"),
        sa.Column("config", sa.JSON, nullable=False),
        sa.Column("latest_result", sa.JSON, nullable=False),
        sa.Column(
            "organization_id",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            sa.ForeignKey("organizations.id"),
            nullable=False,
        ),
        sa.Column(
            "created_by",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_ml_anomaly_jobs_organization_id", "ml_anomaly_jobs", ["organization_id"])

    op.create_table(
        "ml_drift_records",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column(
            "model_id",
            sa.String(64),
            sa.ForeignKey("ml_models.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("drift_type", sa.String(50), nullable=False),
        sa.Column("score", sa.Float, nullable=False),
        sa.Column("threshold", sa.Float, nullable=False, server_default="0.05"),
        sa.Column("details", sa.JSON, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_ml_drift_records_model_id", "ml_drift_records", ["model_id"])

    # --- Workflow engine tables ---
    op.create_table(
        "workflow_definitions",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column(
            "organization_id",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            sa.ForeignKey("organizations.id"),
            nullable=True,
        ),
        sa.Column(
            "created_by",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("is_active", sa.Integer, nullable=False, server_default="1"),
        sa.Column("is_deleted", sa.Integer, nullable=False, server_default="0"),
        sa.Column("published_version_id", sa.BigInteger, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )
    op.create_index(
        "ix_workflow_definitions_organization_id", "workflow_definitions", ["organization_id"]
    )
    op.create_index(
        "ix_workflow_definitions_published_version_id",
        "workflow_definitions",
        ["published_version_id"],
    )

    op.create_table(
        "workflow_versions",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column(
            "workflow_id",
            sa.BigInteger,
            sa.ForeignKey("workflow_definitions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("version_number", sa.Integer, nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("nodes", sa.JSON, nullable=False),
        sa.Column("edges", sa.JSON, nullable=False),
        sa.Column("config", sa.JSON, nullable=False),
        sa.Column(
            "created_by",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.UniqueConstraint("workflow_id", "version_number"),
    )
    op.create_index("ix_workflow_versions_workflow_id", "workflow_versions", ["workflow_id"])

    op.create_table(
        "workflow_executions",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("execution_id", sa.String(64), nullable=False, unique=True),
        sa.Column(
            "workflow_id",
            sa.BigInteger,
            sa.ForeignKey("workflow_definitions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "version_id",
            sa.BigInteger,
            sa.ForeignKey("workflow_versions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "organization_id",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            sa.ForeignKey("organizations.id"),
            nullable=True,
        ),
        sa.Column(
            "triggered_by",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
        sa.Column("trigger_type", sa.String(50), nullable=False, server_default="manual"),
        sa.Column("status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("started_at", sa.DateTime, nullable=True),
        sa.Column("completed_at", sa.DateTime, nullable=True),
        sa.Column("duration_seconds", sa.Integer, nullable=True),
        sa.Column("node_results", sa.JSON, nullable=False),
        sa.Column("context", sa.JSON, nullable=False),
        sa.Column("metrics", sa.JSON, nullable=False),
        sa.Column("errors", sa.JSON, nullable=False),
        sa.Column("warnings", sa.JSON, nullable=False),
        sa.Column("ai_summary", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_workflow_executions_execution_id", "workflow_executions", ["execution_id"])
    op.create_index("ix_workflow_executions_workflow_id", "workflow_executions", ["workflow_id"])
    op.create_index("ix_workflow_executions_version_id", "workflow_executions", ["version_id"])
    op.create_index(
        "ix_workflow_executions_organization_id", "workflow_executions", ["organization_id"]
    )

    op.create_table(
        "workflow_jobs",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column(
            "execution_id",
            sa.String(64),
            sa.ForeignKey("workflow_executions.execution_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("priority", sa.Integer, nullable=False, server_default="0"),
        sa.Column("retry_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("max_retries", sa.Integer, nullable=False, server_default="3"),
        sa.Column("scheduled_at", sa.DateTime, nullable=True),
        sa.Column("started_at", sa.DateTime, nullable=True),
        sa.Column("completed_at", sa.DateTime, nullable=True),
        sa.Column("worker_id", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_workflow_jobs_execution_id", "workflow_jobs", ["execution_id"])

    op.create_table(
        "workflow_lineage",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column(
            "execution_id",
            sa.String(64),
            sa.ForeignKey("workflow_executions.execution_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "organization_id",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            sa.ForeignKey("organizations.id"),
            nullable=True,
        ),
        sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("source_id", sa.String(255), nullable=True),
        sa.Column("target_type", sa.String(50), nullable=False),
        sa.Column("target_id", sa.String(255), nullable=True),
        sa.Column("transformation", sa.String(255), nullable=True),
        sa.Column("meta", sa.JSON, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.UniqueConstraint("execution_id", "source_type", "source_id", "target_type", "target_id"),
    )
    op.create_index("ix_workflow_lineage_execution_id", "workflow_lineage", ["execution_id"])
    op.create_index("ix_workflow_lineage_organization_id", "workflow_lineage", ["organization_id"])

    op.create_table(
        "workflow_templates",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column(
            "created_by",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("nodes", sa.JSON, nullable=False),
        sa.Column("edges", sa.JSON, nullable=False),
        sa.Column("config", sa.JSON, nullable=False),
        sa.Column("is_public", sa.Integer, nullable=False, server_default="0"),
        sa.Column("is_active", sa.Integer, nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )


def downgrade() -> None:
    op.drop_table("workflow_templates")
    op.drop_index("ix_workflow_lineage_organization_id", table_name="workflow_lineage")
    op.drop_index("ix_workflow_lineage_execution_id", table_name="workflow_lineage")
    op.drop_table("workflow_lineage")
    op.drop_index("ix_workflow_jobs_execution_id", table_name="workflow_jobs")
    op.drop_table("workflow_jobs")
    op.drop_index("ix_workflow_executions_organization_id", table_name="workflow_executions")
    op.drop_index("ix_workflow_executions_version_id", table_name="workflow_executions")
    op.drop_index("ix_workflow_executions_workflow_id", table_name="workflow_executions")
    op.drop_index("ix_workflow_executions_execution_id", table_name="workflow_executions")
    op.drop_table("workflow_executions")
    op.drop_index("ix_workflow_versions_workflow_id", table_name="workflow_versions")
    op.drop_table("workflow_versions")
    op.drop_index("ix_workflow_definitions_published_version_id", table_name="workflow_definitions")
    op.drop_index("ix_workflow_definitions_organization_id", table_name="workflow_definitions")
    op.drop_table("workflow_definitions")

    op.drop_index("ix_ml_drift_records_model_id", table_name="ml_drift_records")
    op.drop_table("ml_drift_records")
    op.drop_index("ix_ml_anomaly_jobs_organization_id", table_name="ml_anomaly_jobs")
    op.drop_table("ml_anomaly_jobs")
    op.drop_index("ix_ml_forecasts_model_id", table_name="ml_forecasts")
    op.drop_table("ml_forecasts")
    op.drop_index("ix_ml_predictions_model_id", table_name="ml_predictions")
    op.drop_table("ml_predictions")
    op.drop_index("ix_ml_training_runs_organization_id", table_name="ml_training_runs")
    op.drop_index("ix_ml_training_runs_model_id", table_name="ml_training_runs")
    op.drop_table("ml_training_runs")
    op.drop_index("ix_ml_models_organization_id", table_name="ml_models")
    op.drop_table("ml_models")
