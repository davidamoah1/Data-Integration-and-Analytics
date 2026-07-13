"""Pydantic schemas for Phase 6 AI Intelligence Platform API endpoints."""

from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field


# --- Chat -------------------------------------------------------------------

class ChatRequest(BaseModel):
    message: str = Field(..., max_length=10000)
    assistant_type: str = Field("data_copilot", description="data_copilot, etl_copilot, dashboard_copilot, report_copilot, decision_copilot, forecast_copilot, quality_copilot, sql_copilot")
    conversation_id: Optional[int] = None
    context: Optional[dict] = None


class ChatResponse(BaseModel):
    conversation_id: int
    message_id: int
    response: str
    citations: Optional[list[dict]] = None
    confidence_score: Optional[float] = None
    tokens_used: int
    model_used: str
    provider: str


class ConversationSummary(BaseModel):
    id: int
    assistant_type: str
    title: Optional[str]
    is_active: bool
    created_at: Optional[str]
    updated_at: Optional[str]


class MessageSummary(BaseModel):
    id: int
    role: str
    content: str
    tokens_used: int
    model_used: Optional[str]
    provider: Optional[str]
    confidence_score: Optional[float]
    feedback: Optional[str]
    created_at: Optional[str]


# --- Provider Management ----------------------------------------------------

class ProviderConfigCreate(BaseModel):
    provider_name: str
    display_name: str
    api_key: Optional[str] = None
    api_base_url: Optional[str] = None
    default_model: Optional[str] = None
    available_models: Optional[list[str]] = None
    is_active: bool = True
    is_default: bool = False
    max_tokens: int = 4096
    temperature: float = 0.7
    config: Optional[dict] = None


class ProviderConfigUpdate(BaseModel):
    display_name: Optional[str] = None
    api_key: Optional[str] = None
    api_base_url: Optional[str] = None
    default_model: Optional[str] = None
    available_models: Optional[list[str]] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    config: Optional[dict] = None


class ProviderConfigResponse(BaseModel):
    id: int
    provider_name: str
    display_name: str
    api_base_url: Optional[str]
    default_model: Optional[str]
    available_models: Optional[list[str]]
    is_active: bool
    is_default: bool
    max_tokens: int
    temperature: float
    has_api_key: bool
    created_at: Optional[str]


# --- NL to SQL --------------------------------------------------------------

class NLToSQLRequest(BaseModel):
    question: str = Field(..., max_length=5000)
    table_name: Optional[str] = None
    schema_hint: Optional[dict] = None


class NLToSQLResponse(BaseModel):
    sql: str
    explanation: str
    is_safe: bool
    warnings: list[str] = Field(default_factory=list)
    estimated_rows: Optional[int] = None


# --- NL to ETL --------------------------------------------------------------

class NLToETLRequest(BaseModel):
    instruction: str = Field(..., max_length=5000)
    file_path: Optional[str] = None
    target_table: Optional[str] = None


class NLToETLResponse(BaseModel):
    pipeline_steps: list[dict]
    explanation: str
    estimated_duration: Optional[str] = None


# --- NL to Dashboard --------------------------------------------------------

class NLToDashboardRequest(BaseModel):
    description: str = Field(..., max_length=5000)
    data_source: Optional[str] = None


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
    auto_fixes_applied: Optional[list[dict]] = None


# --- AI Report Writer -------------------------------------------------------

class ReportGenerateRequest(BaseModel):
    report_type: str = Field(..., description="executive, monthly, annual, department, quality, etl, performance, audit")
    title: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    department: Optional[str] = None
    format: str = "markdown"


class ReportGenerateResponse(BaseModel):
    id: int
    report_type: str
    title: str
    content: str
    summary: Optional[str]
    sections: Optional[list[str]]
    created_at: Optional[str]


# --- AI Decision Center -----------------------------------------------------

class DecisionCenterRequest(BaseModel):
    metric: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    context: Optional[dict] = None


