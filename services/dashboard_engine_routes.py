"""FastAPI routes for the Enterprise Dashboard Intelligence Engine.

Endpoints:
  - POST   /dashboard-engine/generate      — Generate dashboard from dataset
  - GET    /dashboard-engine/{id}          — Get dashboard metadata
  - GET    /dashboard-engine                — List dashboards
  - PUT    /dashboard-engine/{id}          — Update dashboard
  - DELETE /dashboard-engine/{id}          — Delete dashboard
  - POST   /dashboard-engine/{id}/widget   — Add widget
  - DELETE /dashboard-engine/{id}/widget/{wid} — Remove widget
  - PUT    /dashboard-engine/{id}/widget/{wid}/resize — Resize widget
  - PUT    /dashboard-engine/{id}/reorder  — Reorder widgets
  - POST   /dashboard-engine/{id}/share    — Share dashboard
  - POST   /dashboard-engine/{id}/reset    — Reset to recommended
  - POST   /dashboard-engine/{id}/save-custom — Save custom layout
  - GET    /dashboard-engine/{id}/kpi-values — Get computed KPI values
  - POST   /dashboard-engine/{id}/filters  — Apply filters
  - GET    /dashboard-engine/{id}/drilldown — Get drilldown data
  - POST   /dashboard-engine/{id}/assistant — Parse NL query
  - POST   /dashboard-engine/{id}/export   — Export dashboard
  - GET    /dashboard-engine/{id}/permissions — Check permissions
"""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from services.chart_recommender import ChartRecommendationEngine
from services.dashboard_assistant import AIDashboardAssistant
from services.dashboard_engine import (
    DashboardEngine,
    DashboardMetadata,
    PermissionLevel,
)
from services.dashboard_export import DashboardExportService
from services.dashboard_layout import DashboardLayoutEngine
from services.dashboard_performance import DashboardPerformanceLayer
from services.drilldown_engine import DrilldownEngine
from services.filter_engine import GlobalFilterEngine
from services.kpi_intelligence import KPIIntelligenceEngine

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/dashboard-engine", tags=["Dashboard Intelligence Engine"])

# ── Engine instances ───────────────────────────────────

_engine = DashboardEngine()
_kpi_engine = KPIIntelligenceEngine()
_chart_engine = ChartRecommendationEngine()
_layout_engine = DashboardLayoutEngine()
_filter_engine = GlobalFilterEngine()
_drilldown_engine = DrilldownEngine()
_assistant = AIDashboardAssistant()
_export_service = DashboardExportService()
_perf = DashboardPerformanceLayer()

# In-memory dataset store (replace with DB in production)
_datasets: dict[str, pd.DataFrame] = {}
_semantic_mappings: dict[str, dict] = {}


# ── Request/Response Models ────────────────────────────


class GenerateDashboardRequest(BaseModel):
    dataset_id: str
    org_id: str = ""
    industry: str = "unknown"
    semantic_mappings: dict = {}
    quality_score: float = 100.0
    title: str = ""
    subtitle: str = ""
    ai_insights: list[str] = []
    recommendations: list[str] = []
    template_key: str = ""
    created_by: str = ""
    layout_template: str = "standard"
    show_filters: bool = True
    show_ai_insights: bool = True


class UpdateDashboardRequest(BaseModel):
    title: str | None = None
    subtitle: str | None = None
    charts: list[dict] | None = None
    kpis: list[dict] | None = None
    filters: list[dict] | None = None
    layout: dict | None = None


class AddWidgetRequest(BaseModel):
    chart_type: str | None = None
    title: str = ""
    section: str = "supporting_charts"
    x_axis: str | None = None
    y_axis: str | None = None
    z_axis: str | None = None
    group_by: str | None = None
    aggregation: str = "sum"
    width: int = 6
    height: int = 300
    metric: str | None = None
    entity: str | None = None
    category: str = "operational"


class ResizeWidgetRequest(BaseModel):
    width: int = 6
    height: int = 300


