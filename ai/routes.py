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

from datetime import datetime
from typing import Optional
import json

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session as DbSession

from shared.database import get_db
from shared.dependencies import get_current_user
from ai.gateway import AIGateway
from ai.assistants.assistants import list_assistants, get_assistant
from ai.memory import AIMemory
from ai.usage import UsageTracker
from ai.providers.manager import ProviderManager
from ai.prompts.templates import PromptManager
from ai.plugins import PluginRegistry, register_system_plugins
from ai.engines.nl_to_sql import NLToSQLEngine
from ai.engines.nl_to_etl import NLToETLEngine
from ai.engines.nl_to_dashboard import NLToDashboardEngine
from ai.engines.ai_quality import AIDataQualityEngine
from ai.engines.report_writer import AIReportWriter
from ai.engines.decision_center import DecisionCenterEngine
from ai.engines.forecasting import ForecastingEngine
from ai.engines.anomaly_detection import AnomalyDetectionEngine
from ai.engines.kpi_engine import KPIEngine
from ai.engines.dashboard_insights import DashboardInsightsEngine
from ai.engines.ai_search import AISearchEngine
from ai.engines.document_chat import DocumentChatEngine
from ai.workflow import WorkflowEngine
from ai.models import (
    AIConversation, AIMessage, AIProviderConfig, AIUsageLog, AIAuditLog,
    AIWorkflow, AIWorkflowRun, AIInsight, AIForecast, AIAnomalyAlert,
    AIDocument, AIKPIRecommendation, AIReportGeneration, AIPromptTemplate,
    AIPlugin,
)
from ai.schemas import (
    ChatRequest, ChatResponse, ConversationSummary, MessageSummary,
    ProviderConfigCreate, ProviderConfigUpdate, ProviderConfigResponse,
    NLToSQLRequest, NLToSQLResponse,
    NLToETLRequest, NLToETLResponse,
    NLToDashboardRequest, NLToDashboardResponse,
    AIQualityRequest, AIQualityResponse,
    ReportGenerateRequest, ReportGenerateResponse,
    DecisionCenterRequest, DecisionCenterResponse,
    ForecastRequest, ForecastResponse,
    AnomalyRequest, AnomalyResponse,
    KPIRecommendRequest, KPIRecommendResponse, KPIMonitorResponse,
    DashboardInsightsRequest, DashboardInsightsResponse,
    AISearchRequest, AISearchResponse,
    DocumentUploadResponse, DocumentChatRequest, DocumentChatResponse,
    WorkflowCreate, WorkflowResponse, WorkflowRunResponse,
    InsightResponse,
    PromptTemplateCreate, PromptTemplateResponse,
    UsageStatsResponse, AuditLogResponse,
    PluginResponse,
    AIDashboardResponse,
    MessageFeedbackRequest,
)
from ai.config import (
    AI_DEFAULT_PROVIDER, AI_DEFAULT_MODEL, AI_MAX_TOKENS, AI_TEMPERATURE,
    AI_STREAM_ENABLED,
)

router = APIRouter(prefix="/ai", tags=["AI Intelligence Platform"])


# --- AI Chat ----------------------------------------------------------------

@router.post("/chat", response_model=ChatResponse)
async def ai_chat(
    request: ChatRequest,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Send a message to an AI assistant and get a response."""
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
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI request failed: {str(e)}")


@router.post("/chat/stream")
async def ai_chat_stream(
    request: ChatRequest,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Stream a chat response from an AI assistant."""
    from fastapi.responses import StreamingResponse

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
        )
        return StreamingResponse(
            generator,
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- Conversations ----------------------------------------------------------

@router.get("/conversations", response_model=list[ConversationSummary])
async def list_conversations(
    assistant_type: Optional[str] = Query(None),
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List user's AI conversations."""
    memory = AIMemory(db)
    return memory.get_conversations(current_user["id"], assistant_type)


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageSummary])
async def get_conversation_messages(
    conversation_id: int,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get all messages in a conversation."""
    memory = AIMemory(db)
    messages = memory.get_conversation_messages(conversation_id)
    if not messages:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return messages


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: int,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Delete (archive) a conversation."""
    memory = AIMemory(db)
    if not memory.delete_conversation(conversation_id):
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"message": "Conversation archived"}


