"""SQLAlchemy ORM models for Phase 6 AI Intelligence Platform.

Tables:
  - ai_conversations: Chat sessions between users and AI assistants
  - ai_messages: Individual messages within conversations
  - ai_provider_configs: Provider configuration (API keys, models, settings)
  - ai_usage_logs: Token usage and cost tracking per request
  - ai_audit_logs: AI action audit trail for compliance
  - ai_workflows: Automated AI workflow definitions
  - ai_workflow_runs: Workflow execution records
  - ai_insights: Generated insights (decision center, dashboard insights, etc.)
  - ai_forecasts: Forecasting results
  - ai_anomaly_alerts: Anomaly detection alerts
  - ai_documents: Uploaded documents for document chat
  - ai_kpi_recommendations: AI-recommended KPIs
  - ai_report_generations: AI-generated report metadata
  - ai_prompt_templates: Reusable prompt templates
  - ai_plugins: Registered AI plugins
"""

from sqlalchemy import (
    JSON,
    TIMESTAMP,
    Boolean,
    Column,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)

from shared.database import Base, BigInt


class AIConversation(Base):
    """A chat conversation between a user and an AI assistant."""

    __tablename__ = "ai_conversations"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    user_id = Column(BigInt, nullable=False, index=True)
    assistant_type = Column(String(50), nullable=False)  # data_copilot, etl_copilot, etc.
    title = Column(String(255), nullable=True)
    context = Column(JSON, nullable=True)  # platform context snapshot
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)


class AIMessage(Base):
    """Individual messages within an AI conversation."""

    __tablename__ = "ai_messages"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    conversation_id = Column(BigInt, ForeignKey("ai_conversations.id"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    tokens_used = Column(Integer, default=0, nullable=False)
    model_used = Column(String(100), nullable=True)
    provider = Column(String(50), nullable=True)
    response_time_ms = Column(Integer, nullable=True)
    citations = Column(JSON, nullable=True)  # references to underlying data
    confidence_score = Column(Float, nullable=True)
    feedback = Column(String(20), nullable=True)  # positive, negative, null
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)


class AIProviderConfig(Base):
    """Configuration for AI providers — admin managed."""

    __tablename__ = "ai_provider_configs"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    provider_name = Column(String(50), nullable=False, unique=True)  # openai, gemini, etc.
    display_name = Column(String(100), nullable=False)
    api_key_encrypted = Column(Text, nullable=True)
    api_base_url = Column(String(500), nullable=True)
    default_model = Column(String(100), nullable=True)
    available_models = Column(JSON, nullable=True)  # list of model names
    is_active = Column(Boolean, default=False, nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)
    max_tokens = Column(Integer, default=4096, nullable=False)
    temperature = Column(Float, default=0.7, nullable=False)
    config = Column(JSON, nullable=True)  # provider-specific settings
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)


class AIUsageLog(Base):
    """Token usage and cost tracking per AI request."""

    __tablename__ = "ai_usage_logs"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    user_id = Column(BigInt, nullable=True, index=True)
    provider = Column(String(50), nullable=False)
    model = Column(String(100), nullable=False)
    prompt_tokens = Column(Integer, default=0, nullable=False)
    completion_tokens = Column(Integer, default=0, nullable=False)
    total_tokens = Column(Integer, default=0, nullable=False)
    estimated_cost_usd = Column(Float, default=0.0, nullable=False)
    request_type = Column(String(50), nullable=True)  # chat, sql, etl, forecast, etc.
    duration_ms = Column(Integer, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_usage_user_date", "user_id", "created_at"),
        Index("idx_usage_provider", "provider"),
    )


class AIAuditLog(Base):
    """Audit trail for all AI actions — compliance and security."""

    __tablename__ = "ai_audit_logs"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    user_id = Column(BigInt, nullable=True, index=True)
    action = Column(String(100), nullable=False)  # chat, generate_sql, generate_etl, etc.
    assistant_type = Column(String(50), nullable=True)
    input_summary = Column(Text, nullable=True)  # sanitized input summary
    output_summary = Column(Text, nullable=True)  # sanitized output summary
    data_accessed = Column(JSON, nullable=True)  # what data was referenced
    permissions_checked = Column(JSON, nullable=True)  # what perms were verified
    success = Column(Boolean, default=True, nullable=False)
    error_message = Column(Text, nullable=True)
    ip_address = Column(String(50), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)


class AIWorkflow(Base):
    """Automated AI workflow definition."""

    __tablename__ = "ai_workflows"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    user_id = Column(BigInt, nullable=True, index=True)
    trigger_type = Column(String(30), nullable=False, default="manual")  # manual, scheduled, event
    trigger_config = Column(JSON, nullable=True)  # cron expr, event filter, etc.
    steps = Column(JSON, nullable=False)  # list of workflow steps
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)


class AIWorkflowRun(Base):
    """Execution record for an AI workflow."""

    __tablename__ = "ai_workflow_runs"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    workflow_id = Column(BigInt, ForeignKey("ai_workflows.id"), nullable=False, index=True)
    status = Column(
        String(20), nullable=False, default="queued"
    )  # queued, running, completed, failed
    trigger_type = Column(String(30), nullable=False, default="manual")
    step_results = Column(JSON, nullable=True)
    started_at = Column(TIMESTAMP, nullable=True)
    completed_at = Column(TIMESTAMP, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)


