"""Dashboard Metadata Model & Engine.

Provides a reusable, persistable dashboard schema and the engine to
generate, store, and manage dashboard configurations dynamically.

Every dashboard contains:
  - Dashboard ID, Dataset ID, Organization ID
  - Industry, Version
  - KPIs, Charts, Filters, Layout, Drilldowns
  - Permissions

Configurations are stored in-memory (replace with DB in production)
so dashboards can be regenerated, edited, and shared.
"""

from __future__ import annotations

import copy
import hashlib
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


# ── Enums ──────────────────────────────────────────────


class WidgetType(str, Enum):
    KPI_CARD = "kpi_card"
    TREND_CARD = "trend_card"
    LINE_CHART = "line_chart"
    BAR_CHART = "bar_chart"
    HORIZONTAL_BAR = "horizontal_bar"
    PIE_CHART = "pie_chart"
    DONUT_CHART = "donut_chart"
    HISTOGRAM = "histogram"
    SCATTER_PLOT = "scatter_plot"
    HEATMAP = "heatmap"
    GEO_MAP = "geo_map"
    GAUGE = "gauge"
    LEADERBOARD = "leaderboard"
    TABLE = "table"
    TREE = "tree"
    FORECAST = "forecast"
    AI_INSIGHT_PANEL = "ai_insight_panel"
    FILTER_BAR = "filter_bar"


class FilterType(str, Enum):
    DATE_RANGE = "date_range"
    SINGLE_SELECT = "single_select"
    MULTI_SELECT = "multi_select"
    SEARCH = "search"
    NUMERIC_RANGE = "numeric_range"


class LayoutSection(str, Enum):
    FILTER_BAR = "filter_bar"
    KPI_ROW = "kpi_row"
    PRIMARY_CHARTS = "primary_charts"
    SUPPORTING_CHARTS = "supporting_charts"
    AI_INSIGHTS = "ai_insights"
    DETAIL_TABLE = "detail_table"


class PermissionLevel(str, Enum):
    VIEW = "view"
    EDIT = "edit"
    SHARE = "share"
    EXPORT = "export"
    ADMIN = "admin"


# ── Data Classes ───────────────────────────────────────


@dataclass
class KPIDefinition:
    """A KPI definition with formula and source columns."""

    key: str
    label: str
    entity: str
    metric: str  # sum, count, avg, min, max, median, custom
    category: str  # operational, financial, clinical, academic, etc.
    formula: str = ""
    source_columns: list[str] = field(default_factory=list)
    aggregation: str = "sum"
    confidence: float = 1.0
    icon: str = "📊"
    unit: str = ""
    threshold_warning: float | None = None
    threshold_critical: float | None = None
    description: str = ""

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "label": self.label,
            "entity": self.entity,
            "metric": self.metric,
            "category": self.category,
            "formula": self.formula,
            "source_columns": self.source_columns,
            "aggregation": self.aggregation,
            "confidence": round(self.confidence, 2),
            "icon": self.icon,
            "unit": self.unit,
            "threshold_warning": self.threshold_warning,
            "threshold_critical": self.threshold_critical,
            "description": self.description,
        }


@dataclass
class ChartDefinition:
    """A chart definition with data bindings."""

    id: str
    chart_type: str
    title: str
    section: str  # LayoutSection value
    x_axis: str | None = None
    y_axis: str | None = None
    z_axis: str | None = None  # for heatmaps
    group_by: str | None = None
    aggregation: str = "sum"
    source_columns: list[str] = field(default_factory=list)
    confidence: float = 1.0
    reasoning: str = ""
    drilldown_target: str | None = None
    filters: list[str] = field(default_factory=list)
    width: int = 6  # grid columns (1-12)
    height: int = 300  # pixels
    order: int = 0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "chart_type": self.chart_type,
            "title": self.title,
            "section": self.section,
            "x_axis": self.x_axis,
            "y_axis": self.y_axis,
            "z_axis": self.z_axis,
            "group_by": self.group_by,
            "aggregation": self.aggregation,
            "source_columns": self.source_columns,
            "confidence": round(self.confidence, 2),
            "reasoning": self.reasoning,
            "drilldown_target": self.drilldown_target,
            "filters": self.filters,
            "width": self.width,
            "height": self.height,
            "order": self.order,
        }


