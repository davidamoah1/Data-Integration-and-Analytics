"""Pydantic schemas for Phase 6 AI Intelligence Platform API endpoints."""

from pydantic import BaseModel, Field

# --- Chat -------------------------------------------------------------------


class ChatRequest(BaseModel):
    message: str = Field(..., max_length=10000)
    assistant_type: str = Field(
        "data_copilot",
        description="data_copilot, etl_copilot, dashboard_copilot, report_copilot, decision_copilot, forecast_copilot, quality_copilot, sql_copilot",
    )
    conversation_id: int | None = None
    context: dict | None = None


class ChatResponse(BaseModel):
    conversation_id: int
    message_id: int
    response: str
    citations: list[dict] | None = None
    confidence_score: float | None = None
    tokens_used: int
    model_used: str
    provider: str


class ConversationSummary(BaseModel):
    id: int
    assistant_type: str
    title: str | None
    is_active: bool
    created_at: str | None
    updated_at: str | None


class MessageSummary(BaseModel):
    id: int
    role: str
    content: str
    tokens_used: int
    model_used: str | None
    provider: str | None
    confidence_score: float | None
    feedback: str | None
    created_at: str | None


# --- Provider Management ----------------------------------------------------


class ProviderConfigCreate(BaseModel):
    provider_name: str
    display_name: str
    api_key: str | None = None
    api_base_url: str | None = None
    default_model: str | None = None
    available_models: list[str] | None = None
    is_active: bool = True
    is_default: bool = False
    max_tokens: int = 4096
    temperature: float = 0.7
    config: dict | None = None


class ProviderConfigUpdate(BaseModel):
    display_name: str | None = None
    api_key: str | None = None
    api_base_url: str | None = None
    default_model: str | None = None
    available_models: list[str] | None = None
    is_active: bool | None = None
    is_default: bool | None = None
    max_tokens: int | None = None
    temperature: float | None = None
    config: dict | None = None


class ProviderConfigResponse(BaseModel):
    id: int
    provider_name: str
    display_name: str
    api_base_url: str | None
    default_model: str | None
    available_models: list[str] | None
    is_active: bool
    is_default: bool
    max_tokens: int
    temperature: float
    has_api_key: bool
    created_at: str | None


# --- NL to SQL --------------------------------------------------------------


class NLToSQLRequest(BaseModel):
    question: str = Field(..., max_length=5000)
    table_name: str | None = None
    schema_hint: dict | None = None


class NLToSQLResponse(BaseModel):
    sql: str
    explanation: str
    is_safe: bool
    warnings: list[str] = Field(default_factory=list)
    estimated_rows: int | None = None


# --- NL to ETL --------------------------------------------------------------


class NLToETLRequest(BaseModel):
    instruction: str = Field(..., max_length=5000)
    file_path: str | None = None
    target_table: str | None = None


class NLToETLResponse(BaseModel):
    pipeline_steps: list[dict]
    explanation: str
    estimated_duration: str | None = None


# --- NL to Dashboard --------------------------------------------------------


class NLToDashboardRequest(BaseModel):
    description: str = Field(..., max_length=5000)
    data_source: str | None = None


class NLToDashboardResponse(BaseModel):
    dashboard_config: dict
    charts: list[dict]
    explanation: str


# --- AI Data Quality --------------------------------------------------------


class AIQualityRequest(BaseModel):
    source_type: str
    source_config: dict
    auto_fix: bool = False


class AIQualityResponse(BaseModel):
    quality_score: int
    risk_level: str
    issues_found: list[dict]
    recommendations: list[str]
    fix_suggestions: list[dict]
    auto_fixes_applied: list[dict] | None = None


# --- AI Report Writer -------------------------------------------------------


class ReportGenerateRequest(BaseModel):
    report_type: str = Field(
        ..., description="executive, monthly, annual, department, quality, etl, performance, audit"
    )
    title: str | None = None
    date_from: str | None = None
    date_to: str | None = None
    department: str | None = None
    format: str = "markdown"


class ReportGenerateResponse(BaseModel):
    id: int
    report_type: str
    title: str
    content: str
    summary: str | None
    sections: list[str] | None
    created_at: str | None


# --- AI Decision Center -----------------------------------------------------


class DecisionCenterRequest(BaseModel):
    metric: str | None = None
    date_from: str | None = None
    date_to: str | None = None
    context: dict | None = None


class DecisionCenterResponse(BaseModel):
    id: int
    title: str
    summary: str
    key_findings: list[dict]
    recommendations: list[str]
    risks: list[str]
    opportunities: list[str]
    confidence_score: float | None
    data_sources: list[dict] | None


# --- AI Forecasting ---------------------------------------------------------


class ForecastRequest(BaseModel):
    source_type: str = Field(..., description="csv, excel, json, database")
    source_config: dict
    target_column: str
    date_column: str
    horizon: int = Field(30, ge=1, le=365)
    frequency: str = Field("D", description="D=daily, W=weekly, M=monthly, Q=quarterly, Y=yearly")
    confidence_level: float = Field(0.95, ge=0.5, le=0.99)


class ForecastResponse(BaseModel):
    id: int
    forecast_type: str
    target_column: str
    horizon: int
    method: str
    predictions: list[dict]
    accuracy_score: float | None
    confidence_level: float
    input_summary: dict | None


# --- AI Anomaly Detection ---------------------------------------------------