@router.post("/messages/{message_id}/feedback")
async def message_feedback(
    message_id: int,
    request: MessageFeedbackRequest,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Provide feedback (positive/negative) on an AI message."""
    memory = AIMemory(db)
    if not memory.set_feedback(message_id, request.feedback):
        raise HTTPException(status_code=404, detail="Message not found")
    return {"message": "Feedback recorded"}


# --- AI Assistants ----------------------------------------------------------

@router.get("/assistants")
async def list_all_assistants():
    """List all available AI assistants."""
    return list_assistants()


# --- Provider Management ----------------------------------------------------

@router.get("/providers")
async def list_providers(
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List all AI providers and their status."""
    manager = ProviderManager(db)
    return manager.list_providers()


@router.post("/providers", response_model=ProviderConfigResponse)
async def create_provider(
    config: ProviderConfigCreate,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Configure a new AI provider."""
    existing = db.query(AIProviderConfig).filter(
        AIProviderConfig.provider_name == config.provider_name
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Provider already configured")

    provider = AIProviderConfig(
        provider_name=config.provider_name,
        display_name=config.display_name,
        api_key_encrypted=config.api_key,
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
    current_user: dict = Depends(get_current_user),
):
    """Update an AI provider configuration."""
    provider = db.query(AIProviderConfig).filter(AIProviderConfig.id == provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    if config.display_name is not None:
        provider.display_name = config.display_name
    if config.api_key is not None:
        provider.api_key_encrypted = config.api_key
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
            db.query(AIProviderConfig).filter(
                AIProviderConfig.is_default == True
            ).update({AIProviderConfig.is_default: False})
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
    current_user: dict = Depends(get_current_user),
):
    """Test a provider connection."""
    manager = ProviderManager(db)
    return manager.test_provider(provider_name)


# --- NL to SQL --------------------------------------------------------------

@router.post("/sql/generate", response_model=NLToSQLResponse)
async def generate_sql(
    request: NLToSQLRequest,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Generate SQL from a natural language question."""
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
    current_user: dict = Depends(get_current_user),
):
    """Execute a validated SQL query safely."""
    engine = NLToSQLEngine(db)
    return engine.execute_sql(sql, limit)


# --- NL to ETL --------------------------------------------------------------

@router.post("/etl/generate", response_model=NLToETLResponse)
async def generate_etl(
    request: NLToETLRequest,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Generate ETL pipeline steps from natural language."""
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
    current_user: dict = Depends(get_current_user),
):
    """Generate a dashboard configuration from a description."""
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
    current_user: dict = Depends(get_current_user),
):
    """Analyze data quality with AI enhancement."""
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
    current_user: dict = Depends(get_current_user),
):
    """Generate an AI-powered report."""
    engine = AIReportWriter(db)
    result = engine.generate_report(
        report_type=request.report_type,
        title=request.title,
        date_from=request.date_from,
        date_to=request.date_to,
        department=request.department,
        format=request.format,
        user_id=current_user["id"],
    )
    return ReportGenerateResponse(**result)


@router.get("/reports", response_model=list[dict])
async def list_reports(
    report_type: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List AI-generated reports."""
    query = db.query(AIReportGeneration)
    if report_type:
        query = query.filter(AIReportGeneration.report_type == report_type)
    reports = query.order_by(AIReportGeneration.created_at.desc()).limit(limit).all()
    return [
        {
            "id": r.id, "report_type": r.report_type, "title": r.title,
            "summary": r.summary, "created_at": str(r.created_at) if r.created_at else None,
        }
        for r in reports
    ]


@router.get("/reports/{report_id}")
async def get_report(
    report_id: int,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get a specific AI-generated report."""
    report = db.query(AIReportGeneration).filter(AIReportGeneration.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return {
        "id": report.id, "report_type": report.report_type, "title": report.title,
        "content": report.content, "summary": report.summary,
        "sections": report.sections, "format": report.format,
        "created_at": str(report.created_at) if report.created_at else None,
    }


# --- AI Decision Center -----------------------------------------------------

@router.post("/decision/analyze", response_model=DecisionCenterResponse)
async def decision_analyze(
    request: DecisionCenterRequest,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Generate a decision intelligence analysis."""
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
    insight_type: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List AI-generated insights."""
    engine = DecisionCenterEngine(db)
    return engine.get_insights(insight_type, limit)


# --- AI Forecasting ---------------------------------------------------------

@router.post("/forecast", response_model=ForecastResponse)
async def generate_forecast(
    request: ForecastRequest,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Generate a time series forecast."""
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
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return ForecastResponse(**{k: v for k, v in result.items() if k != "ai_interpretation"})


@router.get("/forecasts", response_model=list[dict])
async def list_forecasts(
    limit: int = Query(20, ge=1, le=100),
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List forecasts."""
    forecasts = db.query(AIForecast).order_by(AIForecast.created_at.desc()).limit(limit).all()
    return [
        {
            "id": f.id, "forecast_type": f.forecast_type,
            "target_column": f.target_column, "horizon": f.horizon,
            "method": f.method, "accuracy_score": f.accuracy_score,
            "created_at": str(f.created_at) if f.created_at else None,
        }
        for f in forecasts
    ]


@router.get("/forecasts/{forecast_id}")
async def get_forecast(
    forecast_id: int,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get a specific forecast with predictions."""
    forecast = db.query(AIForecast).filter(AIForecast.id == forecast_id).first()
    if not forecast:
        raise HTTPException(status_code=404, detail="Forecast not found")
    return {
        "id": forecast.id, "forecast_type": forecast.forecast_type,
        "target_column": forecast.target_column, "horizon": forecast.horizon,
        "method": forecast.method, "predictions": forecast.predictions,
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
    current_user: dict = Depends(get_current_user),
):
    """Detect anomalies in data."""
    engine = AnomalyDetectionEngine(db)
    result = engine.detect(
        source_type=request.source_type,
        source_config=request.source_config,
        metric_column=request.metric_column,
        date_column=request.date_column,
        sensitivity=request.sensitivity,
        user_id=current_user["id"],
    )
    return AnomalyResponse(**result)


@router.get("/anomaly/alerts", response_model=list[dict])
async def list_alerts(
    is_resolved: bool = Query(False),
    limit: int = Query(50, ge=1, le=200),
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List anomaly alerts."""
    engine = AnomalyDetectionEngine(db)
    return engine.get_alerts(is_resolved, limit)


@router.post("/anomaly/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: int,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Resolve an anomaly alert."""
    engine = AnomalyDetectionEngine(db)
    if not engine.resolve_alert(alert_id, current_user["id"]):
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"message": "Alert resolved"}


# --- AI KPI Engine ----------------------------------------------------------

@router.post("/kpi/recommend", response_model=KPIRecommendResponse)
async def recommend_kpis(
    request: KPIRecommendRequest,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get AI-recommended KPIs."""
    engine = KPIEngine(db)
    result = engine.recommend_kpis(
        domain=request.domain,
        data_source=request.data_source,
        user_id=current_user["id"],
    )
    return KPIRecommendResponse(**result)


@router.get("/kpi/monitor", response_model=KPIMonitorResponse)
async def monitor_kpis(
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Monitor active KPIs and get alerts."""
    engine = KPIEngine(db)
    return engine.monitor_kpis()


# --- AI Dashboard Insights --------------------------------------------------

@router.post("/dashboard/insights", response_model=DashboardInsightsResponse)
async def generate_dashboard_insights(
    request: DashboardInsightsRequest,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Generate AI insights for a dashboard."""
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
    current_user: dict = Depends(get_current_user),
):
    """Global AI-powered search across the platform."""
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
    current_user: dict = Depends(get_current_user),
):
    """Upload a document for AI chat."""
    engine = DocumentChatEngine(db)
    content = await file.read()
    file_type = file.filename.split(".")[-1].lower() if "." in file.filename else "txt"
    try:
        result = engine.upload_document(
            filename=file.filename,
            file_content=content,
            file_type=file_type,
            user_id=current_user["id"],
        )
        return DocumentUploadResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/documents/{document_id}/chat", response_model=DocumentChatResponse)
async def document_chat(
    document_id: int,
    request: DocumentChatRequest,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Chat with an uploaded document."""
    engine = DocumentChatEngine(db)
    result = engine.chat(
        document_id=document_id,
        question=request.question,
        user_id=current_user["id"],
    )
    return DocumentChatResponse(**result)


@router.get("/documents", response_model=list[dict])
async def list_documents(
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List uploaded documents."""
    engine = DocumentChatEngine(db)
    return engine.list_documents(current_user["id"])


# --- AI Workflow ------------------------------------------------------------

@router.post("/workflows", response_model=WorkflowResponse)
async def create_workflow(
    request: WorkflowCreate,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Create a new AI workflow."""
    engine = WorkflowEngine(db)
    result = engine.create_workflow(
        name=request.name,
        steps=request.steps,
        description=request.description,
        trigger_type=request.trigger_type,
        trigger_config=request.trigger_config,
        user_id=current_user["id"],
    )
    return WorkflowResponse(**result)


@router.get("/workflows", response_model=list[WorkflowResponse])
async def list_workflows(
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List AI workflows."""
    engine = WorkflowEngine(db)
    return engine.list_workflows(current_user["id"])


@router.post("/workflows/{workflow_id}/execute", response_model=WorkflowRunResponse)
async def execute_workflow(
    workflow_id: int,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Execute an AI workflow."""
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
    current_user: dict = Depends(get_current_user),
):
    """Get execution history for a workflow."""
    engine = WorkflowEngine(db)
    return engine.get_workflow_runs(workflow_id, limit)


# --- AI Prompt Templates ----------------------------------------------------

@router.get("/prompts", response_model=list[PromptTemplateResponse])
async def list_prompt_templates(
    assistant_type: Optional[str] = Query(None),
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List prompt templates."""
    query = db.query(AIPromptTemplate)
    if assistant_type:
        query = query.filter(AIPromptTemplate.assistant_type == assistant_type)
    templates = query.order_by(AIPromptTemplate.created_at.desc()).all()
    return [
        PromptTemplateResponse(
            id=t.id, name=t.name, assistant_type=t.assistant_type,
            system_prompt=t.system_prompt, description=t.description,
            variables=t.variables, is_active=t.is_active, is_system=t.is_system,
            created_at=str(t.created_at) if t.created_at else None,
        )
        for t in templates
    ]


@router.post("/prompts", response_model=PromptTemplateResponse)
async def create_prompt_template(
    request: PromptTemplateCreate,
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
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
        id=template.id, name=template.name, assistant_type=template.assistant_type,
        system_prompt=template.system_prompt, description=template.description,
        variables=template.variables, is_active=template.is_active,
        is_system=template.is_system,
        created_at=str(template.created_at) if template.created_at else None,
    )


# --- AI Usage & Audit -------------------------------------------------------

@router.get("/usage/stats", response_model=UsageStatsResponse)
async def usage_stats(
    days: int = Query(30, ge=1, le=365),
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get AI usage statistics."""
    tracker = UsageTracker(db)
    return UsageStatsResponse(**tracker.get_stats(days))


@router.get("/usage/me")
async def my_usage(
    days: int = Query(30, ge=1, le=365),
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get current user's AI usage."""
    tracker = UsageTracker(db)
    return tracker.get_user_usage(current_user["id"], days)


@router.get("/usage/limits")
async def usage_limits(
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Check usage limits for the current user."""
    tracker = UsageTracker(db)
    return tracker.check_limits(current_user["id"])


@router.get("/audit/logs", response_model=list[AuditLogResponse])
async def audit_logs(
    limit: int = Query(50, ge=1, le=200),
    db: DbSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get AI audit logs."""
    logs = db.query(AIAuditLog).order_by(AIAuditLog.created_at.desc()).limit(limit).all()
    return [
        AuditLogResponse(
            id=l.id, user_id=l.user_id, action=l.action,
            assistant_type=l.assistant_type,
            input_summary=l.input_summary, output_summary=l.output_summary,
            success=l.success, error_message=l.error_message,
            created_at=str(l.created_at) if l.created_at else None,
        )
        for l in logs
    ]


# --- AI Plugins -------------------------------------------------------------

@router.get("/plugins", response_model=list[PluginResponse])
async def list_plugins(
    plugin_type: Optional[str] = Query(None),
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
    current_user: dict = Depends(get_current_user),
):
    """Get AI platform dashboard metrics."""
    tracker = UsageTracker(db)
    stats = tracker.get_stats(30)

    total_conversations = db.query(AIConversation).count()
    total_messages = db.query(AIMessage).filter(AIMessage.role != "system").count()
    active_workflows = db.query(AIWorkflow).filter(AIWorkflow.is_active == True).count()
    total_insights = db.query(AIInsight).filter(AIInsight.is_archived == False).count()
    total_forecasts = db.query(AIForecast).count()
    active_alerts = db.query(AIAnomalyAlert).filter(AIAnomalyAlert.is_resolved == False).count()

    # Provider status
    manager = ProviderManager(db)
    provider_status = manager.list_providers()

    # Recent insights
    recent_insights = db.query(AIInsight).filter(
        AIInsight.is_archived == False
    ).order_by(AIInsight.created_at.desc()).limit(5).all()
    recent_insights_data = [
        {"id": i.id, "title": i.title, "type": i.insight_type,
         "created_at": str(i.created_at) if i.created_at else None}
        for i in recent_insights
    ]

    # Recent alerts
    recent_alerts = db.query(AIAnomalyAlert).filter(
        AIAnomalyAlert.is_resolved == False
    ).order_by(AIAnomalyAlert.created_at.desc()).limit(5).all()
    recent_alerts_data = [
        {"id": a.id, "title": a.title, "severity": a.severity,
         "created_at": str(a.created_at) if a.created_at else None}
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
