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

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session as DbSession

from services.dashboard_composition import (
    DashboardCompositionService,
    DataSourceType,
    WidgetRegistry,
    WidgetType,
)
from services.dashboard_widget_catalog import INDUSTRY_DASHBOARD_TEMPLATES
from shared.database import get_db
from shared.dependencies import get_current_user
from shared.response import success_response
from shared.security import validate_sql_identifier

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
        widgets = [
            w
            for w in widgets
            if not w.industries or industry in w.industries or "generic" in w.industries
        ]

    if widget_type:
        try:
            wt = WidgetType(widget_type)
            widgets = [w for w in widgets if w.widget_type == wt]
        except ValueError:
            raise HTTPException(
                status_code=400, detail=f"Invalid widget type: {widget_type}"
            ) from None

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
        {
            "value": "kpi_card",
            "label": "KPI Card",
            "description": "Single metric with icon and trend",
        },
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
        templates.append(
            {
                "industry": industry,
                "name": config["name"],
                "description": config["description"],
                "widget_count": widget_count,
                "widget_keys": config["widget_keys"],
            }
        )
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

    Resolves the widget's data source binding and returns real data
    from the configured source. Falls back to an empty structure with
    a `data_source` indicator if no binding is configured.
    """
    dashboard = _composition_service.get(dashboard_id)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")

    widget = next((w for w in dashboard.widgets if w.key == widget_key), None)
    if not widget:
        raise HTTPException(status_code=404, detail="Widget not found in dashboard")

    data = _resolve_widget_data(widget, db)
    return success_response(data)


def _resolve_widget_data(widget, db: DbSession) -> dict:
    """Resolve real data for a widget from its data source binding.

    If the widget has no data source binding, returns an empty structure
    with a `no_data_source` indicator so the frontend can handle it.
    """
    wt = widget.widget_type.value
    ds = widget.data_source

    if ds is None:
        return _empty_widget_data(widget, wt, reason="no_data_source")

    try:
        if ds.source_type == DataSourceType.KPI:
            return _resolve_kpi_widget(widget, wt, ds, db)
        if ds.source_type == DataSourceType.DATASET:
            return _resolve_dataset_widget(widget, wt, ds, db)
        if ds.source_type == DataSourceType.AGGREGATE:
            return _resolve_aggregate_widget(widget, wt, ds, db)
        if ds.source_type == DataSourceType.ANALYTICS_ALERT:
            return _resolve_alert_widget(widget, wt, ds, db)
        if ds.source_type == DataSourceType.REPORT:
            return _resolve_report_widget(widget, wt, ds)
        return _empty_widget_data(
            widget, wt, reason=f"unsupported_source_type:{ds.source_type.value}"
        )
    except Exception as e:
        logger.warning("Failed to resolve widget data for %s: %s", widget.key, e)
        return _empty_widget_data(widget, wt, reason=f"error:{type(e).__name__}")


def _empty_widget_data(widget, wt: str, *, reason: str = "no_data_source") -> dict:
    """Return an empty widget data structure with a reason indicator."""
    base = {
        "widget_key": widget.key,
        "widget_type": wt,
        "title": widget.title,
        "data_source": reason,
    }
    if wt == "kpi_card":
        base.update(
            {
                "value": 0,
                "unit": widget.config.get("unit", ""),
                "icon": widget.config.get("icon", "Activity"),
                "trend": {"direction": "neutral", "change_pct": 0},
            }
        )
    elif wt == "chart":
        base.update(
            {
                "chart_subtype": widget.chart_subtype.value if widget.chart_subtype else "bar",
                "data": {"labels": [], "datasets": []},
                "config": widget.config,
            }
        )
    elif wt == "table":
        base.update(
            {
                "columns": widget.config.get("columns", []),
                "rows": [],
            }
        )
    elif wt == "map":
        base.update(
            {
                "geo_field": widget.config.get("geo_field", "region"),
                "regions": [],
            }
        )
    elif wt == "trend":
        base.update(
            {
                "current": 0,
                "previous": 0,
                "change_pct": 0,
                "direction": "neutral",
                "series": [],
            }
        )
    elif wt == "alert":
        base.update(
            {
                "alerts": [],
                "severity": widget.config.get("severity", "warning"),
            }
        )
    elif wt == "report":
        base.update(
            {
                "report_type": None,
                "status": "not_generated",
                "url": None,
            }
        )
    return base


def _resolve_kpi_widget(widget, wt: str, ds, db: DbSession) -> dict:
    """Resolve KPI data from the database."""
    from database.repositories import SalesRepository

    repo = SalesRepository()
    kpis = repo.get_kpis(
        region=ds.filters.get("region"),
        category=ds.filters.get("category"),
    )
    metric_key = ds.source_id or "total_sales"
    value = kpis.get(str(metric_key), 0)

    if wt == "kpi_card":
        return {
            "widget_key": widget.key,
            "widget_type": wt,
            "title": widget.title,
            "value": float(value),
            "unit": widget.config.get("unit", ""),
            "icon": widget.config.get("icon", "Activity"),
            "trend": {"direction": "neutral", "change_pct": 0},
        }
    return _empty_widget_data(widget, wt, reason="kpi_unmatched_widget_type")


def _resolve_dataset_widget(widget, wt: str, ds, db: DbSession) -> dict:
    """Resolve dataset data by querying the source table."""
    table_name = str(ds.source_id or "sales")
    allowed = {"sales"}
    if table_name not in allowed:
        return _empty_widget_data(widget, wt, reason=f"restricted_table:{table_name}")

    _ALLOWED_AGGS = {"sum", "avg", "min", "max", "count"}
    if ds.group_by:
        try:
            validate_sql_identifier(ds.group_by)
        except ValueError:
            return _empty_widget_data(widget, wt, reason="invalid_group_by")
    agg = ds.aggregation or "sum"
    if agg not in _ALLOWED_AGGS:
        return _empty_widget_data(widget, wt, reason=f"invalid_aggregation:{agg}")

    query = f"SELECT * FROM {table_name}"
    conditions = []
    params: dict = {}
    for key, val in ds.filters.items():
        try:
            validate_sql_identifier(key)
        except ValueError:
            continue
        conditions.append(f"{key} = :{key}")
        params[key] = val
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    if ds.group_by:
        agg = ds.aggregation or "sum"
        query = f"SELECT {ds.group_by}, {agg}(*) as value FROM {table_name}"
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += f" GROUP BY {ds.group_by} ORDER BY value DESC"
    if ds.limit:
        query += f" LIMIT {int(ds.limit)}"

    with db.bind.connect() as conn:
        df = pd.read_sql(text(query), conn, params=params)

    records = df.to_dict("records")

    if wt == "table":
        return {
            "widget_key": widget.key,
            "widget_type": wt,
            "title": widget.title,
            "columns": df.columns.tolist(),
            "rows": records,
        }
    if wt == "chart":
        labels = [str(r.get(ds.group_by or df.columns[0], "")) for r in records]
        values = [float(r.get("value", 0)) for r in records] if ds.group_by else []
        return {
            "widget_key": widget.key,
            "widget_type": wt,
            "title": widget.title,
            "chart_subtype": widget.chart_subtype.value if widget.chart_subtype else "bar",
            "data": {"labels": labels, "datasets": [{"label": widget.title, "data": values}]},
            "config": widget.config,
        }
    return _empty_widget_data(widget, wt, reason="dataset_unmatched_widget_type")


def _resolve_aggregate_widget(widget, wt: str, ds, db: DbSession) -> dict:
    """Resolve aggregate data (group-by + aggregation)."""
    table_name = str(ds.source_id or "sales")
    allowed = {"sales"}
    if table_name not in allowed:
        return _empty_widget_data(widget, wt, reason=f"restricted_table:{table_name}")

    if not ds.group_by:
        return _empty_widget_data(widget, wt, reason="aggregate_requires_group_by")

    _ALLOWED_AGGS = {"sum", "avg", "min", "max", "count"}
    try:
        validate_sql_identifier(ds.group_by)
    except ValueError:
        return _empty_widget_data(widget, wt, reason="invalid_group_by")
    agg = ds.aggregation or "sum"
    if agg not in _ALLOWED_AGGS:
        return _empty_widget_data(widget, wt, reason=f"invalid_aggregation:{agg}")
    metric = ds.query or "sales"
    try:
        validate_sql_identifier(metric)
    except ValueError:
        return _empty_widget_data(widget, wt, reason="invalid_metric")
    query = f"SELECT {ds.group_by}, {agg}({metric}) as value FROM {table_name}"
    conditions = []
    params: dict = {}
    for key, val in ds.filters.items():
        try:
            validate_sql_identifier(key)
        except ValueError:
            continue
        conditions.append(f"{key} = :{key}")
        params[key] = val
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += f" GROUP BY {ds.group_by} ORDER BY value DESC"
    if ds.limit:
        query += f" LIMIT {int(ds.limit)}"

    with db.bind.connect() as conn:
        df = pd.read_sql(text(query), conn, params=params)

    records = df.to_dict("records")
    labels = [str(r.get(ds.group_by, "")) for r in records]
    values = [float(r.get("value", 0)) for r in records]

    if wt == "chart":
        return {
            "widget_key": widget.key,
            "widget_type": wt,
            "title": widget.title,
            "chart_subtype": widget.chart_subtype.value if widget.chart_subtype else "bar",
            "data": {"labels": labels, "datasets": [{"label": widget.title, "data": values}]},
            "config": widget.config,
        }
    if wt == "table":
        return {
            "widget_key": widget.key,
            "widget_type": wt,
            "title": widget.title,
            "columns": [ds.group_by, "value"],
            "rows": records,
        }
    if wt == "trend":
        return {
            "widget_key": widget.key,
            "widget_type": wt,
            "title": widget.title,
            "current": values[0] if values else 0,
            "previous": values[1] if len(values) > 1 else 0,
            "change_pct": (
                round((values[0] - values[1]) / values[1] * 100, 2)
                if len(values) > 1 and values[1] != 0
                else 0
            ),
            "direction": "up" if len(values) > 1 and values[0] > values[1] else "neutral",
            "series": [{"labels": labels, "values": values}],
        }
    return _empty_widget_data(widget, wt, reason="aggregate_unmatched_widget_type")


def _resolve_alert_widget(widget, wt: str, ds, db: DbSession) -> dict:
    """Resolve analytics alerts from the database."""
    from ai.models import AIAnomalyAlert

    alerts = (
        db.query(AIAnomalyAlert)
        .filter(AIAnomalyAlert.is_resolved.is_(False))
        .order_by(AIAnomalyAlert.created_at.desc())
        .limit(ds.limit or 10)
        .all()
    )
    alert_list = [
        {
            "id": a.id,
            "title": a.title,
            "description": a.description,
            "severity": a.severity,
            "created_at": str(a.created_at) if a.created_at else None,
        }
        for a in alerts
    ]
    return {
        "widget_key": widget.key,
        "widget_type": wt,
        "title": widget.title,
        "alerts": alert_list,
        "severity": widget.config.get("severity", "warning"),
    }


def _resolve_report_widget(widget, wt: str, ds) -> dict:
    """Resolve report widget — returns metadata about the referenced report."""
    return {
        "widget_key": widget.key,
        "widget_type": wt,
        "title": widget.title,
        "report_type": ds.source_id,
        "status": "available",
        "url": None,
    }
