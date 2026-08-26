"""Canonical Chart Specification â€” the single source of truth.

Every visualization in the platform (dashboard, report, PPTX) derives
from the same ChartSpecification object.  This prevents the
long-standing bug where the dashboard shows a chart but the PPTX
silently omits it because each subsystem independently recreates
its own chart representation.

Architecture:

                    ANALYSIS
                       â”‚
                       â–¼
              CHART SPECIFICATIONS   â† this file
                       â”‚
          â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
          â–¼            â–¼            â–¼
      DASHBOARD      REPORT        PPTX
          â”‚            â”‚            â”‚
          â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                       â–¼
                  SAME DATA
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class ChartSpecification:
    """Canonical chart specification â€” the single source of truth.

    This object is produced once by the IntelligentChartSelectionEngine
    and consumed by the dashboard layout engine, the report engine, and
    the presentation layout engine.  None of those consumers may create
    their own independent chart representations.
    """

    # â”€â”€ Identity â”€â”€
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    # â”€â”€ Chart type & metadata â”€â”€
    chart_type: str = ""  # bar_chart, line_chart, pie_chart, scatter_plot, histogram, heatmap, etc.
    title: str = ""
    description: str = ""

    # â”€â”€ Data bindings â”€â”€
    x_axis: str | None = None
    y_axis: str | None = None
    z_axis: str | None = None  # for heatmaps
    group_by: str | None = None
    aggregation: str = "sum"  # sum, count, avg, min, max, median
    source_columns: list[str] = field(default_factory=list)

    # â”€â”€ Pre-computed chart data (the actual numbers to plot) â”€â”€
    # This is populated by the deterministic statistical engine,
    # never by AI.  AI may explain the data but never invent it.
    data: list[dict[str, Any]] = field(default_factory=list)
    series: list[dict[str, Any]] = field(default_factory=list)

    # â”€â”€ Scoring & reasoning â”€â”€
    importance_score: float = 0.0  # 0-100
    confidence: float = 0.0  # 0-1
    reason: str = ""  # "Why this chart?" explanation
    source_analysis: str = ""  # what analysis produced this chart

    # â”€â”€ Layout hints (consumed by dashboard & presentation engines) â”€â”€
    section: str = ""  # primary_charts, supporting_charts, kpi_row
    width: int = 6  # grid columns (1-12)
    height: int = 300  # pixels for dashboard
    order: int = 0  # display order

    # â”€â”€ Filters applicable to this chart â”€â”€
    filters: list[str] = field(default_factory=list)

    # â”€â”€ Versioning â”€â”€
    version: int = 1
    dataset_hash: str = ""  # hash of the source dataset for invalidation
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    # â”€â”€ PPTX-specific placement (populated by PresentationLayoutEngine) â”€â”€
    pptx_placement: dict[str, float] | None = None  # {x, y, width, height} in inches

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "chart_type": self.chart_type,
            "title": self.title,
            "description": self.description,
            "x_axis": self.x_axis,
            "y_axis": self.y_axis,
            "z_axis": self.z_axis,
            "group_by": self.group_by,
            "aggregation": self.aggregation,
            "source_columns": self.source_columns,
            "data": self.data,
            "series": self.series,
            "importance_score": round(self.importance_score, 1),
            "confidence": round(self.confidence, 3),
            "reason": self.reason,
            "source_analysis": self.source_analysis,
            "section": self.section,
            "width": self.width,
            "height": self.height,
            "order": self.order,
            "filters": self.filters,
            "version": self.version,
            "dataset_hash": self.dataset_hash,
            "created_at": self.created_at,
            "pptx_placement": self.pptx_placement,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ChartSpecification:
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            chart_type=data.get("chart_type", ""),
            title=data.get("title", ""),
            description=data.get("description", ""),
            x_axis=data.get("x_axis"),
            y_axis=data.get("y_axis"),
            z_axis=data.get("z_axis"),
            group_by=data.get("group_by"),
            aggregation=data.get("aggregation", "sum"),
            source_columns=data.get("source_columns", []),
            data=data.get("data", []),
            series=data.get("series", []),
            importance_score=data.get("importance_score", 0.0),
            confidence=data.get("confidence", 0.0),
            reason=data.get("reason", ""),
            source_analysis=data.get("source_analysis", ""),
            section=data.get("section", ""),
            width=data.get("width", 6),
            height=data.get("height", 300),
            order=data.get("order", 0),
            filters=data.get("filters", []),
            version=data.get("version", 1),
            dataset_hash=data.get("dataset_hash", ""),
            created_at=data.get("created_at", ""),
            pptx_placement=data.get("pptx_placement"),
        )

    def content_hash(self) -> str:
        """Hash of chart content for change detection / deduplication."""
        content = json.dumps(
            {
                "chart_type": self.chart_type,
                "x_axis": self.x_axis,
                "y_axis": self.y_axis,
                "z_axis": self.z_axis,
                "aggregation": self.aggregation,
                "source_columns": sorted(self.source_columns),
            },
            sort_keys=True,
        )
        return hashlib.sha256(content.encode()).hexdigest()[:16]


@dataclass
class KPISpecification:
    """Canonical KPI specification with computed value."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    key: str = ""
    label: str = ""
    value: float | int | str = 0
    unit: str = ""
    metric: str = ""  # sum, count, avg, min, max, median, custom
    category: str = ""  # operational, financial, clinical, academic, etc.
    source_columns: list[str] = field(default_factory=list)
    aggregation: str = "sum"
    confidence: float = 1.0
    icon: str = "ðŸ“Š"
    description: str = ""
    time_context: str = ""
    comparison_value: float | int | None = None
    comparison_label: str = ""
    comparison_direction: str = ""  # up, down, flat
    order: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "key": self.key,
            "label": self.label,
            "value": self.value,
            "unit": self.unit,
            "metric": self.metric,
            "category": self.category,
            "source_columns": self.source_columns,
            "aggregation": self.aggregation,
            "confidence": round(self.confidence, 2),
            "icon": self.icon,
            "description": self.description,
            "time_context": self.time_context,
            "comparison_value": self.comparison_value,
            "comparison_label": self.comparison_label,
            "comparison_direction": self.comparison_direction,
            "order": self.order,
        }