class ReorderRequest(BaseModel):
    section: str
    widget_order: list[str]


class ShareRequest(BaseModel):
    user_ids: list[str]
    permission_level: str = PermissionLevel.VIEW.value


class SaveCustomRequest(BaseModel):
    user_id: str
    title: str
    chart_updates: list[dict] = []
    layout_updates: dict = {}
    kpi_updates: list[dict] = []


class ApplyFiltersRequest(BaseModel):
    filter_values: dict[str, Any] = {}


class DrilldownRequest(BaseModel):
    target_level: int | None = None
    filter_value: dict | None = None
    page: int = 1
    page_size: int = 50
    filters: dict | None = None


class AssistantRequest(BaseModel):
    query: str


class ExportRequest(BaseModel):
    fmt: str = "pdf"
    include_data: bool = True


# ── Endpoints ──────────────────────────────────────────


@router.post("/generate")
async def generate_dashboard(req: GenerateDashboardRequest):
    """Generate a dashboard dynamically from dataset and semantic analysis."""
    df = _datasets.get(req.dataset_id)
    if df is None:
        raise HTTPException(status_code=404, detail=f"Dataset {req.dataset_id} not found")

    # Detect KPIs
    kpis = _kpi_engine.detect_kpis(
        df=df,
        industry=req.industry,
        semantic_mappings=req.semantic_mappings,
        quality_score=req.quality_score,
    )

    # Recommend charts
    charts = _chart_engine.recommend_charts(
        df=df,
        industry=req.industry,
        semantic_mappings=req.semantic_mappings,
    )

    # Detect filters
    filters = _filter_engine.detect_filters(
        df=df,
        semantic_mappings=req.semantic_mappings,
    )

    # Generate layout
    layout = _layout_engine.apply_template(
        template_key=req.layout_template,
        kpis=kpis,
        charts=charts,
    )

    # Generate drilldowns
    drilldowns = _drilldown_engine.generate_drilldowns(
        df=df,
        kpis=kpis,
        charts=charts,
        semantic_mappings=req.semantic_mappings,
    )

    # Create dashboard metadata
    dashboard = DashboardMetadata(
        dashboard_id=DashboardEngine.generate_id(),
        dataset_id=req.dataset_id,
        org_id=req.org_id,
        title=req.title or f"{req.industry.title()} Dashboard",
        subtitle=req.subtitle,
        industry=req.industry,
        kpis=kpis,
        charts=charts,
        filters=filters,
        layout=layout,
        drilldowns=drilldowns,
        ai_insights=req.ai_insights,
        recommendations=req.recommendations,
        template_key=req.template_key,
        created_by=req.created_by,
    )
    dashboard.permissions.owner_id = req.created_by
    dashboard.permissions.org_id = req.org_id

    # Store
    _engine.create(dashboard)
    _semantic_mappings[dashboard.dashboard_id] = req.semantic_mappings

    return {"success": True, "data": dashboard.to_dict()}


@router.get("/{dashboard_id}")
async def get_dashboard(dashboard_id: str):
    """Get dashboard metadata."""
    dashboard = _engine.get(dashboard_id)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return {"success": True, "data": dashboard.to_dict()}


@router.get("")
async def list_dashboards(
    dataset_id: str | None = Query(None),
    org_id: str | None = Query(None),
    limit: int = Query(100),
):
    """List dashboards."""
    if dataset_id:
        dashboards = _engine.list_by_dataset(dataset_id)
    elif org_id:
        dashboards = _engine.list_by_org(org_id)
    else:
        dashboards = _engine.list_all(limit)
    return {"success": True, "data": [d.to_dict() for d in dashboards]}


@router.put("/{dashboard_id}")
async def update_dashboard(dashboard_id: str, req: UpdateDashboardRequest):
    """Update dashboard metadata."""
    updates = req.model_dump(exclude_none=True)
    dashboard = _engine.update(dashboard_id, updates)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return {"success": True, "data": dashboard.to_dict()}


