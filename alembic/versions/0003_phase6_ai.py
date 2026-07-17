"""Phase 6 — AI Intelligence Platform tables.

Revision ID: 0003_phase6_ai
Revises: 0002_phase5_etl
Create Date: 2026-07-12
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0003_phase6_ai"
down_revision = "0002_phase5_etl"
branch_labels = None
depends_on = None


def upgrade():
    # --- AI Conversations ---
    op.create_table(
        "ai_conversations",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger(), nullable=False, index=True),
        sa.Column("assistant_type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column("context", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), default=True, nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            onupdate=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )

    # --- AI Messages ---
    op.create_table(
        "ai_messages",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "conversation_id",
            sa.BigInteger(),
            sa.ForeignKey("ai_conversations.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("tokens_used", sa.Integer(), default=0, nullable=False),
        sa.Column("model_used", sa.String(100), nullable=True),
        sa.Column("provider", sa.String(50), nullable=True),
        sa.Column("response_time_ms", sa.Integer(), nullable=True),
        sa.Column("citations", sa.JSON(), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("feedback", sa.String(20), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )

    # --- AI Provider Configs ---
    op.create_table(
        "ai_provider_configs",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("provider_name", sa.String(50), nullable=False, unique=True),
        sa.Column("display_name", sa.String(100), nullable=False),
        sa.Column("api_key_encrypted", sa.Text(), nullable=True),
        sa.Column("api_base_url", sa.String(500), nullable=True),
        sa.Column("default_model", sa.String(100), nullable=True),
        sa.Column("available_models", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), default=False, nullable=False),
        sa.Column("is_default", sa.Boolean(), default=False, nullable=False),
        sa.Column("max_tokens", sa.Integer(), default=4096, nullable=False),
        sa.Column("temperature", sa.Float(), default=0.7, nullable=False),
        sa.Column("config", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            onupdate=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )

    # --- AI Usage Logs ---
    op.create_table(
        "ai_usage_logs",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger(), nullable=True, index=True),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column("prompt_tokens", sa.Integer(), default=0, nullable=False),
        sa.Column("completion_tokens", sa.Integer(), default=0, nullable=False),
        sa.Column("total_tokens", sa.Integer(), default=0, nullable=False),
        sa.Column("estimated_cost_usd", sa.Float(), default=0.0, nullable=False),
        sa.Column("request_type", sa.String(50), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )
    op.create_index("idx_usage_user_date", "ai_usage_logs", ["user_id", "created_at"])
    op.create_index("idx_usage_provider", "ai_usage_logs", ["provider"])

    # --- AI Audit Logs ---
    op.create_table(
        "ai_audit_logs",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger(), nullable=True, index=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("assistant_type", sa.String(50), nullable=True),
        sa.Column("input_summary", sa.Text(), nullable=True),
        sa.Column("output_summary", sa.Text(), nullable=True),
        sa.Column("data_accessed", sa.JSON(), nullable=True),
        sa.Column("permissions_checked", sa.JSON(), nullable=True),
        sa.Column("success", sa.Boolean(), default=True, nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(50), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )

    # --- AI Workflows ---
    op.create_table(
        "ai_workflows",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("user_id", sa.BigInteger(), nullable=True, index=True),
        sa.Column("trigger_type", sa.String(30), default="manual", nullable=False),
        sa.Column("trigger_config", sa.JSON(), nullable=True),
        sa.Column("steps", sa.JSON(), nullable=False),
        sa.Column("is_active", sa.Boolean(), default=True, nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            onupdate=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )

    # --- AI Workflow Runs ---
    op.create_table(
        "ai_workflow_runs",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "workflow_id",
            sa.BigInteger(),
            sa.ForeignKey("ai_workflows.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("status", sa.String(20), default="queued", nullable=False),
        sa.Column("trigger_type", sa.String(30), default="manual", nullable=False),
        sa.Column("step_results", sa.JSON(), nullable=True),
        sa.Column("started_at", sa.TIMESTAMP(), nullable=True),
        sa.Column("completed_at", sa.TIMESTAMP(), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )

    # --- AI Insights ---
    op.create_table(
        "ai_insights",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("insight_type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("key_findings", sa.JSON(), nullable=True),
        sa.Column("recommendations", sa.JSON(), nullable=True),
        sa.Column("risks", sa.JSON(), nullable=True),
        sa.Column("opportunities", sa.JSON(), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("data_sources", sa.JSON(), nullable=True),
        sa.Column("user_id", sa.BigInteger(), nullable=True, index=True),
        sa.Column("is_archived", sa.Boolean(), default=False, nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )

    # --- AI Forecasts ---
    op.create_table(
        "ai_forecasts",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("forecast_type", sa.String(50), nullable=False),
        sa.Column("target_column", sa.String(100), nullable=False),
        sa.Column("horizon", sa.Integer(), nullable=False),
        sa.Column("method", sa.String(50), nullable=True),
        sa.Column("predictions", sa.JSON(), nullable=False),
        sa.Column("accuracy_score", sa.Float(), nullable=True),
        sa.Column("confidence_level", sa.Float(), default=0.95, nullable=False),
        sa.Column("input_summary", sa.JSON(), nullable=True),
        sa.Column("user_id", sa.BigInteger(), nullable=True, index=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )

    # --- AI Anomaly Alerts ---
    op.create_table(
        "ai_anomaly_alerts",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("alert_type", sa.String(50), nullable=False),
        sa.Column("severity", sa.String(20), default="warning", nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("metric_name", sa.String(100), nullable=True),
        sa.Column("expected_value", sa.Float(), nullable=True),
        sa.Column("actual_value", sa.Float(), nullable=True),
        sa.Column("deviation_percentage", sa.Float(), nullable=True),
        sa.Column("context_data", sa.JSON(), nullable=True),
        sa.Column("is_resolved", sa.Boolean(), default=False, nullable=False),
        sa.Column("resolved_by", sa.BigInteger(), nullable=True),
        sa.Column("resolved_at", sa.TIMESTAMP(), nullable=True),
        sa.Column("user_id", sa.BigInteger(), nullable=True, index=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )

    # --- AI Documents ---
    op.create_table(
        "ai_documents",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("file_type", sa.String(20), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("file_path", sa.String(500), nullable=False),
        sa.Column("extracted_text", sa.Text(), nullable=True),
        sa.Column("extra_data", sa.JSON(), nullable=True),
        sa.Column("user_id", sa.BigInteger(), nullable=True, index=True),
        sa.Column("is_indexed", sa.Boolean(), default=False, nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )

    # --- AI KPI Recommendations ---
    op.create_table(
        "ai_kpi_recommendations",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("kpi_name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("formula", sa.Text(), nullable=True),
        sa.Column("target_value", sa.Float(), nullable=True),
        sa.Column("current_value", sa.Float(), nullable=True),
        sa.Column("unit", sa.String(50), nullable=True),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("threshold_warning", sa.Float(), nullable=True),
        sa.Column("threshold_critical", sa.Float(), nullable=True),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column("user_id", sa.BigInteger(), nullable=True, index=True),
        sa.Column("is_active", sa.Boolean(), default=True, nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )

    # --- AI Report Generations ---
    op.create_table(
        "ai_report_generations",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("report_type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("data_sources", sa.JSON(), nullable=True),
        sa.Column("sections", sa.JSON(), nullable=True),
        sa.Column("format", sa.String(20), default="markdown", nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=True, index=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )

    # --- AI Prompt Templates ---
    op.create_table(
        "ai_prompt_templates",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(200), nullable=False, unique=True),
        sa.Column("assistant_type", sa.String(50), nullable=False),
        sa.Column("system_prompt", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("variables", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), default=True, nullable=False),
        sa.Column("is_system", sa.Boolean(), default=False, nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            onupdate=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )

    # --- AI Plugins ---
    op.create_table(
        "ai_plugins",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("display_name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("plugin_type", sa.String(50), nullable=False),
        sa.Column("module_path", sa.String(500), nullable=False),
        sa.Column("config_schema", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), default=False, nullable=False),
        sa.Column("is_system", sa.Boolean(), default=False, nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )


def downgrade():
    tables = [
        "ai_plugins",
        "ai_prompt_templates",
        "ai_report_generations",
        "ai_kpi_recommendations",
        "ai_documents",
        "ai_anomaly_alerts",
        "ai_forecasts",
        "ai_insights",
        "ai_workflow_runs",
        "ai_workflows",
        "ai_audit_logs",
        "ai_usage_logs",
        "ai_provider_configs",
        "ai_messages",
        "ai_conversations",
    ]
    for table in tables:
        op.drop_table(table)
