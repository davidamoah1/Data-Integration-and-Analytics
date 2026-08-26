"""FastAPI routes for Enterprise AI Decision Support System.

Endpoints:
  - Executive Summary generation
  - Root Cause Analysis
  - Enterprise Forecasting
  - Enterprise Anomaly Detection
  - Recommendation Engine
  - Natural Language Analytics
  - Report Generation
  - Task Types listing
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session as DbSession

from ai.engines.enterprise_anomaly import EnterpriseAnomalyEngine
from ai.engines.enterprise_forecast import EnterpriseForecastEngine
from ai.engines.enterprise_report import EnterpriseReportEngine
from ai.engines.executive_summary import ExecutiveSummaryEngine
from ai.engines.nl_analytics import NLAnalyticsEngine
from ai.engines.recommendation_engine import RecommendationEngine
from ai.engines.root_cause import RootCauseAnalysisEngine
from ai.prompt_orchestrator import PromptOrchestrator
from shared.database import get_db
from shared.dependencies import get_current_user
from shared.tenant import get_current_organization_id

router = APIRouter(prefix="/ai/enterprise", tags=["Enterprise AI Decision Support"])


# â”€â”€ Request/Response Schemas â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


class ExecutiveSummaryRequest(BaseModel):
    dataset_id: str | None = None
    industry: str = "unknown"
    user_message: str = "What happened this month?"


class RootCauseRequest(BaseModel):
    question: str
    dataset_id: str | None = None
    industry: str = "unknown"


class ForecastRequest(BaseModel):
    metric: str = "revenue"
    dataset_id: str | None = None
    industry: str = "unknown"
    horizon: str | int = "medium"
    frequency: str = "D"
    confidence_level: float = 0.95
    method: str = "auto"


class AnomalyRequest(BaseModel):
    metric: str = "revenue"
    dataset_id: str | None = None
    industry: str = "unknown"
    sensitivity: float | None = None


class RecommendationRequest(BaseModel):
    dataset_id: str | None = None
    industry: str = "unknown"
    user_message: str = "What should I do?"


class NLAnalyticsRequest(BaseModel):
    question: str
    dataset_id: str | None = None
    industry: str = "unknown"


class ReportRequest(BaseModel):
    report_type: str = "executive"
    title: str | None = None
    dataset_id: str | None = None
    industry: str = "unknown"
    format: str = "markdown"


class TaskTypeResponse(BaseModel):
    task_types: list[dict] = Field(default_factory=list)


# â”€â”€ Endpoints â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


@router.post("/executive-summary")
def generate_executive_summary(
    request: ExecutiveSummaryRequest,
    db: DbSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """Generate an executive summary from the current dataset."""
    engine = ExecutiveSummaryEngine(db)
    return engine.generate(
        user_message=request.user_message,
        industry=request.industry,
        user_id=user.id if user else None,
    )


@router.post("/root-cause")
def analyze_root_cause(
    request: RootCauseRequest,
    db: DbSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """Perform root cause analysis on a metric change."""
    engine = RootCauseAnalysisEngine(db)
    return engine.analyze(
        question=request.question,
        industry=request.industry,
        user_id=user.id if user else None,
    )


@router.post("/forecast")
def generate_forecast(
    request: ForecastRequest,
    db: DbSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """Generate a forecast for a metric."""
    engine = EnterpriseForecastEngine(db)
    return engine.forecast(
        metric=request.metric,
        industry=request.industry,
        horizon=request.horizon,
        frequency=request.frequency,
        confidence_level=request.confidence_level,
        method=request.method,
        user_id=user.id if user else None,
    )


@router.post("/anomaly")
def detect_anomalies(
    request: AnomalyRequest,
    db: DbSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """Detect anomalies in a metric."""
    engine = EnterpriseAnomalyEngine(db)
    return engine.detect(
        metric=request.metric,
        industry=request.industry,
        sensitivity=request.sensitivity,
        user_id=user.id if user else None,
    )


@router.post("/recommendations")
def get_recommendations(
    request: RecommendationRequest,
    db: DbSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """Generate actionable recommendations."""
    engine = RecommendationEngine(db)
    return engine.generate(
        industry=request.industry,
        user_id=user.id if user else None,
        user_message=request.user_message,
    )


@router.post("/nl-analytics")
def analyze_natural_language(
    request: NLAnalyticsRequest,
    db: DbSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """Analyze a natural language question."""
    engine = NLAnalyticsEngine(db)
    return engine.analyze(
        question=request.question,
        industry=request.industry,
        user_id=user.id if user else None,
    )


@router.post("/report")
def generate_report(
    request: ReportRequest,
    db: DbSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """Generate a professional report."""
    org_id = get_current_organization_id(user, db)
    engine = EnterpriseReportEngine(db)
    return engine.generate(
        report_type=request.report_type,
        title=request.title,
        industry=request.industry,
        user_id=user["id"] if user else None,
        organization_id=org_id,
        format=request.format,
    )


@router.get("/task-types")
def list_task_types(user=Depends(get_current_user)):
    """List all available AI task types."""
    orchestrator = PromptOrchestrator()
    return {"task_types": orchestrator.list_task_types()}