@router.delete("/{dashboard_id}")
async def delete_dashboard(dashboard_id: str):
    """Delete a dashboard."""
    if not _engine.delete(dashboard_id):
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return {"success": True, "message": "Dashboard deleted"}


@router.post("/{dashboard_id}/widget")
async def add_widget(dashboard_id: str, req: AddWidgetRequest):
    """Add a widget to a dashboard."""
    widget = req.model_dump(exclude_none=True)
    dashboard = _engine.add_widget(dashboard_id, widget)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return {"success": True, "data": dashboard.to_dict()}


@router.delete("/{dashboard_id}/widget/{widget_id}")
async def remove_widget(dashboard_id: str, widget_id: str):
    """Remove a widget from a dashboard."""
    dashboard = _engine.remove_widget(dashboard_id, widget_id)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return {"success": True, "data": dashboard.to_dict()}


@router.put("/{dashboard_id}/widget/{widget_id}/resize")
async def resize_widget(dashboard_id: str, widget_id: str, req: ResizeWidgetRequest):
    """Resize a widget."""
    dashboard = _engine.resize_widget(dashboard_id, widget_id, req.width, req.height)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return {"success": True, "data": dashboard.to_dict()}


@router.put("/{dashboard_id}/reorder")
async def reorder_widgets(dashboard_id: str, req: ReorderRequest):
    """Reorder widgets within a section."""
    dashboard = _engine.reorder_widgets(dashboard_id, req.section, req.widget_order)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return {"success": True, "data": dashboard.to_dict()}


@router.post("/{dashboard_id}/share")
async def share_dashboard(dashboard_id: str, req: ShareRequest):
    """Share a dashboard with users."""
    dashboard = _engine.share(dashboard_id, req.user_ids, req.permission_level)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return {"success": True, "data": dashboard.to_dict()}


@router.post("/{dashboard_id}/save-custom")
async def save_custom_layout(dashboard_id: str, req: SaveCustomRequest):
    """Save a user's customized version of a dashboard."""
    try:
        dashboard = _engine.save_custom_layout(
            parent_dashboard_id=dashboard_id,
            user_id=req.user_id,
            title=req.title,
            chart_updates=req.chart_updates,
            layout_updates=req.layout_updates,
            kpi_updates=req.kpi_updates,
        )
        return {"success": True, "data": dashboard.to_dict()}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from None


@router.post("/{dashboard_id}/reset")
async def reset_to_recommended(dashboard_id: str):
    """Reset a custom dashboard to its parent (recommended) layout."""
    dashboard = _engine.reset_to_recommended(dashboard_id)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard or parent not found")
    return {"success": True, "data": dashboard.to_dict()}


@router.get("/{dashboard_id}/kpi-values")
async def get_kpi_values(dashboard_id: str):
    """Get computed KPI values."""
    dashboard = _engine.get(dashboard_id)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")

    df = _datasets.get(dashboard.dataset_id)
    if df is None:
        raise HTTPException(status_code=404, detail="Dataset not found")

    dataset_hash = _perf.compute_dataset_hash(df)
    values = {}
    for kpi in dashboard.kpis:
        if kpi.key == "total_records":
            values[kpi.key] = len(df)
        elif kpi.key == "data_quality":
            values[kpi.key] = "N/A"
        else:
            val = _perf.compute_kpi(
                kpi_key=kpi.key,
                df=df,
                source_columns=kpi.source_columns,
                aggregation=kpi.aggregation,
                dataset_hash=dataset_hash,
            )
            if val is not None:
                values[kpi.key] = val

    return {"success": True, "data": values}