class DecisionCenterResponse(BaseModel):
    id: int
    title: str
    summary: str
    key_findings: list[dict]
    recommendations: list[str]
    risks: list[str]
    opportunities: list[str]
    confidence_score: Optional[float]
    data_sources: Optional[list[dict]]


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
    accuracy_score: Optional[float]
    confidence_level: float
    input_summary: Optional[dict]


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
    domain: Optional[str] = Field(None, description="sales, operations, finance, healthcare, education")
    data_source: Optional[dict] = None


class KPIRecommendResponse(BaseModel):
    recommendations: list[dict]
    explanation: str


class KPIMonitorResponse(BaseModel):
    kpis: list[dict]
    alerts: list[dict]


# --- AI Dashboard Insights --------------------------------------------------

class DashboardInsightsRequest(BaseModel):
    dashboard_id: Optional[str] = None
    data_source: Optional[dict] = None
    context: Optional[dict] = None


class DashboardInsightsResponse(BaseModel):
    key_findings: list[dict]
    risks: list[str]
    opportunities: list[str]
    recommendations: list[str]
    trend_analysis: Optional[dict]


# --- AI Search --------------------------------------------------------------

class AISearchRequest(BaseModel):
    query: str = Field(..., max_length=500)
    search_type: Optional[str] = Field(None, description="all, jobs, reports, pipelines, data, insights")


class AISearchResponse(BaseModel):
    results: list[dict]
    total: int
    ai_summary: Optional[str] = None


# --- AI Document Chat -------------------------------------------------------

class DocumentUploadResponse(BaseModel):
    document_id: int
    filename: str
    file_type: str
    page_count: Optional[int] = None
    is_indexed: bool


class DocumentChatRequest(BaseModel):
    document_id: int
    question: str = Field(..., max_length=5000)


class DocumentChatResponse(BaseModel):
    answer: str
    citations: Optional[list[dict]] = None
    confidence_score: Optional[float] = None


# --- AI Workflow ------------------------------------------------------------

class WorkflowCreate(BaseModel):
    name: str
    description: Optional[str] = None
    trigger_type: str = "manual"
    trigger_config: Optional[dict] = None
    steps: list[dict]


class WorkflowResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    trigger_type: str
    trigger_config: Optional[dict]
    steps: list[dict]
    is_active: bool
    created_at: Optional[str]


class WorkflowRunResponse(BaseModel):
    id: int
    workflow_id: int
    status: str
    step_results: Optional[list[dict]]
    duration_seconds: Optional[int]
    error_message: Optional[str]
    created_at: Optional[str]


# --- AI Insights ------------------------------------------------------------

class InsightResponse(BaseModel):
    id: int
    insight_type: str
    title: str
    summary: str
    key_findings: Optional[list[dict]]
    recommendations: Optional[list[str]]
    risks: Optional[list[str]]
    opportunities: Optional[list[str]]
    confidence_score: Optional[float]
    data_sources: Optional[list[dict]]
    created_at: Optional[str]


# --- AI Prompt Templates ----------------------------------------------------

class PromptTemplateCreate(BaseModel):
    name: str
    assistant_type: str
    system_prompt: str
    description: Optional[str] = None
    variables: Optional[list[str]] = None


class PromptTemplateResponse(BaseModel):
    id: int
    name: str
    assistant_type: str
    system_prompt: str
    description: Optional[str]
    variables: Optional[list[str]]
    is_active: bool
    is_system: bool
    created_at: Optional[str]


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
    user_id: Optional[int]
    action: str
    assistant_type: Optional[str]
    input_summary: Optional[str]
    output_summary: Optional[str]
    success: bool
    error_message: Optional[str]
    created_at: Optional[str]


# --- AI Plugins -------------------------------------------------------------

class PluginResponse(BaseModel):
    id: int
    name: str
    display_name: str
    description: Optional[str]
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