@dataclass
class FilterDefinition:
    """A global filter definition."""

    id: str
    filter_type: str  # FilterType value
    label: str
    column: str
    entity: str | None = None
    default_value: Any = None
    options: list[Any] = field(default_factory=list)
    depends_on: str | None = None  # cascading filter

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "filter_type": self.filter_type,
            "label": self.label,
            "column": self.column,
            "entity": self.entity,
            "default_value": self.default_value,
            "options": self.options,
            "depends_on": self.depends_on,
        }


@dataclass
class DrilldownLevel:
    """A single drilldown level."""

    level: int
    label: str
    chart_id: str | None = None
    table_columns: list[str] = field(default_factory=list)
    parent_column: str | None = None
    target_column: str | None = None

    def to_dict(self) -> dict:
        return {
            "level": self.level,
            "label": self.label,
            "chart_id": self.chart_id,
            "table_columns": self.table_columns,
            "parent_column": self.parent_column,
            "target_column": self.target_column,
        }


@dataclass
class DashboardPermissions:
    """Access control for a dashboard."""

    owner_id: str = ""
    org_id: str = ""
    visibility: str = "private"  # private, org, public
    allowed_roles: list[str] = field(default_factory=list)
    allowed_users: list[str] = field(default_factory=list)
    permissions: dict[str, list[str]] = field(default_factory=dict)  # user_id → [PermissionLevel]

    def to_dict(self) -> dict:
        return {
            "owner_id": self.owner_id,
            "org_id": self.org_id,
            "visibility": self.visibility,
            "allowed_roles": self.allowed_roles,
            "allowed_users": self.allowed_users,
            "permissions": self.permissions,
        }


@dataclass
class DashboardLayout:
    """Layout configuration for a dashboard."""

    sections: dict[str, list[str]] = field(default_factory=dict)  # section → widget IDs
    grid_columns: int = 12
    responsive: bool = True
    background_color: str = ""
    show_ai_insights: bool = True
    show_filters: bool = True

    def to_dict(self) -> dict:
        return {
            "sections": self.sections,
            "grid_columns": self.grid_columns,
            "responsive": self.responsive,
            "background_color": self.background_color,
            "show_ai_insights": self.show_ai_insights,
            "show_filters": self.show_filters,
        }


