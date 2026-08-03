"""FastAPI routes for the Dashboard Composition Engine — Phase 6.

Endpoints:
  - GET    /api/dashboards/widgets              — List all available widgets
  - GET    /api/dashboards/widgets/types         — List supported widget types
  - GET    /api/dashboards/widgets/industry/{industry} — Widgets by industry
  - GET    /api/dashboards/templates             — List industry dashboard templates
  - POST   /api/dashboards/compose               — Compose a dashboard from widgets
  - GET    /api/dashboards/{dashboard_id}        — Get a composed dashboard
  - GET    /api/dashboards                       — List composed dashboards
  - POST   /api/dashboards/{dashboard_id}/widgets — Add widget to dashboard
  - DELETE /api/dashboards/{dashboard_id}/widgets/{widget_key} — Remove widget
  - GET    /api/dashboards/{dashboard_id}/data/{widget_key} — Get widget data
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session as DbSession

from shared.database import get_db
from shared.dependencies import get_current_user
from shared.response import success_response
from services.dashboard_composition import (
    DashboardCompositionService,
    WidgetRegistry,
    WidgetType,
)
from services.dashboard_widget_catalog import INDUSTRY_DASHBOARD_TEMPLATES

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/dashboards", tags=["Dashboard Composition"])

_composition_service = DashboardCompositionService()


# ── Request/Response Models ───────────────────────────


class ComposeDashboardRequest(BaseModel):
    name: str
    industry: str = "generic"
    widget_keys: list[str] | None = None
    description: str = ""


class AddWidgetRequest(BaseModel):
    widget_key: str


# ── Widget Endpoints ──────────────────────────────────


@router.get("/widgets")
async def list_widgets(
    industry: str | None = Query(None, description="Filter by industry"),
    widget_type: str | None = Query(None, description="Filter by widget type"),
    current_user: dict = Depends(get_current_user),
):
    """List all available widget definitions, optionally filtered."""
    widgets = WidgetRegistry.all()

    if industry:
        widgets = [w for w in widgets if not w.industries or industry in w.industries or "generic" in w.industries]

    if widget_type:
        try:
            wt = WidgetType(widget_type)
            widgets = [w for w in widgets if w.widget_type == wt]
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid widget type: {widget_type}")

    return success_response(
        [w.to_dict() for w in sorted(widgets, key=lambda x: (x.group, x.order))],
        f"Retrieved {len(widgets)} widgets",
    )


@router.get("/widgets/types")
async def list_widget_types(
    current_user: dict = Depends(get_current_user),
):
    """List all supported widget types."""
    types = [
        {"value": "kpi_card", "label": "KPI Card", "description": "Single metric with icon and trend"},
        {"value": "chart", "label": "Chart", "description": "Visual chart (line, bar, pie, etc.)"},
        {"value": "table", "label": "Table", "description": "Tabular data display"},
        {"value": "map", "label": "Map", "description": "Geographic data visualization"},
        {"value": "trend", "label": "Trend", "description": "Time-series trend with comparison"},
        {"value": "alert", "label": "Alert", "description": "Alert or notification panel"},
        {"value": "report", "label": "Report", "description": "Embedded report widget"},
    ]
    return success_response(types)


@router.get("/widgets/industry/{industry}")
async def list_widgets_by_industry(
    industry: str,
    current_user: dict = Depends(get_current_user),
):
    """List widgets available for a specific industry."""
    permissions = current_user.get("permissions", [])
    roles = current_user.get("roles", [])

    # Map super_admin to all permissions
    if "super_admin" in roles:
        permissions = ["*"]

    widgets = WidgetRegistry.by_industry(industry, permissions, roles)
    return success_response(
        [w.to_dict() for w in widgets],
        f"Retrieved {len(widgets)} widgets for industry '{industry}'",
    )


# ── Template Endpoints ────────────────────────────────


@router.get("/templates")
async def list_templates(
    current_user: dict = Depends(get_current_user),
):
    """List all industry dashboard templates."""
    templates = []
    for industry, config in INDUSTRY_DASHBOARD_TEMPLATES.items():
        widget_count = len(config["widget_keys"])
        templates.append({
            "industry": industry,
            "name": config["name"],
            "description": config["description"],
            "widget_count": widget_count,
            "widget_keys": config["widget_keys"],
        })
    return success_response(templates)


# ── Dashboard Composition Endpoints ───────────────────


@router.post("/compose")
async def compose_dashboard(
    request: ComposeDashboardRequest,
    current_user: dict = Depends(get_current_user),
):
    """Compose a new dashboard from widget keys or industry defaults."""
    permissions = current_user.get("permissions", [])
    roles = current_user.get("roles", [])
    if "super_admin" in roles:
        permissions = ["*"]

    dashboard = _composition_service.compose(
        name=request.name,
        industry=request.industry,
        widget_keys=request.widget_keys,
        permissions=permissions,
        roles=roles,
        description=request.description,
        created_by=str(current_user.get("id", "")),
    )
    return success_response(dashboard.to_dict(), "Dashboard composed successfully")


@router.get("/{dashboard_id}")
async def get_dashboard(
    dashboard_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get a composed dashboard by ID."""
    dashboard = _composition_service.get(dashboard_id)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return success_response(dashboard.to_dict())