class AIInsight(Base):
    """Generated insights from decision center, dashboard insights, etc."""

    __tablename__ = "ai_insights"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    insight_type = Column(
        String(50), nullable=False
    )  # decision, dashboard, trend, risk, opportunity
    title = Column(String(255), nullable=False)
    summary = Column(Text, nullable=False)
    details = Column(JSON, nullable=True)  # structured insight data
    key_findings = Column(JSON, nullable=True)  # list of findings
    recommendations = Column(JSON, nullable=True)  # list of recommended actions
    risks = Column(JSON, nullable=True)  # list of identified risks
    opportunities = Column(JSON, nullable=True)  # list of opportunities
    confidence_score = Column(Float, nullable=True)
    data_sources = Column(JSON, nullable=True)  # citations to underlying data
    user_id = Column(BigInt, nullable=True, index=True)
    is_archived = Column(Boolean, default=False, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)


class AIForecast(Base):
    """Forecasting results from the AI forecasting engine."""

    __tablename__ = "ai_forecasts"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    forecast_type = Column(String(50), nullable=False)  # revenue, attendance, enrollment, etc.
    target_column = Column(String(100), nullable=False)
    horizon = Column(Integer, nullable=False)  # number of periods forecasted
    method = Column(String(50), nullable=True)  # auto, arima, exponential, linear, etc.
    predictions = Column(JSON, nullable=False)  # list of {date, value, lower_ci, upper_ci}
    accuracy_score = Column(Float, nullable=True)
    confidence_level = Column(Float, default=0.95, nullable=False)
    input_summary = Column(JSON, nullable=True)  # stats about input data
    user_id = Column(BigInt, nullable=True, index=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)


class AIAnomalyAlert(Base):
    """Anomaly detection alerts."""

    __tablename__ = "ai_anomaly_alerts"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    alert_type = Column(String(50), nullable=False)  # spike, drop, fraud, trend, missing
    severity = Column(String(20), nullable=False, default="warning")  # info, warning, critical
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    metric_name = Column(String(100), nullable=True)
    expected_value = Column(Float, nullable=True)
    actual_value = Column(Float, nullable=True)
    deviation_percentage = Column(Float, nullable=True)
    context_data = Column(JSON, nullable=True)
    is_resolved = Column(Boolean, default=False, nullable=False)
    resolved_by = Column(BigInt, nullable=True)
    resolved_at = Column(TIMESTAMP, nullable=True)
    user_id = Column(BigInt, nullable=True, index=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)


class AIDocument(Base):
    """Uploaded documents for AI document chat."""

    __tablename__ = "ai_documents"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(20), nullable=False)  # pdf, word, excel, csv, ppt
    file_size = Column(Integer, nullable=False)
    file_path = Column(String(500), nullable=False)
    extracted_text = Column(Text, nullable=True)
    extra_data = Column(JSON, nullable=True)  # page count, sheet names, etc.
    user_id = Column(BigInt, nullable=True, index=True)
    is_indexed = Column(Boolean, default=False, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)


class AIKPIRecommendation(Base):
    """AI-recommended KPIs for the organization."""

    __tablename__ = "ai_kpi_recommendations"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    kpi_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    formula = Column(Text, nullable=True)  # how to calculate
    target_value = Column(Float, nullable=True)
    current_value = Column(Float, nullable=True)
    unit = Column(String(50), nullable=True)
    category = Column(String(100), nullable=True)  # sales, operations, finance, etc.
    threshold_warning = Column(Float, nullable=True)
    threshold_critical = Column(Float, nullable=True)
    rationale = Column(Text, nullable=True)  # why this KPI matters
    user_id = Column(BigInt, nullable=True, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)


class AIReportGeneration(Base):
    """Metadata for AI-generated reports."""

    __tablename__ = "ai_report_generations"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    report_type = Column(String(50), nullable=False)  # executive, monthly, annual, department, etc.
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)  # markdown content
    summary = Column(Text, nullable=True)
    data_sources = Column(JSON, nullable=True)
    sections = Column(JSON, nullable=True)  # list of section titles
    format = Column(String(20), default="markdown", nullable=False)  # markdown, html, pdf
    user_id = Column(BigInt, nullable=True, index=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)


class AIPromptTemplate(Base):
    """Reusable prompt templates managed by administrators."""

    __tablename__ = "ai_prompt_templates"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, unique=True)
    assistant_type = Column(String(50), nullable=False)
    system_prompt = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    variables = Column(JSON, nullable=True)  # list of template variables
    is_active = Column(Boolean, default=True, nullable=False)
    is_system = Column(Boolean, default=False, nullable=False)  # built-in vs custom
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)


class AIPlugin(Base):
    """Registered AI plugins for extensibility."""

    __tablename__ = "ai_plugins"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    display_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    plugin_type = Column(String(50), nullable=False)  # provider, assistant, engine, tool
    module_path = Column(String(500), nullable=False)  # import path
    config_schema = Column(JSON, nullable=True)  # expected configuration
    is_active = Column(Boolean, default=False, nullable=False)
    is_system = Column(Boolean, default=False, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