@dataclass
class DashboardMetadata:
    """Complete dashboard metadata model.

    This is the persistable schema for a generated dashboard.
    """

    dashboard_id: str
    dataset_id: str
    org_id: str
    title: str
    subtitle: str = ""
    industry: str = "unknown"
    version: int = 1
    kpis: list[KPIDefinition] = field(default_factory=list)
    charts: list[ChartDefinition] = field(default_factory=list)
    filters: list[FilterDefinition] = field(default_factory=list)
    layout: DashboardLayout = field(default_factory=DashboardLayout)
    drilldowns: list[DrilldownLevel] = field(default_factory=list)
    permissions: DashboardPermissions = field(default_factory=DashboardPermissions)
    ai_insights: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    template_key: str = ""
    created_at: str = ""
    updated_at: str = ""
    created_by: str = ""
    is_custom: bool = False  # True if user modified from recommended
    parent_dashboard_id: str | None = None  # for saved custom layouts

    def to_dict(self) -> dict:
        return {
            "dashboard_id": self.dashboard_id,
            "dataset_id": self.dataset_id,
            "org_id": self.org_id,
            "title": self.title,
            "subtitle": self.subtitle,
            "industry": self.industry,
            "version": self.version,
            "kpis": [k.to_dict() for k in self.kpis],
            "charts": [c.to_dict() for c in self.charts],
            "filters": [f.to_dict() for f in self.filters],
            "layout": self.layout.to_dict(),
            "drilldowns": [d.to_dict() for d in self.drilldowns],
            "permissions": self.permissions.to_dict(),
            "ai_insights": self.ai_insights,
            "recommendations": self.recommendations,
            "template_key": self.template_key,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "created_by": self.created_by,
            "is_custom": self.is_custom,
            "parent_dashboard_id": self.parent_dashboard_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> DashboardMetadata:
        """Reconstruct from dict (e.g., from DB)."""
        return cls(
            dashboard_id=data["dashboard_id"],
            dataset_id=data["dataset_id"],
            org_id=data.get("org_id", ""),
            title=data["title"],
            subtitle=data.get("subtitle", ""),
            industry=data.get("industry", "unknown"),
            version=data.get("version", 1),
            kpis=[KPIDefinition(**k) for k in data.get("kpis", [])],
            charts=[ChartDefinition(**c) for c in data.get("charts", [])],
            filters=[FilterDefinition(**f) for f in data.get("filters", [])],
            layout=DashboardLayout(**data.get("layout", {})),
            drilldowns=[DrilldownLevel(**d) for d in data.get("drilldowns", [])],
            permissions=DashboardPermissions(**data.get("permissions", {})),
            ai_insights=data.get("ai_insights", []),
            recommendations=data.get("recommendations", []),
            template_key=data.get("template_key", ""),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            created_by=data.get("created_by", ""),
            is_custom=data.get("is_custom", False),
            parent_dashboard_id=data.get("parent_dashboard_id"),
        )

    def content_hash(self) -> str:
        """Hash of KPI/chart/filter content for change detection."""
        content = json.dumps(
            {
                "kpis": [k.to_dict() for k in self.kpis],
                "charts": [c.to_dict() for c in self.charts],
                "filters": [f.to_dict() for f in self.filters],
            },
            sort_keys=True,
        )
        return hashlib.sha256(content.encode()).hexdigest()[:16]


# ── Dashboard Engine ───────────────────────────────────


class DashboardEngine:
    """Manages dashboard lifecycle: create, store, update, share, delete.

    In production, replace _store with a database table.
    """

    def __init__(self):
        self._store: dict[str, DashboardMetadata] = {}
        self._by_dataset: dict[str, list[str]] = {}  # dataset_id → dashboard_ids
        self._by_org: dict[str, list[str]] = {}  # org_id → dashboard_ids

    # ── CRUD ──────────────────────────────────────────

    def create(self, dashboard: DashboardMetadata) -> DashboardMetadata:
        """Store a new dashboard."""
        now = self._now()
        dashboard.created_at = now
        dashboard.updated_at = now
        self._store[dashboard.dashboard_id] = dashboard
        self._index(dashboard)
        logger.info(
            f"Created dashboard {dashboard.dashboard_id} for dataset {dashboard.dataset_id}"
        )
        return dashboard

    def get(self, dashboard_id: str) -> DashboardMetadata | None:
        return self._store.get(dashboard_id)

    def update(self, dashboard_id: str, updates: dict) -> DashboardMetadata | None:
        dashboard = self._store.get(dashboard_id)
        if not dashboard:
            return None

        for key, value in updates.items():
            if key in (
                "title",
                "subtitle",
                "industry",
                "version",
                "ai_insights",
                "recommendations",
                "template_key",
                "is_custom",
            ):
                setattr(dashboard, key, value)
            elif key == "kpis":
                dashboard.kpis = [KPIDefinition(**k) if isinstance(k, dict) else k for k in value]
            elif key == "charts":
                dashboard.charts = [
                    ChartDefinition(**c) if isinstance(c, dict) else c for c in value
                ]
            elif key == "filters":
                dashboard.filters = [
                    FilterDefinition(**f) if isinstance(f, dict) else f for f in value
                ]
            elif key == "layout":
                dashboard.layout = DashboardLayout(**value) if isinstance(value, dict) else value
            elif key == "drilldowns":
                dashboard.drilldowns = [
                    DrilldownLevel(**d) if isinstance(d, dict) else d for d in value
                ]
            elif key == "permissions":
                dashboard.permissions = (
                    DashboardPermissions(**value) if isinstance(value, dict) else value
                )

        dashboard.updated_at = self._now()
        dashboard.version += 1
        return dashboard

    def delete(self, dashboard_id: str) -> bool:
        dashboard = self._store.pop(dashboard_id, None)
        if not dashboard:
            return False
        self._unindex(dashboard)
        return True

    def list_by_dataset(self, dataset_id: str) -> list[DashboardMetadata]:
        ids = self._by_dataset.get(dataset_id, [])
        return [self._store[i] for i in ids if i in self._store]

    def list_by_org(self, org_id: str) -> list[DashboardMetadata]:
        ids = self._by_org.get(org_id, [])
        return [self._store[i] for i in ids if i in self._store]

    def list_all(self, limit: int = 100) -> list[DashboardMetadata]:
        return list(self._store.values())[:limit]

    # ── Customization ─────────────────────────────────

    def save_custom_layout(
        self,
        parent_dashboard_id: str,
        user_id: str,
        title: str,
        chart_updates: list[dict] | None = None,
        layout_updates: dict | None = None,
        kpi_updates: list[dict] | None = None,
    ) -> DashboardMetadata:
        """Save a user's customized version of a dashboard."""
        parent = self._store.get(parent_dashboard_id)
        if not parent:
            raise ValueError(f"Parent dashboard {parent_dashboard_id} not found")

        custom = copy.deepcopy(parent)
        custom.dashboard_id = str(uuid.uuid4())
        custom.title = title
        custom.parent_dashboard_id = parent_dashboard_id
        custom.is_custom = True
        custom.created_by = user_id
        custom.version = 1

        if chart_updates:
            for update in chart_updates:
                chart_id = update.get("id")
                for _i, chart in enumerate(custom.charts):
                    if chart.id == chart_id:
                        for k, v in update.items():
                            if k != "id" and hasattr(chart, k):
                                setattr(chart, k, v)
                        break

        if layout_updates:
            for k, v in layout_updates.items():
                if hasattr(custom.layout, k):
                    setattr(custom.layout, k, v)

        if kpi_updates:
            for update in kpi_updates:
                kpi_key = update.get("key")
                for _i, kpi in enumerate(custom.kpis):
                    if kpi.key == kpi_key:
                        for k, v in update.items():
                            if k != "key" and hasattr(kpi, k):
                                setattr(kpi, k, v)
                        break

        return self.create(custom)

    def add_widget(self, dashboard_id: str, widget: dict) -> DashboardMetadata | None:
        """Add a widget (chart or KPI) to a dashboard."""
        dashboard = self._store.get(dashboard_id)
        if not dashboard:
            return None

        if widget.get("chart_type"):
            if "id" not in widget or not widget["id"]:
                widget["id"] = str(uuid.uuid4())
            chart = ChartDefinition(**widget)
            dashboard.charts.append(chart)
            section = chart.section
            if section not in dashboard.layout.sections:
                dashboard.layout.sections[section] = []
            dashboard.layout.sections[section].append(chart.id)
        elif widget.get("metric"):
            kpi = KPIDefinition(**widget)
            dashboard.kpis.append(kpi)

        dashboard.updated_at = self._now()
        dashboard.version += 1
        return dashboard

    def remove_widget(self, dashboard_id: str, widget_id: str) -> DashboardMetadata | None:
        """Remove a widget from a dashboard."""
        dashboard = self._store.get(dashboard_id)
        if not dashboard:
            return None

        dashboard.charts = [c for c in dashboard.charts if c.id != widget_id]
        dashboard.kpis = [k for k in dashboard.kpis if k.key != widget_id]
        for section_widgets in dashboard.layout.sections.values():
            if widget_id in section_widgets:
                section_widgets.remove(widget_id)

        dashboard.updated_at = self._now()
        dashboard.version += 1
        return dashboard

    def reorder_widgets(
        self, dashboard_id: str, section: str, widget_order: list[str]
    ) -> DashboardMetadata | None:
        """Reorder widgets within a section."""
        dashboard = self._store.get(dashboard_id)
        if not dashboard:
            return None

        dashboard.layout.sections[section] = widget_order
        for i, wid in enumerate(widget_order):
            for chart in dashboard.charts:
                if chart.id == wid:
                    chart.order = i

        dashboard.updated_at = self._now()
        dashboard.version += 1
        return dashboard

    def resize_widget(
        self, dashboard_id: str, widget_id: str, width: int, height: int
    ) -> DashboardMetadata | None:
        """Resize a widget."""
        dashboard = self._store.get(dashboard_id)
        if not dashboard:
            return None

        for chart in dashboard.charts:
            if chart.id == widget_id:
                chart.width = max(1, min(12, width))
                chart.height = max(100, height)
                break

        dashboard.updated_at = self._now()
        dashboard.version += 1
        return dashboard

    # ── Sharing ───────────────────────────────────────

    def share(
        self,
        dashboard_id: str,
        user_ids: list[str],
        permission_level: str = PermissionLevel.VIEW.value,
    ) -> DashboardMetadata | None:
        """Share a dashboard with users."""
        dashboard = self._store.get(dashboard_id)
        if not dashboard:
            return None

        for uid in user_ids:
            dashboard.permissions.allowed_users.append(uid)
            dashboard.permissions.permissions.setdefault(uid, []).append(permission_level)

        dashboard.updated_at = self._now()
        return dashboard

    def set_visibility(self, dashboard_id: str, visibility: str) -> DashboardMetadata | None:
        """Set dashboard visibility (private, org, public)."""
        dashboard = self._store.get(dashboard_id)
        if not dashboard:
            return None

        dashboard.permissions.visibility = visibility
        dashboard.updated_at = self._now()
        return dashboard

    # ── Permissions ───────────────────────────────────

    def can_access(self, dashboard_id: str, user_id: str, user_roles: list[str]) -> bool:
        """Check if a user can access a dashboard."""
        dashboard = self._store.get(dashboard_id)
        if not dashboard:
            return False

        perms = dashboard.permissions
        if perms.visibility == "public":
            return True
        if user_id == perms.owner_id:
            return True
        if user_id in perms.allowed_users:
            return True
        if any(role in perms.allowed_roles for role in user_roles):
            return True
        if perms.visibility == "org" and perms.org_id:
            # Would check user's org membership in production
            return True
        return False

    def can_edit(self, dashboard_id: str, user_id: str) -> bool:
        """Check if a user can edit a dashboard."""
        dashboard = self._store.get(dashboard_id)
        if not dashboard:
            return False
        if user_id == dashboard.permissions.owner_id:
            return True
        perms = dashboard.permissions.permissions.get(user_id, [])
        return PermissionLevel.EDIT.value in perms or PermissionLevel.ADMIN.value in perms

    def can_export(self, dashboard_id: str, user_id: str) -> bool:
        """Check if a user can export a dashboard."""
        dashboard = self._store.get(dashboard_id)
        if not dashboard:
            return False
        if user_id == dashboard.permissions.owner_id:
            return True
        perms = dashboard.permissions.permissions.get(user_id, [])
        return (
            PermissionLevel.EXPORT.value in perms
            or PermissionLevel.ADMIN.value in perms
            or PermissionLevel.EDIT.value in perms
        )

    # ── Reset ─────────────────────────────────────────

    def reset_to_recommended(self, custom_dashboard_id: str) -> DashboardMetadata | None:
        """Reset a custom dashboard to its parent (recommended) layout."""
        custom = self._store.get(custom_dashboard_id)
        if not custom or not custom.parent_dashboard_id:
            return None

        parent = self._store.get(custom.parent_dashboard_id)
        if not parent:
            return None

        custom.charts = copy.deepcopy(parent.charts)
        custom.kpis = copy.deepcopy(parent.kpis)
        custom.filters = copy.deepcopy(parent.filters)
        custom.layout = copy.deepcopy(parent.layout)
        custom.drilldowns = copy.deepcopy(parent.drilldowns)
        custom.is_custom = False
        custom.updated_at = self._now()
        custom.version += 1
        return custom

    # ── Helpers ───────────────────────────────────────

    def _index(self, dashboard: DashboardMetadata) -> None:
        self._by_dataset.setdefault(dashboard.dataset_id, []).append(dashboard.dashboard_id)
        if dashboard.org_id:
            self._by_org.setdefault(dashboard.org_id, []).append(dashboard.dashboard_id)

    def _unindex(self, dashboard: DashboardMetadata) -> None:
        ids = self._by_dataset.get(dashboard.dataset_id, [])
        if dashboard.dashboard_id in ids:
            ids.remove(dashboard.dashboard_id)
        if dashboard.org_id:
            org_ids = self._by_org.get(dashboard.org_id, [])
            if dashboard.dashboard_id in org_ids:
                org_ids.remove(dashboard.dashboard_id)

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def generate_id() -> str:
        return str(uuid.uuid4())
