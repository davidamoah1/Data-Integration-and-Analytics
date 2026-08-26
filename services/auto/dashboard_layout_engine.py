"""Intelligent Dashboard Layout Engine.

Automatically decides:
  - Which charts appear on the dashboard
  - Their order, size, and position
  - KPI row placement
  - Filter bar placement
  - Insights section placement
  - Responsive grid layout

Dashboard hierarchy (top to bottom):
  1. Filter bar (if filters exist)
  2. Executive KPI row
  3. Primary chart (most important, full width)
  4. Major comparisons (2-column)
  5. Secondary analysis (2-column)
  6. Detailed analysis (1 or 2-column)
  7. AI insights panel
"""

from __future__ import annotations

import logging

from services.auto.chart_specification import (
    ChartSpecification,
    DashboardSpecification,
    FilterSpecification,
    InsightSpecification,
    KPISpecification,
)

logger = logging.getLogger(__name__)


class IntelligentDashboardLayoutEngine:
    """Generates intelligent, responsive dashboard layouts."""

    # Grid system
    DESKTOP_COLUMNS = 12
    TABLET_COLUMNS = 8
    MOBILE_COLUMNS = 4

    # Section names
    FILTER_BAR = "filter_bar"
    KPI_ROW = "kpi_row"
    PRIMARY_CHARTS = "primary_charts"
    SUPPORTING_CHARTS = "supporting_charts"
    AI_INSIGHTS = "ai_insights"
    DETAIL_TABLE = "detail_table"

    def generate_layout(
        self,
        title: str,
        subtitle: str,
        industry: str,
        dataset_name: str,
        dataset_hash: str,
        kpis: list[KPISpecification],
        charts: list[ChartSpecification],
        filters: list[FilterSpecification],
        insights: list[InsightSpecification],
        recommendations: list[str] | None = None,
    ) -> DashboardSpecification:
        """Generate a complete dashboard specification with intelligent layout.

        Args:
            title: Dashboard title.
            subtitle: Dashboard subtitle.
            industry: Detected industry.
            dataset_name: Name of the source dataset.
            dataset_hash: Hash of the source dataset.
            kpis: KPI specifications.
            charts: Chart specifications.
            filters: Filter specifications.
            insights: Insight specifications.
            recommendations: Optional recommendations list.

        Returns:
            DashboardSpecification with layout.
        """
        dashboard = DashboardSpecification(
            title=title,
            subtitle=subtitle,
            industry=industry,
            dataset_name=dataset_name,
            dataset_hash=dataset_hash,
            kpis=kpis,
            charts=charts,
            filters=filters,
            insights=insights,
            recommendations=recommendations or [],
            grid_columns=self.DESKTOP_COLUMNS,
            tablet_columns=self.TABLET_COLUMNS,
            mobile_columns=self.MOBILE_COLUMNS,
        )

        # Build layout sections
        layout: dict[str, list[str]] = {}

        # 1. Filter bar
        if filters:
            layout[self.FILTER_BAR] = [f.id for f in filters]

        # 2. KPI row
        if kpis:
            layout[self.KPI_ROW] = [k.id for k in kpis]

        # 3. Assign charts to sections based on their section field
        primary_charts = [c for c in charts if c.section == "primary_charts"]
        supporting_charts = [c for c in charts if c.section == "supporting_charts"]

        # If no primary charts assigned, use the top 2 by score
        if not primary_charts and charts:
            primary_charts = charts[:2]
            supporting_charts = charts[2:]

        # Ensure at most 2 primary charts
        if len(primary_charts) > 2:
            supporting_charts = primary_charts[2:] + supporting_charts
            primary_charts = primary_charts[:2]

        # 4. Primary charts section
        layout[self.PRIMARY_CHARTS] = [c.id for c in primary_charts]

        # 5. Supporting charts section
        layout[self.SUPPORTING_CHARTS] = [c.id for c in supporting_charts]

        # 6. AI insights
        if insights:
            layout[self.AI_INSIGHTS] = [i.id for i in insights]

        dashboard.layout = layout

        # Adjust chart widths for responsive layout
        self._apply_responsive_widths(dashboard)

        return dashboard

    def _apply_responsive_widths(self, dashboard: DashboardSpecification) -> None:
        """Apply responsive width rules to charts based on their section."""
        for chart in dashboard.charts:
            if chart.section == "primary_charts":
                # Primary charts: full width on desktop, full on tablet/mobile
                chart.width = self.DESKTOP_COLUMNS
            elif chart.section == "supporting_charts":
                # Supporting charts: half width on desktop
                chart.width = self.DESKTOP_COLUMNS // 2
            else:
                chart.width = self.DESKTOP_COLUMNS // 2

    def generate_compact_layout(
        self,
        title: str,
        subtitle: str,
        industry: str,
        dataset_name: str,
        dataset_hash: str,
        kpis: list[KPISpecification],
        charts: list[ChartSpecification],
        filters: list[FilterSpecification],
        insights: list[InsightSpecification],
        recommendations: list[str] | None = None,
    ) -> DashboardSpecification:
        """Generate a compact dashboard (fewer charts, smaller KPIs)."""
        # Limit to 4 charts, 4 KPIs, 3 insights
        charts = charts[:4]
        kpis = kpis[:4]
        insights = insights[:3]

        dashboard = self.generate_layout(
            title=title,
            subtitle=subtitle,
            industry=industry,
            dataset_name=dataset_name,
            dataset_hash=dataset_hash,
            kpis=kpis,
            charts=charts,
            filters=filters,
            insights=insights,
            recommendations=recommendations,
        )

        # Compact: reduce heights
        for chart in dashboard.charts:
            chart.height = max(200, chart.height - 50)

        return dashboard

    def generate_mobile_layout(
        self,
        title: str,
        subtitle: str,
        industry: str,
        dataset_name: str,
        dataset_hash: str,
        kpis: list[KPISpecification],
        charts: list[ChartSpecification],
        filters: list[FilterSpecification],
        insights: list[InsightSpecification],
        recommendations: list[str] | None = None,
    ) -> DashboardSpecification:
        """Generate a mobile-optimized dashboard (single column)."""
        # Limit to 3 charts, 3 KPIs, 2 insights
        charts = charts[:3]
        kpis = kpis[:3]
        insights = insights[:2]

        dashboard = self.generate_layout(
            title=title,
            subtitle=subtitle,
            industry=industry,
            dataset_name=dataset_name,
            dataset_hash=dataset_hash,
            kpis=kpis,
            charts=charts,
            filters=filters,
            insights=insights,
            recommendations=recommendations,
        )

        # Mobile: all full width, reduced height
        for chart in dashboard.charts:
            chart.width = self.MOBILE_COLUMNS
            chart.height = 250

        dashboard.grid_columns = self.MOBILE_COLUMNS
        return dashboard

    def generate_executive_layout(
        self,
        title: str,
        subtitle: str,
        industry: str,
        dataset_name: str,
        dataset_hash: str,
        kpis: list[KPISpecification],
        charts: list[ChartSpecification],
        filters: list[FilterSpecification],
        insights: list[InsightSpecification],
        recommendations: list[str] | None = None,
    ) -> DashboardSpecification:
        """Generate an executive dashboard (KPIs + 1 primary chart + insights)."""
        # Executive: 6 KPIs, 1 primary chart, 3 insights, no filters
        charts = charts[:1]
        kpis = kpis[:6]
        insights = insights[:3]

        dashboard = self.generate_layout(
            title=title,
            subtitle=subtitle,
            industry=industry,
            dataset_name=dataset_name,
            dataset_hash=dataset_hash,
            kpis=kpis,
            charts=charts,
            filters=[],  # No filters in executive view
            insights=insights,
            recommendations=recommendations,
        )

        # Executive: larger chart height
        for chart in dashboard.charts:
            chart.height = 450

        return dashboard
