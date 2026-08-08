"""Dashboard Layout Engine.

Generates responsive dashboard layouts automatically.

Layout structure:
  1. Filter bar at the top
  2. KPI cards in a row
  3. Primary charts prominently (full width or 2-column)
  4. Supporting charts below (2-3 column grid)
  5. AI insight panel on the side
  6. Detail table at the bottom

Supports multiple saved layouts and responsive design.
"""

from __future__ import annotations

import logging

from services.dashboard_engine import (
    ChartDefinition,
    DashboardLayout,
    KPIDefinition,
    LayoutSection,
)

logger = logging.getLogger(__name__)


class DashboardLayoutEngine:
    """Generates and manages dashboard layouts."""

    def generate_layout(
        self,
        kpis: list[KPIDefinition],
        charts: list[ChartDefinition],
        show_filters: bool = True,
        show_ai_insights: bool = True,
    ) -> DashboardLayout:
        """Generate a layout from KPIs and charts.

        Args:
            kpis: List of KPI definitions.
            charts: List of chart definitions.
            show_filters: Whether to show filter bar.
            show_ai_insights: Whether to show AI insights panel.

        Returns:
            DashboardLayout with sections and widget placement.
        """
        sections: dict[str, list[str]] = {}

        # Section 1: Filter bar
        if show_filters:
            sections[LayoutSection.FILTER_BAR.value] = ["filter_bar"]

        # Section 2: KPI row
        kpi_ids = [kpi.key for kpi in kpis[:8]]  # Max 8 KPI cards
        sections[LayoutSection.KPI_ROW.value] = kpi_ids

        # Section 3: Primary charts (high confidence, time series, geo)
        primary = [c for c in charts if c.section == LayoutSection.PRIMARY_CHARTS.value]
        primary.sort(key=lambda c: c.confidence, reverse=True)
        primary = primary[:4]

        # Assign widths for primary charts
        for i, chart in enumerate(primary):
            if i == 0 and chart.chart_type in ("geo_map", "line_chart"):
                chart.width = 12  # Full width for first primary
            else:
                chart.width = 6  # Half width

        sections[LayoutSection.PRIMARY_CHARTS.value] = [c.id for c in primary]

        # Section 4: Supporting charts
        supporting = [c for c in charts if c.section == LayoutSection.SUPPORTING_CHARTS.value]
        supporting.sort(key=lambda c: c.confidence, reverse=True)
        supporting = supporting[:8]

        # Assign widths for supporting charts
        for _i, chart in enumerate(supporting):
            if chart.chart_type in ("pie_chart", "donut_chart", "gauge"):
                chart.width = 4  # Third width
            else:
                chart.width = 6  # Half width

        sections[LayoutSection.SUPPORTING_CHARTS.value] = [c.id for c in supporting]

        # Section 5: AI insights
        if show_ai_insights:
            sections[LayoutSection.AI_INSIGHTS.value] = ["ai_insights"]

        # Section 6: Detail table
        sections[LayoutSection.DETAIL_TABLE.value] = ["detail_table"]

        return DashboardLayout(
            sections=sections,
            grid_columns=12,
            responsive=True,
            show_ai_insights=show_ai_insights,
            show_filters=show_filters,
        )

    def generate_compact_layout(
        self,
        kpis: list[KPIDefinition],
        charts: list[ChartDefinition],
    ) -> DashboardLayout:
        """Generate a compact layout (fewer charts, smaller KPI row)."""
        sections: dict[str, list[str]] = {}

        sections[LayoutSection.FILTER_BAR.value] = ["filter_bar"]
        sections[LayoutSection.KPI_ROW.value] = [kpi.key for kpi in kpis[:4]]

        # Only top 4 charts
        top_charts = sorted(charts, key=lambda c: c.confidence, reverse=True)[:4]
        for chart in top_charts:
            chart.width = 6

        sections[LayoutSection.PRIMARY_CHARTS.value] = [c.id for c in top_charts]
        sections[LayoutSection.AI_INSIGHTS.value] = ["ai_insights"]

        return DashboardLayout(
            sections=sections,
            grid_columns=12,
            responsive=True,
            show_ai_insights=True,
            show_filters=True,
        )

    def generate_mobile_layout(
        self,
        kpis: list[KPIDefinition],
        charts: list[ChartDefinition],
    ) -> DashboardLayout:
        """Generate a mobile-friendly layout (single column)."""
        sections: dict[str, list[str]] = {}

        sections[LayoutSection.FILTER_BAR.value] = ["filter_bar"]
        sections[LayoutSection.KPI_ROW.value] = [kpi.key for kpi in kpis[:4]]

        # All charts full width, stacked
        for chart in charts[:6]:
            chart.width = 12

        sections[LayoutSection.PRIMARY_CHARTS.value] = [c.id for c in charts[:6]]
        sections[LayoutSection.AI_INSIGHTS.value] = ["ai_insights"]

        return DashboardLayout(
            sections=sections,
            grid_columns=12,
            responsive=True,
            show_ai_insights=True,
            show_filters=True,
        )

    def generate_executive_layout(
        self,
        kpis: list[KPIDefinition],
        charts: list[ChartDefinition],
    ) -> DashboardLayout:
        """Generate an executive layout (KPIs first, minimal charts)."""
        sections: dict[str, list[str]] = {}

        sections[LayoutSection.KPI_ROW.value] = [kpi.key for kpi in kpis[:6]]

        # Only top 2 charts
        top_charts = sorted(charts, key=lambda c: c.confidence, reverse=True)[:2]
        for chart in top_charts:
            chart.width = 6

        sections[LayoutSection.PRIMARY_CHARTS.value] = [c.id for c in top_charts]
        sections[LayoutSection.AI_INSIGHTS.value] = ["ai_insights"]

        return DashboardLayout(
            sections=sections,
            grid_columns=12,
            responsive=True,
            show_ai_insights=True,
            show_filters=False,
        )

    def get_layout_templates(self) -> list[dict]:
        """Return available layout templates."""
        return [
            {
                "key": "standard",
                "name": "Standard",
                "description": "Balanced layout with filters, KPIs, and charts",
            },
            {
                "key": "compact",
                "name": "Compact",
                "description": "Fewer charts, focused on key metrics",
            },
            {
                "key": "mobile",
                "name": "Mobile",
                "description": "Single-column layout for mobile devices",
            },
            {
                "key": "executive",
                "name": "Executive",
                "description": "KPI-first layout with minimal charts",
            },
        ]

    def apply_template(
        self,
        template_key: str,
        kpis: list[KPIDefinition],
        charts: list[ChartDefinition],
    ) -> DashboardLayout:
        """Apply a layout template."""
        if template_key == "compact":
            return self.generate_compact_layout(kpis, charts)
        elif template_key == "mobile":
            return self.generate_mobile_layout(kpis, charts)
        elif template_key == "executive":
            return self.generate_executive_layout(kpis, charts)
        else:
            return self.generate_layout(kpis, charts)