class AnomalyRequest(BaseModel):
    source_type: str
    source_config: dict
    metric_column: str
    date_column: str
    sensitivity: float = Field(2.0, ge=0.5, le=5.0)


class AnomalyResponse(BaseModel):
    alerts: list[dict]
    total_anomalies: int
    summary: str


# --- AI KPI Engine ----------------------------------------------------------


class KPIRecommendRequest(BaseModel):
    domain: str | None = Field(
        None, description="sales, operations, finance, healthcare, education"
    )
    data_source: dict | None = None


class KPIRecommendResponse(BaseModel):
    recommendations: list[dict]
    explanation: str


class KPIMonitorResponse(BaseModel):
    kpis: list[dict]
    alerts: list[dict]


# --- AI Dashboard Insights --------------------------------------------------


class DashboardInsightsRequest(BaseModel):
    dashboard_id: str | None = None
    data_source: dict | None = None
    context: dict | None = None


class DashboardInsightsResponse(BaseModel):
    key_findings: list[dict]
    risks: list[str]
    opportunities: list[str]
    recommendations: list[str]
    trend_analysis: dict | None


# --- AI Search --------------------------------------------------------------


class AISearchRequest(BaseModel):
    query: str = Field(..., max_length=500)
    search_type: str | None = Field(
        None, description="all, jobs, reports, pipelines, data, insights"
    )


class AISearchResponse(BaseModel):
    results: list[dict]
    total: int
    ai_summary: str | None = None


# --- AI Document Chat -------------------------------------------------------


class DocumentUploadResponse(BaseModel):
    document_id: int
    filename: str
    file_type: str
    page_count: int | None = None
    is_indexed: bool


class DocumentChatRequest(BaseModel):
    document_id: int
    question: str = Field(..., max_length=5000)


class DocumentChatResponse(BaseModel):
    answer: str
    citations: list[dict] | None = None
    confidence_score: float | None = None


# --- AI Workflow ------------------------------------------------------------


class WorkflowCreate(BaseModel):
    name: str
    description: str | None = None
    trigger_type: str = "manual"
    trigger_config: dict | None = None
    steps: list[dict]


class WorkflowResponse(BaseModel):
    id: int
    name: str
    description: str | None
    trigger_type: str
    trigger_config: dict | None
    steps: list[dict]
    is_active: bool
    created_at: str | None


class WorkflowRunResponse(BaseModel):
    id: int
    workflow_id: int
    status: str
    step_results: list[dict] | None
    duration_seconds: int | None
    error_message: str | None
    created_at: str | None


# --- AI Insights ------------------------------------------------------------


class InsightResponse(BaseModel):
    id: int
    insight_type: str
    title: str
    summary: str
    key_findings: list[dict] | None
    recommendations: list[str] | None
    risks: list[str] | None
    opportunities: list[str] | None
    confidence_score: float | None
    data_sources: list[dict] | None
    created_at: str | None


# --- AI Prompt Templates ----------------------------------------------------


class PromptTemplateCreate(BaseModel):
    name: str
    assistant_type: str
    system_prompt: str
    description: str | None = None
    variables: list[str] | None = None


class PromptTemplateResponse(BaseModel):
    id: int
    name: str
    assistant_type: str
    system_prompt: str
    description: str | None
    variables: list[str] | None
    is_active: bool
    is_system: bool
    created_at: str | None


# --- AI Usage & Audit -------------------------------------------------------


class UsageStatsResponse(BaseModel):
    total_requests: int
    total_tokens: int
    total_cost_usd: float
    by_provider: dict
    by_request_type: dict
    daily_average: float


class AuditLogResponse(BaseModel):
    id: int
    user_id: int | None
    action: str
    assistant_type: str | None
    input_summary: str | None
    output_summary: str | None
    success: bool
    error_message: str | None
    created_at: str | None


# --- AI Plugins -------------------------------------------------------------


class PluginResponse(BaseModel):
    id: int
    name: str
    display_name: str
    description: str | None
    plugin_type: str
    is_active: bool
    is_system: bool


# --- AI Dashboard -----------------------------------------------------------


class AIDashboardResponse(BaseModel):
    total_conversations: int
    total_messages: int
    total_tokens_used: int
    total_cost_usd: float
    active_workflows: int
    total_insights: int
    total_forecasts: int
    active_alerts: int
    provider_status: list[dict]
    recent_insights: list[dict]
    recent_alerts: list[dict]


# --- Feedback ---------------------------------------------------------------


class MessageFeedbackRequest(BaseModel):
    feedback: str = Field(..., description="positive or negative")


# --- AI Productivity Extensions ----------------------------------------------


class ExplainChartRequest(BaseModel):
    chart_type: str = Field(default="unknown", max_length=50)
    title: str = Field(default="", max_length=500)
    data_summary: dict = Field(default_factory=dict)
    context: str = Field(default="", max_length=2000)


class ExplainChartResponse(BaseModel):
    explanation: str
    chart_type: str


class ExplainETLFailureResponse(BaseModel):
    job_id: int
    explanation: str
    suggested_fixes: list[str]


class SummarizeReportRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=10000)
    report_type: str = Field(default="general", max_length=50)
    max_points: int = Field(default=5, ge=1, le=20)


class SummarizeReportResponse(BaseModel):
    summary: str
    key_findings: list[str]


class RecommendActionsRequest(BaseModel):
    context: str = Field(default="", max_length=2000)
    data_summary: dict = Field(default_factory=dict)


class RecommendActionsResponse(BaseModel):
    recommendations: list[str]
    full_response: str