@router.get("")
async def list_dashboards(
    industry: str | None = Query(None),
    current_user: dict = Depends(get_current_user),
):
    """List composed dashboards, optionally filtered by industry."""
    if industry:
        dashboards = _composition_service.list_by_industry(industry)
    else:
        all_dashes = _composition_service.list_by_industry("generic")
        for ind in INDUSTRY_DASHBOARD_TEMPLATES:
            all_dashes.extend(_composition_service.list_by_industry(ind))
        dashboards = all_dashes
    return success_response([d.to_dict() for d in dashboards])


@router.post("/{dashboard_id}/widgets")
async def add_widget_to_dashboard(
    dashboard_id: str,
    request: AddWidgetRequest,
    current_user: dict = Depends(get_current_user),
):
    """Add a widget to an existing dashboard."""
    dashboard = _composition_service.add_widget(dashboard_id, request.widget_key)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard or widget not found")
    return success_response(dashboard.to_dict(), "Widget added")


@router.delete("/{dashboard_id}/widgets/{widget_key}")
async def remove_widget_from_dashboard(
    dashboard_id: str,
    widget_key: str,
    current_user: dict = Depends(get_current_user),
):
    """Remove a widget from a dashboard."""
    dashboard = _composition_service.remove_widget(dashboard_id, widget_key)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return success_response(dashboard.to_dict(), "Widget removed")


@router.get("/{dashboard_id}/data/{widget_key}")
async def get_widget_data(
    dashboard_id: str,
    widget_key: str,
    current_user: dict = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """Get data for a specific widget in a dashboard.

    This endpoint resolves the widget's data source binding and returns
    the appropriate data. For now, returns placeholder data structure.
    """
    dashboard = _composition_service.get(dashboard_id)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")

    widget = next((w for w in dashboard.widgets if w.key == widget_key), None)
    if not widget:
        raise HTTPException(status_code=404, detail="Widget not found in dashboard")

    # Build placeholder data based on widget type
    data = _build_placeholder_widget_data(widget)
    return success_response(data)


def _build_placeholder_widget_data(widget) -> dict:
    """Build placeholder data structure for a widget."""
    wt = widget.widget_type.value

    if wt == "kpi_card":
        return {
            "widget_key": widget.key,
            "widget_type": wt,
            "title": widget.title,
            "value": 0,
            "unit": widget.config.get("unit", ""),
            "icon": widget.config.get("icon", "Activity"),
            "trend": {"direction": "neutral", "change_pct": 0},
        }

    if wt == "chart":
        return {
            "widget_key": widget.key,
            "widget_type": wt,
            "title": widget.title,
            "chart_subtype": widget.chart_subtype.value if widget.chart_subtype else "bar",
            "data": {"labels": [], "datasets": []},
            "config": widget.config,
        }

    if wt == "table":
        return {
            "widget_key": widget.key,
            "widget_type": wt,
            "title": widget.title,
            "columns": widget.config.get("columns", []),
            "rows": [],
        }

    if wt == "map":
        return {
            "widget_key": widget.key,
            "widget_type": wt,
            "title": widget.title,
            "geo_field": widget.config.get("geo_field", "region"),
            "regions": [],
        }

    if wt == "trend":
        return {
            "widget_key": widget.key,
            "widget_type": wt,
            "title": widget.title,
            "current": 0,
            "previous": 0,
            "change_pct": 0,
            "direction": "neutral",
            "series": [],
        }

    if wt == "alert":
        return {
            "widget_key": widget.key,
            "widget_type": wt,
            "title": widget.title,
            "alerts": [],
            "severity": widget.config.get("severity", "warning"),
        }

    if wt == "report":
        return {
            "widget_key": widget.key,
            "widget_type": wt,
            "title": widget.title,
            "report_type": widget.data_source.source_id if widget.data_source else None,
            "status": "not_generated",
            "url": None,
        }

    return {"widget_key": widget.key, "widget_type": wt, "title": widget.title}
