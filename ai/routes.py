"""FastAPI routes for the AI Intelligence Platform — all AI endpoints.

Endpoints:
  - AI Chat (streaming + non-streaming)
  - Conversations (list, get, delete)
  - Provider management (CRUD, test, list)
  - NL-to-SQL (generate, execute)
  - NL-to-ETL (generate pipeline)
  - NL-to-Dashboard (generate dashboard)
  - AI Data Quality (analyze, fix)
  - AI Report Writer (generate, list, get)
  - AI Decision Center (analyze, insights)
  - AI Forecasting (forecast, list, get)
  - AI Anomaly Detection (detect, alerts, resolve)
  - AI KPI Engine (recommend, monitor)
  - AI Dashboard Insights (generate)
  - AI Search (global search)
  - AI Document Chat (upload, chat, list)
  - AI Workflow (create, execute, list, runs)
  - AI Prompt Templates (CRUD)
  - AI Usage & Audit (stats, logs)
  - AI Plugins (list, activate, deactivate)
  - AI Dashboard (overview metrics)
  - AI Assistants (list)
  - Message Feedback
"""

# ruff: noqa: B008  # FastAPI Depends() calls in default arguments are intentional

from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile
from sqlalchemy.orm import Session as DbSession

from ai.assistants.assistants import list_assistants
from ai.engines.ai_quality import AIDataQualityEngine
from ai.engines.ai_search import AISearchEngine
from ai.engines.anomaly_detection import AnomalyDetectionEngine
from ai.engines.dashboard_insights import DashboardInsightsEngine
from ai.engines.decision_center import DecisionCenterEngine
from ai.engines.document_chat import DocumentChatEngine
from ai.engines.forecasting import ForecastingEngine
from ai.engines.kpi_engine import KPIEngine
from ai.engines.nl_to_dashboard import NLToDashboardEngine
from ai.engines.nl_to_etl import NLToETLEngine
from ai.engines.nl_to_sql import NLToSQLEngine
from ai.engines.report_writer import AIReportWriter
from ai.gateway import AIGateway
from ai.memory import AIMemory
from ai.models import (
    AIAnomalyAlert,
    AIAuditLog,
    AIConversation,
    AIForecast,
    AIInsight,
    AIMessage,
    AIPromptTemplate,
    AIProviderConfig,
    AIReportGeneration,
    AIWorkflow,
)
from ai.plugins import PluginRegistry
from ai.prompts.templates import PromptManager
from ai.providers.manager import ProviderManager
from ai.schemas import (
    AIDashboardResponse,
    AIQualityRequest,
    AIQualityResponse,
    AISearchRequest,
    AISearchResponse,
    AnomalyRequest,
    AnomalyResponse,
    AuditLogResponse,
    ChatRequest,
    ChatResponse,
    ConversationSummary,
    DashboardInsightsRequest,
    DashboardInsightsResponse,
    DecisionCenterRequest,
    DecisionCenterResponse,
    DocumentChatRequest,
    DocumentChatResponse,
    DocumentUploadResponse,
    ExplainChartRequest,
    ExplainChartResponse,
    ExplainETLFailureResponse,
    ForecastRequest,
    ForecastResponse,
    InsightResponse,
    KPIMonitorResponse,
    KPIRecommendRequest,
    KPIRecommendResponse,
    MessageFeedbackRequest,
    MessageSummary,
    NLToDashboardRequest,
    NLToDashboardResponse,
    NLToETLRequest,
    NLToETLResponse,
    NLToSQLRequest,
    NLToSQLResponse,
    PluginResponse,
    PromptTemplateCreate,
    PromptTemplateResponse,
    ProviderConfigCreate,
    ProviderConfigResponse,
    ProviderConfigUpdate,
    RecommendActionsRequest,
    RecommendActionsResponse,
    ReportGenerateRequest,
    ReportGenerateResponse,
    SummarizeReportRequest,
    SummarizeReportResponse,
    UsageStatsResponse,
    WorkflowCreate,
    WorkflowResponse,
    WorkflowRunResponse,
)
from ai.usage import UsageTracker
from ai.workflow import WorkflowEngine
from services.report_export_service import ReportExportService
from shared.database import get_db
from shared.dependencies import get_current_user, require_permissions
from shared.security import encrypt_secret
from shared.tenant import get_tenant_context, verify_resource_ownership

router = APIRouter(prefix="/ai", tags=["AI Intelligence Platform"])


# --- AI Chat ----------------------------------------------------------------


@router.post("/chat", response_model=ChatResponse)
async def ai_chat(
    request: ChatRequest,
    db: DbSession = Depends(get_db),
    tenant: dict = Depends(get_tenant_context),
):
    """Send a message to an AI assistant and get a response."""
    current_user = tenant["user"]
    org_id = tenant["organization_id"]
    gateway = AIGateway(db)
    try:
        result = gateway.chat(
            user_message=request.message,
            assistant_type=request.assistant_type,
            user_id=current_user["id"],
            conversation_id=request.conversation_id,
            context=request.context,
            stream=False,
            permissions=current_user.get("permissions", []),
            organization_id=org_id,
        )
        return ChatResponse(
            conversation_id=result["conversation_id"],
            message_id=result["message_id"],
            response=result["response"],
            citations=result.get("citations"),
            confidence_score=result.get("confidence_score"),
            tokens_used=result["tokens_used"],
            model_used=result["model_used"],
            provider=result["provider"],
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail="AI request failed") from e