@router.post("/{dashboard_id}/filters")
async def apply_filters(dashboard_id: str, req: ApplyFiltersRequest):
    """Apply global filters and get filtered data."""
    dashboard = _engine.get(dashboard_id)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")

    df = _datasets.get(dashboard.dataset_id)
    if df is None:
        raise HTTPException(status_code=404, detail="Dataset not found")

    filtered = _filter_engine.apply_filters(df, req.filter_values, dashboard.filters)

    # Get affected charts
    affected = {}
    for filter_id in req.filter_values:
        chart_ids = _filter_engine.get_affected_charts(
            filter_id, dashboard.filters, dashboard.charts
        )
        affected[filter_id] = chart_ids

    return {
        "success": True,
        "data": {
            "row_count": len(filtered),
            "affected_charts": affected,
        },
    }


@router.post("/{dashboard_id}/drilldown")
async def get_drilldown_data(dashboard_id: str, req: DrilldownRequest):
    """Get drilldown detail data."""
    dashboard = _engine.get(dashboard_id)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")

    df = _datasets.get(dashboard.dataset_id)
    if df is None:
        raise HTTPException(status_code=404, detail="Dataset not found")

    path = _drilldown_engine.create_path(dashboard.drilldowns)

    if req.target_level is not None:
        path = _drilldown_engine.drill_down(path, req.target_level, req.filter_value)
    else:
        path = _drilldown_engine.drill_down(path, 0)

    result = _drilldown_engine.get_detail_data(
        df=df,
        path=path,
        filters=req.filters,
        page=req.page,
        page_size=req.page_size,
    )

    return {"success": True, "data": result}


@router.post("/{dashboard_id}/assistant")
async def assistant_query(dashboard_id: str, req: AssistantRequest):
    """Parse a natural language query into a dashboard action."""
    dashboard = _engine.get(dashboard_id)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")

    df = _datasets.get(dashboard.dataset_id)
    df_columns = list(df.columns) if df is not None else []

    action = _assistant.parse_query(req.query)
    result = _assistant.execute_action(action, dashboard.to_dict(), df_columns)

    suggestions = _assistant.get_suggestions(dashboard.to_dict(), df_columns)

    return {
        "success": True,
        "data": {
            **result,
            "suggestions": suggestions,
        },
    }


@router.post("/{dashboard_id}/export")
async def export_dashboard(dashboard_id: str, req: ExportRequest):
    """Export a dashboard to the specified format."""
    dashboard = _engine.get(dashboard_id)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")

    df = _datasets.get(dashboard.dataset_id) if req.include_data else None

    # Get KPI values
    kpi_values = {}
    if df is not None:
        dataset_hash = _perf.compute_dataset_hash(df)
        for kpi in dashboard.kpis:
            if kpi.key == "total_records":
                kpi_values[kpi.key] = len(df)
            else:
                val = _perf.compute_kpi(
                    kpi_key=kpi.key,
                    df=df,
                    source_columns=kpi.source_columns,
                    aggregation=kpi.aggregation,
                    dataset_hash=dataset_hash,
                )
                if val is not None:
                    kpi_values[kpi.key] = val

    try:
        content, filename, content_type = _export_service.export(
            dashboard=dashboard,
            df=df,
            fmt=req.fmt,
            kpi_values=kpi_values,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from None

    from fastapi.responses import Response

    return Response(
        content=content,
        media_type=content_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/{dashboard_id}/permissions")
async def check_permissions(
    dashboard_id: str,
    user_id: str = Query(""),
    user_roles: str = Query(""),
):
    """Check user permissions for a dashboard."""
    dashboard = _engine.get(dashboard_id)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")

    roles = user_roles.split(",") if user_roles else []

    return {
        "success": True,
        "data": {
            "can_access": _engine.can_access(dashboard_id, user_id, roles),
            "can_edit": _engine.can_edit(dashboard_id, user_id),
            "can_export": _engine.can_export(dashboard_id, user_id),
            "visibility": dashboard.permissions.visibility,
            "is_owner": user_id == dashboard.permissions.owner_id,
        },
    }


# ── Helper: Register dataset ───────────────────────────


def register_dataset(dataset_id: str, df: pd.DataFrame) -> None:
    """Register a dataset for dashboard generation."""
    _datasets[dataset_id] = df