@dataclass
class InsightSpecification:
    """Canonical insight specification generated from real computed data."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    severity: str = "info"  # info, warning, critical, positive
    insight_type: str = ""  # trend, anomaly, correlation, dominance, quality, comparison
    metric: str = ""
    value: float | None = None
    recommendation: str = ""
    source_data: str = ""  # reference to the computed data that supports this insight
    priority: int = 0  # higher = more important
    order: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "severity": self.severity,
            "insight_type": self.insight_type,
            "metric": self.metric,
            "value": self.value,
            "recommendation": self.recommendation,
            "source_data": self.source_data,
            "priority": self.priority,
            "order": self.order,
        }


@dataclass
class FilterSpecification:
    """Canonical filter specification."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    filter_type: str = ""  # date_range, single_select, multi_select
    label: str = ""
    column: str = ""
    entity: str | None = None
    default_value: Any = None
    options: list[Any] = field(default_factory=list)
    order: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "filter_type": self.filter_type,
            "label": self.label,
            "column": self.column,
            "entity": self.entity,
            "default_value": self.default_value,
            "options": self.options,
            "order": self.order,
        }


@dataclass
class DashboardSpecification:
    """Complete auto-generated dashboard specification.

    This is the top-level object that the IntelligentDashboardLayoutEngine
    produces.  It contains all KPIs, charts, filters, insights, and
    layout information.  The report and presentation engines consume
    the same chart specifications from this object.
    """

    dashboard_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    subtitle: str = ""
    industry: str = "unknown"
    dataset_name: str = ""
    dataset_hash: str = ""

    kpis: list[KPISpecification] = field(default_factory=list)
    charts: list[ChartSpecification] = field(default_factory=list)
    filters: list[FilterSpecification] = field(default_factory=list)
    insights: list[InsightSpecification] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)

    # Layout: sections â†’ list of component IDs
    layout: dict[str, list[str]] = field(default_factory=dict)
    grid_columns: int = 12
    responsive: bool = True

    # Responsive breakpoints
    tablet_columns: int = 8
    mobile_columns: int = 4

    version: int = 1
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    is_custom: bool = False

    # User mode
    mode: str = "auto"  # auto, expert

    def to_dict(self) -> dict[str, Any]:
        return {
            "dashboard_id": self.dashboard_id,
            "title": self.title,
            "subtitle": self.subtitle,
            "industry": self.industry,
            "dataset_name": self.dataset_name,
            "dataset_hash": self.dataset_hash,
            "kpis": [k.to_dict() for k in self.kpis],
            "charts": [c.to_dict() for c in self.charts],
            "filters": [f.to_dict() for f in self.filters],
            "insights": [i.to_dict() for i in self.insights],
            "recommendations": self.recommendations,
            "layout": self.layout,
            "grid_columns": self.grid_columns,
            "responsive": self.responsive,
            "tablet_columns": self.tablet_columns,
            "mobile_columns": self.mobile_columns,
            "version": self.version,
            "created_at": self.created_at,
            "is_custom": self.is_custom,
            "mode": self.mode,
        }


@dataclass
class PresentationSpecification:
    """Complete auto-generated presentation specification.

    Produced by the PresentationLayoutEngine.  Uses the SAME chart
    specifications as the dashboard â€” never creates independent charts.
    """

    presentation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    subtitle: str = ""
    template: str = "executive"

    slides: list[dict[str, Any]] = field(default_factory=list)

    # Chart IDs that were included in the presentation
    included_chart_ids: list[str] = field(default_factory=list)
    # Chart IDs that were intentionally excluded, with reasons
    excluded_charts: list[dict[str, str]] = field(default_factory=list)

    # Validation results
    validation: dict[str, Any] = field(default_factory=dict)

    version: int = 1
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "presentation_id": self.presentation_id,
            "title": self.title,
            "subtitle": self.subtitle,
            "template": self.template,
            "slides": self.slides,
            "included_chart_ids": self.included_chart_ids,
            "excluded_charts": self.excluded_charts,
            "validation": self.validation,
            "version": self.version,
            "created_at": self.created_at,
        }