@router.post("/chat/stream")
async def ai_chat_stream(
    request: ChatRequest,
    db: DbSession = Depends(get_db),
    tenant: dict = Depends(get_tenant_context),
):
    """Stream a chat response from an AI assistant."""
    from fastapi.responses import StreamingResponse

    current_user = tenant["user"]
    org_id = tenant["organization_id"]
    gateway = AIGateway(db)
    try:
        generator = gateway.chat(
            user_message=request.message,
            assistant_type=request.assistant_type,
            user_id=current_user["id"],
            conversation_id=request.conversation_id,
            context=request.context,
            stream=True,
            permissions=current_user.get("permissions", []),
            organization_id=org_id,
        )
        return StreamingResponse(
            generator,
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="AI streaming request failed") from e


# --- Conversations ----------------------------------------------------------


@router.get("/conversations", response_model=list[ConversationSummary])
async def list_conversations(
    assistant_type: str | None = Query(None),
    db: DbSession = Depends(get_db),
    tenant: dict = Depends(get_tenant_context),
):
    """List user's AI conversations."""
    current_user = tenant["user"]
    org_id = tenant["organization_id"]
    memory = AIMemory(db)
    return memory.get_conversations(current_user["id"], assistant_type, org_id)


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageSummary])
async def get_conversation_messages(
    conversation_id: int,
    db: DbSession = Depends(get_db),
    tenant: dict = Depends(get_tenant_context),
):
    """Get all messages in a conversation."""
    current_user = tenant["user"]
    org_id = tenant["organization_id"]
    conversation = (
        db.query(AIConversation)
        .filter(
            AIConversation.id == conversation_id,
            AIConversation.user_id == current_user["id"],
            AIConversation.organization_id == org_id,
        )
        .first()
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    memory = AIMemory(db)
    return memory.get_conversation_messages(conversation_id)


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: int,
    db: DbSession = Depends(get_db),
    tenant: dict = Depends(get_tenant_context),
):
    """Delete (archive) a conversation."""
    current_user = tenant["user"]
    org_id = tenant["organization_id"]
    conversation = (
        db.query(AIConversation)
        .filter(
            AIConversation.id == conversation_id,
            AIConversation.user_id == current_user["id"],
            AIConversation.organization_id == org_id,
        )
        .first()
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    memory = AIMemory(db)
    memory.delete_conversation(conversation_id)
    return {"message": "Conversation archived"}


@router.get("/conversations/search", response_model=list[ConversationSummary])
async def search_conversations(
    q: str = Query(..., min_length=1, max_length=200),
    limit: int = Query(20, ge=1, le=100),
    db: DbSession = Depends(get_db),
    tenant: dict = Depends(get_tenant_context),
):
    """Search user's AI conversations by title and message content."""
    current_user = tenant["user"]
    memory = AIMemory(db)
    return memory.search_conversations(current_user["id"], q, limit)


@router.get("/conversations/{conversation_id}/export")
async def export_conversation(
    conversation_id: int,
    db: DbSession = Depends(get_db),
    tenant: dict = Depends(get_tenant_context),
):
    """Export a conversation with all messages as structured data."""
    current_user = tenant["user"]
    memory = AIMemory(db)
    result = memory.export_conversation(conversation_id, current_user["id"])
    if not result:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return result


@router.post("/messages/{message_id}/feedback")
async def message_feedback(
    message_id: int,
    request: MessageFeedbackRequest,
    db: DbSession = Depends(get_db),
    tenant: dict = Depends(get_tenant_context),
):
    """Provide feedback (positive/negative) on an AI message."""
    current_user = tenant["user"]
    org_id = tenant["organization_id"]
    msg = db.query(AIMessage).filter(AIMessage.id == message_id).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    conversation = (
        db.query(AIConversation)
        .filter(
            AIConversation.id == msg.conversation_id,
            AIConversation.user_id == current_user["id"],
            AIConversation.organization_id == org_id,
        )
        .first()
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="Message not found")
    memory = AIMemory(db)
    memory.set_feedback(message_id, request.feedback)
    return {"message": "Feedback recorded"}


# --- AI Assistants ----------------------------------------------------------


@router.get("/assistants")
async def list_all_assistants(
    tenant: dict = Depends(get_tenant_context),
):
    """List all available AI assistants."""
    return list_assistants()


# --- Provider Management ----------------------------------------------------


@router.get("/providers")
async def list_providers(
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(require_permissions("ai.use")),
):
    """List all AI providers and their status."""
    manager = ProviderManager(db)
    return manager.list_providers()


@router.post("/providers", response_model=ProviderConfigResponse)
async def create_provider(
    config: ProviderConfigCreate,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(require_permissions("settings.manage")),
):
    """Configure a new AI provider."""
    existing = (
        db.query(AIProviderConfig)
        .filter(AIProviderConfig.provider_name == config.provider_name)
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Provider already configured")

    provider = AIProviderConfig(
        provider_name=config.provider_name,
        display_name=config.display_name,
        api_key_encrypted=encrypt_secret(config.api_key),
        api_base_url=config.api_base_url,
        default_model=config.default_model,
        available_models=config.available_models,
        is_active=config.is_active,
        is_default=config.is_default,
        max_tokens=config.max_tokens,
        temperature=config.temperature,
        config=config.config,
    )
    db.add(provider)
    db.commit()
    db.refresh(provider)
    return ProviderConfigResponse(
        id=provider.id,
        provider_name=provider.provider_name,
        display_name=provider.display_name,
        api_base_url=provider.api_base_url,
        default_model=provider.default_model,
        available_models=provider.available_models,
        is_active=provider.is_active,
        is_default=provider.is_default,
        max_tokens=provider.max_tokens,
        temperature=provider.temperature,
        has_api_key=bool(provider.api_key_encrypted),
        created_at=str(provider.created_at) if provider.created_at else None,
    )


@router.put("/providers/{provider_id}", response_model=ProviderConfigResponse)
async def update_provider(
    provider_id: int,
    config: ProviderConfigUpdate,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(require_permissions("settings.manage")),
):
    """Update an AI provider configuration."""
    provider = db.query(AIProviderConfig).filter(AIProviderConfig.id == provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    if config.display_name is not None:
        provider.display_name = config.display_name
    if config.api_key is not None:
        provider.api_key_encrypted = encrypt_secret(config.api_key)
    if config.api_base_url is not None:
        provider.api_base_url = config.api_base_url
    if config.default_model is not None:
        provider.default_model = config.default_model
    if config.available_models is not None:
        provider.available_models = config.available_models
    if config.is_active is not None:
        provider.is_active = config.is_active
    if config.is_default is not None:
        if config.is_default:
            db.query(AIProviderConfig).filter(AIProviderConfig.is_default.is_(True)).update(
                {AIProviderConfig.is_default: False}
            )
        provider.is_default = config.is_default
    if config.max_tokens is not None:
        provider.max_tokens = config.max_tokens
    if config.temperature is not None:
        provider.temperature = config.temperature
    if config.config is not None:
        provider.config = config.config

    db.commit()
    db.refresh(provider)
    return ProviderConfigResponse(
        id=provider.id,
        provider_name=provider.provider_name,
        display_name=provider.display_name,
        api_base_url=provider.api_base_url,
        default_model=provider.default_model,
        available_models=provider.available_models,
        is_active=provider.is_active,
        is_default=provider.is_default,
        max_tokens=provider.max_tokens,
        temperature=provider.temperature,
        has_api_key=bool(provider.api_key_encrypted),
        created_at=str(provider.created_at) if provider.created_at else None,
    )


@router.post("/providers/{provider_name}/test")
async def test_provider(
    provider_name: str,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(require_permissions("settings.manage")),
):
    """Test a provider connection."""
    manager = ProviderManager(db)
    return manager.test_provider(provider_name)


# --- NL to SQL --------------------------------------------------------------


@router.post("/sql/generate", response_model=NLToSQLResponse)
async def generate_sql(
    request: NLToSQLRequest,
    db: DbSession = Depends(get_db),
    tenant: dict = Depends(get_tenant_context),
):
    """Generate SQL from a natural language question."""
    current_user = tenant["user"]
    engine = NLToSQLEngine(db)
    result = engine.generate_sql(
        question=request.question,
        table_name=request.table_name,
        schema_hint=request.schema_hint,
        user_id=current_user["id"],
    )
    return NLToSQLResponse(**result)


@router.post("/sql/execute")
async def execute_sql(
    sql: str = Query(..., description="Validated SQL query to execute"),
    limit: int = Query(100, ge=1, le=1000),
    db: DbSession = Depends(get_db),
    tenant: dict = Depends(get_tenant_context),
):
    """Execute a validated SQL query safely."""
    engine = NLToSQLEngine(db)
    return engine.execute_sql(sql, limit)


# --- NL to ETL --------------------------------------------------------------


@router.post("/etl/generate", response_model=NLToETLResponse)
async def generate_etl(
    request: NLToETLRequest,
    db: DbSession = Depends(get_db),
    tenant: dict = Depends(get_tenant_context),
):
    """Generate ETL pipeline steps from natural language."""
    current_user = tenant["user"]
    engine = NLToETLEngine(db)
    result = engine.generate_pipeline(
        instruction=request.instruction,
        file_path=request.file_path,
        target_table=request.target_table,
        user_id=current_user["id"],
    )
    return NLToETLResponse(**result)


# --- NL to Dashboard --------------------------------------------------------


@router.post("/dashboard/generate", response_model=NLToDashboardResponse)
async def generate_dashboard(
    request: NLToDashboardRequest,
    db: DbSession = Depends(get_db),
    tenant: dict = Depends(get_tenant_context),
):
    """Generate a dashboard configuration from a description."""
    current_user = tenant["user"]
    engine = NLToDashboardEngine(db)
    result = engine.generate_dashboard(
        description=request.description,
        data_source=request.data_source,
        user_id=current_user["id"],
    )
    return NLToDashboardResponse(**result)


# --- AI Data Quality --------------------------------------------------------


@router.post("/quality/analyze", response_model=AIQualityResponse)
async def ai_quality_analyze(
    request: AIQualityRequest,
    db: DbSession = Depends(get_db),
    tenant: dict = Depends(get_tenant_context),
):
    """Analyze data quality with AI enhancement."""
    current_user = tenant["user"]
    engine = AIDataQualityEngine(db)
    result = engine.analyze(
        source_type=request.source_type,
        source_config=request.source_config,
        auto_fix=request.auto_fix,
        user_id=current_user["id"],
        permissions=current_user.get("permissions", []),
    )
    return AIQualityResponse(**result)


# --- AI Report Writer -------------------------------------------------------


@router.post("/reports/generate", response_model=ReportGenerateResponse)
async def generate_report(
    request: ReportGenerateRequest,
    db: DbSession = Depends(get_db),
    tenant: dict = Depends(get_tenant_context),
):
    """Generate an AI-powered report."""
    current_user = tenant["user"]
    org_id = tenant["organization_id"]
    engine = AIReportWriter(db)
    result = engine.generate_report(
        report_type=request.report_type,
        title=request.title,
        date_from=request.date_from,
        date_to=request.date_to,
        department=request.department,
        format=request.format,
        user_id=current_user["id"],
        organization_id=org_id,
    )
    return ReportGenerateResponse(**result)


@router.get("/reports", response_model=list[dict])
async def list_reports(
    report_type: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: DbSession = Depends(get_db),
    tenant: dict = Depends(get_tenant_context),
):
    """List AI-generated reports."""
    org_id = tenant["organization_id"]
    query = db.query(AIReportGeneration).filter(AIReportGeneration.organization_id == org_id)
    if report_type:
        query = query.filter(AIReportGeneration.report_type == report_type)
    reports = query.order_by(AIReportGeneration.created_at.desc()).limit(limit).all()
    return [
        {
            "id": r.id,
            "report_type": r.report_type,
            "title": r.title,
            "summary": r.summary,
            "created_at": str(r.created_at) if r.created_at else None,
        }
        for r in reports
    ]


@router.get("/reports/{report_id}")
async def get_report(
    report_id: int,
    db: DbSession = Depends(get_db),
    tenant: dict = Depends(get_tenant_context),
):
    """Get a specific AI-generated report."""
    org_id = tenant["organization_id"]
    report = verify_resource_ownership(db, AIReportGeneration, report_id, org_id)
    return {
        "id": report.id,
        "report_type": report.report_type,
        "title": report.title,
        "content": report.content,
        "summary": report.summary,
        "sections": report.sections,
        "format": report.format,
        "created_at": str(report.created_at) if report.created_at else None,
    }


@router.get("/reports/{report_id}/export")
async def export_report(
    report_id: int,
    format: str = Query("pdf", pattern="^(csv|excel|xlsx|pdf)$"),
    db: DbSession = Depends(get_db),
    tenant: dict = Depends(get_tenant_context),
):
    """Export an AI-generated report to CSV, Excel, or PDF."""
    org_id = tenant["organization_id"]
    report = verify_resource_ownership(db, AIReportGeneration, report_id, org_id)
    try:
        data, media_type, ext = ReportExportService().export(report, format)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return Response(
        content=data,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename=report_{report_id}.{ext}"},
    )


# --- AI Decision Center -----------------------------------------------------


@router.post("/decision/analyze", response_model=DecisionCenterResponse)
async def decision_analyze(
    request: DecisionCenterRequest,
    db: DbSession = Depends(get_db),
    tenant: dict = Depends(get_tenant_context),
):
    """Generate a decision intelligence analysis."""
    current_user = tenant["user"]
    engine = DecisionCenterEngine(db)
    result = engine.analyze(
        metric=request.metric,
        date_from=request.date_from,
        date_to=request.date_to,
        context=request.context,
        user_id=current_user["id"],
    )
    return DecisionCenterResponse(**result)


@router.get("/insights", response_model=list[InsightResponse])
async def list_insights(
    insight_type: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: DbSession = Depends(get_db),
    tenant: dict = Depends(get_tenant_context),
):
    """List AI-generated insights."""
    org_id = tenant["organization_id"]
    query = db.query(AIInsight).filter(AIInsight.organization_id == org_id)
    if insight_type:
        query = query.filter(AIInsight.insight_type == insight_type)
    insights = query.order_by(AIInsight.created_at.desc()).limit(limit).all()
    return [
        InsightResponse(
            id=i.id,
            title=i.title,
            insight_type=i.insight_type,
            summary=i.summary,
            key_findings=i.key_findings,
            recommendations=i.recommendations,
            risks=i.risks,
            opportunities=i.opportunities,
            confidence_score=i.confidence_score,
            data_sources=i.data_sources,
            created_at=str(i.created_at) if i.created_at else None,
        )
        for i in insights
    ]


# --- AI Forecasting ---------------------------------------------------------


@router.post("/forecast", response_model=ForecastResponse)
async def generate_forecast(
    request: ForecastRequest,
    db: DbSession = Depends(get_db),
    tenant: dict = Depends(get_tenant_context),
):
    """Generate a time series forecast."""
    current_user = tenant["user"]
    org_id = tenant["organization_id"]
    engine = ForecastingEngine(db)
    result = engine.forecast(
        source_type=request.source_type,
        source_config=request.source_config,
        target_column=request.target_column,
        date_column=request.date_column,
        horizon=request.horizon,
        frequency=request.frequency,
        confidence_level=request.confidence_level,
        user_id=current_user["id"],
        organization_id=org_id,
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return ForecastResponse(**{k: v for k, v in result.items() if k != "ai_interpretation"})


@router.get("/forecasts", response_model=list[dict])
async def list_forecasts(
    limit: int = Query(20, ge=1, le=100),
    db: DbSession = Depends(get_db),
    tenant: dict = Depends(get_tenant_context),
):
    """List forecasts."""
    org_id = tenant["organization_id"]
    forecasts = (
        db.query(AIForecast)
        .filter(AIForecast.organization_id == org_id)
        .order_by(AIForecast.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": f.id,
            "forecast_type": f.forecast_type,
            "target_column": f.target_column,
            "horizon": f.horizon,
            "method": f.method,
            "accuracy_score": f.accuracy_score,
            "created_at": str(f.created_at) if f.created_at else None,
        }
        for f in forecasts
    ]


@router.get("/forecasts/{forecast_id}")
async def get_forecast(
    forecast_id: int,
    db: DbSession = Depends(get_db),
    tenant: dict = Depends(get_tenant_context),
):
    """Get a specific forecast with predictions."""
    org_id = tenant["organization_id"]
    forecast = verify_resource_ownership(db, AIForecast, forecast_id, org_id)
    return {
        "id": forecast.id,
        "forecast_type": forecast.forecast_type,
        "target_column": forecast.target_column,
        "horizon": forecast.horizon,
        "method": forecast.method,
        "predictions": forecast.predictions,
        "accuracy_score": forecast.accuracy_score,
        "confidence_level": forecast.confidence_level,
        "input_summary": forecast.input_summary,
        "created_at": str(forecast.created_at) if forecast.created_at else None,
    }


# --- AI Anomaly Detection ---------------------------------------------------


@router.post("/anomaly/detect", response_model=AnomalyResponse)
async def detect_anomalies(
    request: AnomalyRequest,
    db: DbSession = Depends(get_db),
    tenant: dict = Depends(get_tenant_context),
):
    """Detect anomalies in data."""
    current_user = tenant["user"]
    org_id = tenant["organization_id"]
    engine = AnomalyDetectionEngine(db)
    result = engine.detect(
        source_type=request.source_type,
        source_config=request.source_config,
        metric_column=request.metric_column,
        date_column=request.date_column,
        sensitivity=request.sensitivity,
        user_id=current_user["id"],
        organization_id=org_id,
    )
    return AnomalyResponse(**result)


@router.get("/anomaly/alerts", response_model=list[dict])
async def list_alerts(
    is_resolved: bool = Query(False),
    limit: int = Query(50, ge=1, le=200),
    db: DbSession = Depends(get_db),
    tenant: dict = Depends(get_tenant_context),
):
    """List anomaly alerts."""
    org_id = tenant["organization_id"]
    alerts = (
        db.query(AIAnomalyAlert)
        .filter(
            AIAnomalyAlert.organization_id == org_id,
            AIAnomalyAlert.is_resolved == is_resolved,
        )
        .order_by(AIAnomalyAlert.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": a.id,
            "title": a.title,
            "description": a.description,
            "severity": a.severity,
            "metric": a.metric_name,
            "detected_value": a.actual_value,
            "expected_value": a.expected_value,
            "is_resolved": a.is_resolved,
            "created_at": str(a.created_at) if a.created_at else None,
        }
        for a in alerts
    ]


@router.post("/anomaly/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: int,
    db: DbSession = Depends(get_db),
    tenant: dict = Depends(get_tenant_context),
):
    """Resolve an anomaly alert."""
    current_user = tenant["user"]
    org_id = tenant["organization_id"]
    alert = verify_resource_ownership(db, AIAnomalyAlert, alert_id, org_id)
    alert.is_resolved = True
    alert.resolved_by = current_user["id"]
    db.commit()
    return {"message": "Alert resolved"}


# --- AI KPI Engine ----------------------------------------------------------


@router.post("/kpi/recommend", response_model=KPIRecommendResponse)
async def recommend_kpis(
    request: KPIRecommendRequest,
    db: DbSession = Depends(get_db),
    tenant: dict = Depends(get_tenant_context),
):
    """Get AI-recommended KPIs."""
    current_user = tenant["user"]
    org_id = tenant["organization_id"]
    engine = KPIEngine(db)
    result = engine.recommend_kpis(
        domain=request.domain,
        data_source=request.data_source,
        user_id=current_user["id"],
        organization_id=org_id,
    )
    return KPIRecommendResponse(**result)


@router.get("/kpi/monitor", response_model=KPIMonitorResponse)
async def monitor_kpis(
    db: DbSession = Depends(get_db),
    tenant: dict = Depends(get_tenant_context),
):
    """Monitor active KPIs and get alerts."""
    engine = KPIEngine(db)
    return engine.monitor_kpis()


# --- AI Dashboard Insights --------------------------------------------------


@router.post("/dashboard/insights", response_model=DashboardInsightsResponse)
async def generate_dashboard_insights(
    request: DashboardInsightsRequest,
    db: DbSession = Depends(get_db),
    tenant: dict = Depends(get_tenant_context),
):
    """Generate AI insights for a dashboard."""
    current_user = tenant["user"]
    engine = DashboardInsightsEngine(db)
    result = engine.generate_insights(
        dashboard_id=request.dashboard_id,
        data_source=request.data_source,
        context=request.context,
        user_id=current_user["id"],
    )
    return DashboardInsightsResponse(**result)


# --- AI Search --------------------------------------------------------------


@router.post("/search", response_model=AISearchResponse)
async def ai_search(
    request: AISearchRequest,
    db: DbSession = Depends(get_db),
    tenant: dict = Depends(get_tenant_context),
):
    """Global AI-powered search across the platform."""
    current_user = tenant["user"]
    engine = AISearchEngine(db)
    result = engine.search(
        query=request.query,
        search_type=request.search_type,
        user_id=current_user["id"],
    )
    return AISearchResponse(**result)


# --- AI Document Chat -------------------------------------------------------


@router.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: DbSession = Depends(get_db),
    tenant: dict = Depends(get_tenant_context),
):
    """Upload a document for AI chat."""
    current_user = tenant["user"]
    org_id = tenant["organization_id"]
    engine = DocumentChatEngine(db)
    content = await file.read()
    file_type = file.filename.split(".")[-1].lower() if "." in file.filename else "txt"
    try:
        result = engine.upload_document(
            filename=file.filename,
            file_content=content,
            file_type=file_type,
            user_id=current_user["id"],
            organization_id=org_id,
        )
        return DocumentUploadResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/documents/{document_id}/chat", response_model=DocumentChatResponse)
async def document_chat(
    document_id: int,
    request: DocumentChatRequest,
    db: DbSession = Depends(get_db),
    tenant: dict = Depends(get_tenant_context),
):
    """Chat with an uploaded document."""
    current_user = tenant["user"]
    org_id = tenant["organization_id"]
    engine = DocumentChatEngine(db)
    result = engine.chat(
        document_id=document_id,
        question=request.question,
        user_id=current_user["id"],
        organization_id=org_id,
    )
    return DocumentChatResponse(**result)


@router.get("/documents", response_model=list[dict])
async def list_documents(
    db: DbSession = Depends(get_db),
    tenant: dict = Depends(get_tenant_context),
):
    """List uploaded documents."""
    current_user = tenant["user"]
    org_id = tenant["organization_id"]
    engine = DocumentChatEngine(db)
    return engine.list_documents(current_user["id"], org_id)


# --- AI Workflow ------------------------------------------------------------


@router.post("/workflows", response_model=WorkflowResponse)
async def create_workflow(
    request: WorkflowCreate,
    db: DbSession = Depends(get_db),
    tenant: dict = Depends(get_tenant_context),
):
    """Create a new AI workflow."""
    current_user = tenant["user"]
    org_id = tenant["organization_id"]
    engine = WorkflowEngine(db)
    result = engine.create_workflow(
        name=request.name,
        steps=request.steps,
        description=request.description,
        trigger_type=request.trigger_type,
        trigger_config=request.trigger_config,
        user_id=current_user["id"],
        organization_id=org_id,
    )
    return WorkflowResponse(**result)


@router.get("/workflows", response_model=list[WorkflowResponse])
async def list_workflows(
    db: DbSession = Depends(get_db),
    tenant: dict = Depends(get_tenant_context),
):
    """List AI workflows."""
    org_id = tenant["organization_id"]
    workflows = (
        db.query(AIWorkflow)
        .filter(AIWorkflow.organization_id == org_id)
        .order_by(AIWorkflow.created_at.desc())
        .all()
    )
    return [
        WorkflowResponse(
            id=w.id,
            name=w.name,
            description=w.description,
            trigger_type=w.trigger_type,
            is_active=w.is_active,
            created_at=str(w.created_at) if w.created_at else None,
        )
        for w in workflows
    ]


@router.post("/workflows/{workflow_id}/execute", response_model=WorkflowRunResponse)
async def execute_workflow(
    workflow_id: int,
    db: DbSession = Depends(get_db),
    tenant: dict = Depends(get_tenant_context),
):
    """Execute an AI workflow."""
    current_user = tenant["user"]
    org_id = tenant["organization_id"]
    verify_resource_ownership(db, AIWorkflow, workflow_id, org_id)
    engine = WorkflowEngine(db)
    result = engine.execute_workflow(workflow_id, current_user["id"])
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return WorkflowRunResponse(**result)


@router.get("/workflows/{workflow_id}/runs", response_model=list[WorkflowRunResponse])
async def get_workflow_runs(
    workflow_id: int,
    limit: int = Query(20, ge=1, le=100),
    db: DbSession = Depends(get_db),
    tenant: dict = Depends(get_tenant_context),
):
    """Get execution history for a workflow."""
    org_id = tenant["organization_id"]
    verify_resource_ownership(db, AIWorkflow, workflow_id, org_id)
    engine = WorkflowEngine(db)
    return engine.get_workflow_runs(workflow_id, limit)


# --- AI Prompt Templates ----------------------------------------------------


@router.get("/prompts", response_model=list[PromptTemplateResponse])
async def list_prompt_templates(
    assistant_type: str | None = Query(None),
    db: DbSession = Depends(get_db),
    tenant: dict = Depends(get_tenant_context),
):
    """List prompt templates."""
    query = db.query(AIPromptTemplate)
    if assistant_type:
        query = query.filter(AIPromptTemplate.assistant_type == assistant_type)
    templates = query.order_by(AIPromptTemplate.created_at.desc()).all()
    return [
        PromptTemplateResponse(
            id=t.id,
            name=t.name,
            assistant_type=t.assistant_type,
            system_prompt=t.system_prompt,
            description=t.description,
            variables=t.variables,
            is_active=t.is_active,
            is_system=t.is_system,
            created_at=str(t.created_at) if t.created_at else None,
        )
        for t in templates
    ]


@router.post("/prompts", response_model=PromptTemplateResponse)
async def create_prompt_template(
    request: PromptTemplateCreate,
    db: DbSession = Depends(get_db),
    tenant: dict = Depends(get_tenant_context),
):
    """Create a custom prompt template."""
    manager = PromptManager(db)
    template = manager.create_custom_prompt(
        name=request.name,
        assistant_type=request.assistant_type,
        system_prompt=request.system_prompt,
        description=request.description,
        variables=request.variables,
    )
    return PromptTemplateResponse(
        id=template.id,
        name=template.name,
        assistant_type=template.assistant_type,
        system_prompt=template.system_prompt,
        description=template.description,
        variables=template.variables,
        is_active=template.is_active,
        is_system=template.is_system,
        created_at=str(template.created_at) if template.created_at else None,
    )


# --- AI Usage & Audit -------------------------------------------------------


@router.get("/usage/stats", response_model=UsageStatsResponse)
async def usage_stats(
    days: int = Query(30, ge=1, le=365),
    db: DbSession = Depends(get_db),
    tenant: dict = Depends(get_tenant_context),
):
    """Get AI usage statistics."""
    tracker = UsageTracker(db)
    return UsageStatsResponse(**tracker.get_stats(days))


@router.get("/usage/me")
async def my_usage(
    days: int = Query(30, ge=1, le=365),
    db: DbSession = Depends(get_db),
    tenant: dict = Depends(get_tenant_context),
):
    """Get current user's AI usage."""
    current_user = tenant["user"]
    tracker = UsageTracker(db)
    return tracker.get_user_usage(current_user["id"], days)


@router.get("/usage/limits")
async def usage_limits(
    db: DbSession = Depends(get_db),
    tenant: dict = Depends(get_tenant_context),
):
    """Check usage limits for the current user."""
    current_user = tenant["user"]
    tracker = UsageTracker(db)
    return tracker.check_limits(current_user["id"])


@router.get("/audit/logs", response_model=list[AuditLogResponse])
async def audit_logs(
    limit: int = Query(50, ge=1, le=200),
    db: DbSession = Depends(get_db),
    tenant: dict = Depends(get_tenant_context),
):
    """Get AI audit logs."""
    org_id = tenant["organization_id"]
    logs = (
        db.query(AIAuditLog)
        .filter(AIAuditLog.organization_id == org_id)
        .order_by(AIAuditLog.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        AuditLogResponse(
            id=log.id,
            user_id=log.user_id,
            action=log.action,
            assistant_type=log.assistant_type,
            input_summary=log.input_summary,
            output_summary=log.output_summary,
            success=log.success,
            error_message=log.error_message,
            created_at=str(log.created_at) if log.created_at else None,
        )
        for log in logs
    ]


# --- AI Plugins -------------------------------------------------------------


@router.get("/plugins", response_model=list[PluginResponse])
async def list_plugins(
    plugin_type: str | None = Query(None),
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List AI plugins."""
    registry = PluginRegistry(db)
    return registry.list_plugins(plugin_type)


@router.post("/plugins/{plugin_id}/activate")
async def activate_plugin(
    plugin_id: int,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Activate an AI plugin."""
    registry = PluginRegistry(db)
    if not registry.activate_plugin(plugin_id):
        raise HTTPException(status_code=400, detail="Failed to activate plugin")
    return {"message": "Plugin activated"}


@router.post("/plugins/{plugin_id}/deactivate")
async def deactivate_plugin(
    plugin_id: int,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Deactivate an AI plugin."""
    registry = PluginRegistry(db)
    if not registry.deactivate_plugin(plugin_id):
        raise HTTPException(status_code=404, detail="Plugin not found")
    return {"message": "Plugin deactivated"}


# --- AI Dashboard -----------------------------------------------------------


@router.get("/dashboard", response_model=AIDashboardResponse)
async def ai_dashboard(
    db: DbSession = Depends(get_db),
    tenant: dict = Depends(get_tenant_context),
):
    """Get AI platform dashboard metrics."""
    org_id = tenant["organization_id"]
    tracker = UsageTracker(db)
    stats = tracker.get_stats(30)

    total_conversations = (
        db.query(AIConversation).filter(AIConversation.organization_id == org_id).count()
    )
    total_messages = (
        db.query(AIMessage)
        .join(AIConversation, AIMessage.conversation_id == AIConversation.id)
        .filter(AIConversation.organization_id == org_id, AIMessage.role != "system")
        .count()
    )
    active_workflows = (
        db.query(AIWorkflow)
        .filter(AIWorkflow.organization_id == org_id, AIWorkflow.is_active.is_(True))
        .count()
    )
    total_insights = (
        db.query(AIInsight)
        .filter(AIInsight.organization_id == org_id, AIInsight.is_archived.is_(False))
        .count()
    )
    total_forecasts = db.query(AIForecast).filter(AIForecast.organization_id == org_id).count()
    active_alerts = (
        db.query(AIAnomalyAlert)
        .filter(AIAnomalyAlert.organization_id == org_id, AIAnomalyAlert.is_resolved.is_(False))
        .count()
    )

    # Provider status
    manager = ProviderManager(db)
    provider_status = manager.list_providers()

    # Recent insights
    recent_insights = (
        db.query(AIInsight)
        .filter(AIInsight.organization_id == org_id, AIInsight.is_archived.is_(False))
        .order_by(AIInsight.created_at.desc())
        .limit(5)
        .all()
    )
    recent_insights_data = [
        {
            "id": i.id,
            "title": i.title,
            "type": i.insight_type,
            "created_at": str(i.created_at) if i.created_at else None,
        }
        for i in recent_insights
    ]

    # Recent alerts
    recent_alerts = (
        db.query(AIAnomalyAlert)
        .filter(AIAnomalyAlert.organization_id == org_id, AIAnomalyAlert.is_resolved.is_(False))
        .order_by(AIAnomalyAlert.created_at.desc())
        .limit(5)
        .all()
    )
    recent_alerts_data = [
        {
            "id": a.id,
            "title": a.title,
            "severity": a.severity,
            "created_at": str(a.created_at) if a.created_at else None,
        }
        for a in recent_alerts
    ]

    return AIDashboardResponse(
        total_conversations=total_conversations,
        total_messages=total_messages,
        total_tokens_used=stats["total_tokens"],
        total_cost_usd=stats["total_cost_usd"],
        active_workflows=active_workflows,
        total_insights=total_insights,
        total_forecasts=total_forecasts,
        active_alerts=active_alerts,
        provider_status=provider_status,
        recent_insights=recent_insights_data,
        recent_alerts=recent_alerts_data,
    )


# --- AI Productivity Extensions ----------------------------------------------


@router.post("/explain/chart", response_model=ExplainChartResponse)
async def explain_chart(
    body: ExplainChartRequest,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Explain a chart or visualization in plain English.

    Accepts chart type, data summary, and context to generate
    a human-readable explanation of what the chart shows.
    """
    chart_type = body.chart_type
    title = body.title
    data_summary = body.data_summary
    context = body.context

    prompt = (
        f"Explain this {chart_type} chart titled '{title}' in plain English. "
        f"Data summary: {data_summary}. Context: {context}. "
        "Describe what trends, patterns, or outliers are visible and what they mean for the business."
    )

    memory = AIMemory(db)
    gateway = AIGateway(db, memory=memory)
    try:
        response = gateway.chat(
            user_message=prompt,
            assistant_type="data_analyst",
            user_id=current_user["id"],
        )
        return ExplainChartResponse(
            explanation=response.get("response", ""),
            chart_type=chart_type,
        )
    except Exception as e:
        return ExplainChartResponse(
            explanation=f"Unable to generate explanation: {e}",
            chart_type=chart_type,
        )


@router.post("/explain/etl-failure/{job_id}", response_model=ExplainETLFailureResponse)
async def explain_etl_failure(
    job_id: int,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Explain why an ETL job failed and suggest fixes."""
    from etl.models import ETLJob

    job = db.query(ETLJob).filter(ETLJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="ETL job not found")

    error_detail = job.error_message or "No error message recorded"
    prompt = (
        f"An ETL job (pipeline_id={job.pipeline_id}, type={job.job_type}) "
        f"failed with status '{job.status}'. "
        f"Error: {error_detail}. "
        "Explain what likely went wrong and suggest specific steps to fix it."
    )

    memory = AIMemory(db)
    gateway = AIGateway(db, memory=memory)
    try:
        response = gateway.chat(
            user_message=prompt,
            assistant_type="etl_assistant",
            user_id=current_user["id"],
        )
        return ExplainETLFailureResponse(
            job_id=job_id,
            explanation=response.get("response", ""),
            suggested_fixes=[],
        )
    except Exception as e:
        return ExplainETLFailureResponse(
            job_id=job_id,
            explanation=f"Unable to analyze: {e}",
            suggested_fixes=[],
        )


@router.post("/reports/summarize", response_model=SummarizeReportResponse)
async def summarize_report(
    body: SummarizeReportRequest,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Summarize a report or data extract into key findings."""
    report_content = body.content
    report_type = body.report_type
    max_points = body.max_points

    prompt = (
        f"Summarize this {report_type} report into {max_points} key findings. "
        f"Be concise and actionable. Report content: {report_content[:4000]}"
    )

    memory = AIMemory(db)
    gateway = AIGateway(db, memory=memory)
    try:
        response = gateway.chat(
            user_message=prompt,
            assistant_type="data_analyst",
            user_id=current_user["id"],
        )
        summary_text = response.get("response", "")
        key_findings = [
            line.strip().lstrip("0123456789.-) ")
            for line in summary_text.split("\n")
            if line.strip() and len(line.strip()) > 10
        ][:max_points]
        return SummarizeReportResponse(summary=summary_text, key_findings=key_findings)
    except Exception as e:
        return SummarizeReportResponse(summary=f"Unable to summarize: {e}", key_findings=[])


@router.post("/recommend/actions", response_model=RecommendActionsResponse)
async def recommend_actions(
    body: RecommendActionsRequest,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Recommend actions based on data analysis context."""
    context = body.context
    data_summary = body.data_summary

    prompt = (
        f"Based on this data context: {data_summary}. "
        f"Additional context: {context}. "
        "Recommend 3-5 specific, actionable next steps the user should take. "
        "Format as a numbered list with brief explanations."
    )

    memory = AIMemory(db)
    gateway = AIGateway(db, memory=memory)
    try:
        response = gateway.chat(
            user_message=prompt,
            assistant_type="data_analyst",
            user_id=current_user["id"],
        )
        recommendations_text = response.get("response", "")
        recommendations = [
            line.strip().lstrip("0123456789.-) ")
            for line in recommendations_text.split("\n")
            if line.strip() and len(line.strip()) > 10
        ][:5]
        return RecommendActionsResponse(
            recommendations=recommendations,
            full_response=recommendations_text,
        )
    except Exception as e:
        return RecommendActionsResponse(
            recommendations=[],
            full_response=f"Unable to generate recommendations: {e}",
        )
