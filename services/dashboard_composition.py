"""Dashboard Composition Engine â€” Phase 6.

Provides a widget registry, data source bindings, and composition service
for building dashboards from reusable widgets that adapt by industry.

Widget types: kpi_card, chart, table, map, trend, alert, report

Architecture:
    Dashboard â†’ Widgets â†’ Permissions â†’ Data Sources
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


# â”€â”€ Enums â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


class WidgetType(str, Enum):
    KPI_CARD = "kpi_card"
    CHART = "chart"
    TABLE = "table"
    MAP = "map"
    TREND = "trend"
    ALERT = "alert"
    REPORT = "report"


class ChartSubType(str, Enum):
    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    DONUT = "donut"
    SCATTER = "scatter"
    AREA = "area"
    HEATMAP = "heatmap"
    GAUGE = "gauge"
    HORIZONTAL_BAR = "horizontal_bar"


class DataSourceType(str, Enum):
    DATASET = "dataset"
    KPI = "kpi"
    ANALYTICS_ALERT = "analytics_alert"
    REPORT = "report"
    EXTERNAL_API = "external_api"
    AGGREGATE = "aggregate"


class Industry(str, Enum):
    HEALTHCARE = "healthcare"
    EDUCATION = "education"
    BUSINESS = "business"
    RESEARCH = "research"
    GOVERNMENT = "government"
    NGO = "ngo"
    CHURCH = "church"
    GENERIC = "generic"


# â”€â”€ Data Classes â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


@dataclass
class DataSourceBinding:
    """Binds a widget to a data source with query configuration."""

    source_type: DataSourceType
    source_id: str | int | None = None
    query: str | None = None
    filters: dict[str, Any] = field(default_factory=dict)
    aggregation: str = "sum"
    group_by: str | None = None
    time_field: str | None = None
    limit: int | None = None

    def to_dict(self) -> dict:
        return {
            "source_type": self.source_type.value,
            "source_id": self.source_id,
            "query": self.query,
            "filters": self.filters,
            "aggregation": self.aggregation,
            "group_by": self.group_by,
            "time_field": self.time_field,
            "limit": self.limit,
        }

    @classmethod
    def from_dict(cls, data: dict) -> DataSourceBinding:
        return cls(
            source_type=DataSourceType(data.get("source_type", "dataset")),
            source_id=data.get("source_id"),
            query=data.get("query"),
            filters=data.get("filters", {}),
            aggregation=data.get("aggregation", "sum"),
            group_by=data.get("group_by"),
            time_field=data.get("time_field"),
            limit=data.get("limit"),
        )


@dataclass
class WidgetDefinition:
    """A reusable widget definition with data source binding and permissions."""

    key: str
    widget_type: WidgetType
    title: str
    description: str = ""
    chart_subtype: ChartSubType | None = None
    data_source: DataSourceBinding | None = None
    permission: str = "dashboard.view"
    industries: list[str] = field(default_factory=list)  # empty = all industries
    roles: list[str] = field(default_factory=list)  # empty = all roles
    config: dict[str, Any] = field(default_factory=dict)
    width: int = 6  # grid columns (1-12)
    height: int = 300  # pixels
    order: int = 0
    group: str = "Overview"

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "widget_type": self.widget_type.value,
            "title": self.title,
            "description": self.description,
            "chart_subtype": self.chart_subtype.value if self.chart_subtype else None,
            "data_source": self.data_source.to_dict() if self.data_source else None,
            "permission": self.permission,
            "industries": self.industries,
            "roles": self.roles,
            "config": self.config,
            "width": self.width,
            "height": self.height,
            "order": self.order,
            "group": self.group,
        }

    @classmethod
    def from_dict(cls, data: dict) -> WidgetDefinition:
        ds_data = data.get("data_source")
        return cls(
            key=data["key"],
            widget_type=WidgetType(data.get("widget_type", "kpi_card")),
            title=data.get("title", ""),
            description=data.get("description", ""),
            chart_subtype=(
                ChartSubType(data["chart_subtype"]) if data.get("chart_subtype") else None
            ),
            data_source=DataSourceBinding.from_dict(ds_data) if ds_data else None,
            permission=data.get("permission", "dashboard.view"),
            industries=data.get("industries", []),
            roles=data.get("roles", []),
            config=data.get("config", {}),
            width=data.get("width", 6),
            height=data.get("height", 300),
            order=data.get("order", 0),
            group=data.get("group", "Overview"),
        )


@dataclass
class DashboardComposition:
    """A composed dashboard with widgets, filtered by industry and permissions."""

    dashboard_id: str
    name: str
    description: str = ""
    industry: str = "generic"
    widgets: list[WidgetDefinition] = field(default_factory=list)
    layout: dict[str, list[str]] = field(default_factory=dict)
    created_by: str = ""
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict:
        return {
            "dashboard_id": self.dashboard_id,
            "name": self.name,
            "description": self.description,
            "industry": self.industry,
            "widgets": [w.to_dict() for w in self.widgets],
            "layout": self.layout,
            "created_by": self.created_by,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


# â”€â”€ Widget Registry â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


class WidgetRegistry:
    """Registry of reusable widget definitions, filterable by industry and role."""

    _widgets: dict[str, WidgetDefinition] = {}

    @classmethod
    def register(cls, widget: WidgetDefinition) -> None:
        cls._widgets[widget.key] = widget
        logger.debug(f"Registered widget: {widget.key} ({widget.widget_type})")

    @classmethod
    def get(cls, key: str) -> WidgetDefinition | None:
        return cls._widgets.get(key)

    @classmethod
    def all(cls) -> list[WidgetDefinition]:
        return list(cls._widgets.values())

    @classmethod
    def by_type(cls, widget_type: WidgetType) -> list[WidgetDefinition]:
        return [w for w in cls._widgets.values() if w.widget_type == widget_type]

    @classmethod
    def by_industry(
        cls,
        industry: str,
        permissions: list[str] | None = None,
        roles: list[str] | None = None,
    ) -> list[WidgetDefinition]:
        """Return widgets available for a given industry, filtered by permissions and roles."""
        result = []
        for widget in cls._widgets.values():
            if (
                widget.industries
                and industry not in widget.industries
                and "generic" not in widget.industries
            ):
                continue
            if permissions and widget.permission and widget.permission not in permissions:
                continue
            if roles and widget.roles and not any(r in roles for r in widget.roles):
                continue
            result.append(widget)
        return sorted(result, key=lambda w: w.order)

    @classmethod
    def supported_types(cls) -> list[str]:
        return sorted({w.widget_type.value for w in cls._widgets.values()})


# â”€â”€ Dashboard Composition Service â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


class DashboardCompositionService:
    """Service for composing dashboards from widgets, adapted by industry."""

    def __init__(self):
        self._dashboards: dict[str, DashboardComposition] = {}

    def compose(
        self,
        name: str,
        industry: str,
        widget_keys: list[str] | None = None,
        permissions: list[str] | None = None,
        roles: list[str] | None = None,
        description: str = "",
        created_by: str = "",
    ) -> DashboardComposition:
        """Compose a dashboard from widget keys, or all industry-applicable widgets."""
        if widget_keys:
            widgets = [WidgetRegistry.get(k) for k in widget_keys if WidgetRegistry.get(k)]
            widgets = [w for w in widgets if w is not None]
        else:
            widgets = WidgetRegistry.by_industry(industry, permissions, roles)

        layout = self._build_layout(widgets)

        dashboard = DashboardComposition(
            dashboard_id=f"dash_{industry}_{len(self._dashboards) + 1}",
            name=name,
            description=description,
            industry=industry,
            widgets=widgets,
            layout=layout,
            created_by=created_by,
        )
        self._dashboards[dashboard.dashboard_id] = dashboard
        logger.info(
            f"Composed dashboard {dashboard.dashboard_id} with {len(widgets)} widgets for industry={industry}"
        )
        return dashboard

    def get(self, dashboard_id: str) -> DashboardComposition | None:
        return self._dashboards.get(dashboard_id)

    def list_by_industry(self, industry: str) -> list[DashboardComposition]:
        return [d for d in self._dashboards.values() if d.industry == industry]

    def add_widget(self, dashboard_id: str, widget_key: str) -> DashboardComposition | None:
        dashboard = self._dashboards.get(dashboard_id)
        if not dashboard:
            return None
        widget = WidgetRegistry.get(widget_key)
        if not widget:
            return None
        dashboard.widgets.append(widget)
        self._rebuild_layout(dashboard)
        return dashboard

    def remove_widget(self, dashboard_id: str, widget_key: str) -> DashboardComposition | None:
        dashboard = self._dashboards.get(dashboard_id)
        if not dashboard:
            return None
        dashboard.widgets = [w for w in dashboard.widgets if w.key != widget_key]
        self._rebuild_layout(dashboard)
        return dashboard

    def _build_layout(self, widgets: list[WidgetDefinition]) -> dict[str, list[str]]:
        layout: dict[str, list[str]] = {}
        for w in sorted(widgets, key=lambda x: x.order):
            if w.group not in layout:
                layout[w.group] = []
            layout[w.group].append(w.key)
        return layout

    def _rebuild_layout(self, dashboard: DashboardComposition) -> None:
        dashboard.layout = self._build_layout(dashboard.widgets)
