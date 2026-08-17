"""Presentation Layout Engine.

Automatically determines:
  - Number of slides
  - Slide order
  - Charts per slide (1-2 max)
  - Chart placement (x, y, width, height in inches)
  - Titles, captions, and supporting insights
  - Validation: no overlaps, no cropping, no off-slide content

Uses the SAME ChartSpecification objects as the dashboard — never
creates independent chart representations.

PPTX dimensions: 13.333 × 7.5 inches (16:9 widescreen)

Slide structure:
  1. Title slide
  2. Executive Summary (KPIs)
  3-N. Chart slides (1 chart per slide for readability)
  N+1. Key Insights
  N+2. Recommendations
  N+3. Thank You / Q&A
"""

from __future__ import annotations

import logging
from typing import Any

from services.auto.chart_specification import (
    ChartSpecification,
    DashboardSpecification,
    InsightSpecification,
    KPISpecification,
    PresentationSpecification,
)

logger = logging.getLogger(__name__)


class PresentationLayoutEngine:
    """Generates intelligent PPTX presentation layouts with validated chart placement."""

    # PPTX dimensions (16:9 widescreen)
    SLIDE_WIDTH = 13.333
    SLIDE_HEIGHT = 7.5

    # Margins
    MARGIN = 0.5
    TITLE_HEIGHT = 1.0
    CONTENT_TOP = 1.5

    # Chart placement defaults
    CHART_LEFT = 0.75
    CHART_TOP = 1.75
    CHART_WIDTH = 11.8
    CHART_HEIGHT = 5.25

    # Two-chart layout
    CHART_LEFT_HALF = 0.5
    CHART_WIDTH_HALF = 6.0

    # KPI card dimensions
    KPI_CARD_WIDTH = 2.8
    KPI_CARD_HEIGHT = 1.5
    KPI_GAP = 0.3

    MAX_CHART_SLIDES = 10

    def generate_presentation(
        self,
        dashboard: DashboardSpecification,
        template: str = "executive",
        max_chart_slides: int | None = None,
    ) -> PresentationSpecification:
        """Generate a complete presentation specification.

        Args:
            dashboard: DashboardSpecification with charts, KPIs, insights.
            template: Presentation template (executive, analytical, research, pitch).
            max_chart_slides: Maximum number of chart slides.

        Returns:
            PresentationSpecification with validated slide layout.
        """
        max_chart_slides = max_chart_slides or self.MAX_CHART_SLIDES

        # Select charts for presentation (sorted by importance)
        presentation_charts = sorted(
            dashboard.charts, key=lambda c: c.importance_score, reverse=True
        )
        presentation_charts = presentation_charts[:max_chart_slides]

        slides: list[dict[str, Any]] = []
        included_chart_ids: list[str] = []
        excluded_charts: list[dict[str, str]] = []

        # Track which charts were excluded and why
        for chart in dashboard.charts:
            if chart.id not in [c.id for c in presentation_charts]:
                excluded_charts.append(
                    {
                        "chart_id": chart.id,
                        "title": chart.title,
                        "reason": "Exceeded maximum chart slides limit",
                    }
                )

        # ── Slide 1: Title ──
        slides.append(
            {
                "slide_number": 1,
                "layout": "title",
                "title": dashboard.title,
                "subtitle": dashboard.subtitle or f"Generated from {dashboard.dataset_name}",
                "speaker_notes": f"Welcome. Today we'll cover {dashboard.title}. This presentation was automatically generated from your dataset.",
            }
        )

        # ── Slide 2: Executive Summary (KPIs) ──
        if dashboard.kpis:
            kpi_slide = self._make_kpi_slide(dashboard.kpis, slide_number=len(slides) + 1)
            slides.append(kpi_slide)

        # ── Slides 3-N: Chart slides (1 chart per slide) ──
        for _i, chart in enumerate(presentation_charts):
            slide = self._make_chart_slide(chart, slide_number=len(slides) + 1)
            slides.append(slide)
            included_chart_ids.append(chart.id)

        # ── Key Insights slide ──
        if dashboard.insights:
            slide = self._make_insights_slide(dashboard.insights, slide_number=len(slides) + 1)
            slides.append(slide)

        # ── Recommendations slide ──
        if dashboard.recommendations:
            slide = self._make_recommendations_slide(
                dashboard.recommendations, slide_number=len(slides) + 1
            )
            slides.append(slide)

        # ── Closing slide ──
        slides.append(
            {
                "slide_number": len(slides) + 1,
                "layout": "title",
                "title": "Thank You",
                "subtitle": "Questions & Discussion",
                "speaker_notes": "Open the floor for questions.",
            }
        )

        # Validate all placements
        validation = self._validate_presentation(slides)

        return PresentationSpecification(
            title=dashboard.title,
            subtitle=dashboard.subtitle,
            template=template,
            slides=slides,
            included_chart_ids=included_chart_ids,
            excluded_charts=excluded_charts,
            validation=validation,
        )

    # ── Slide factories ──

    def _make_kpi_slide(self, kpis: list[KPISpecification], slide_number: int) -> dict[str, Any]:
        """Create a KPI summary slide with validated card placements."""
        # Calculate KPI card positions
        n_kpis = min(len(kpis), 6)
        cards = []

        # Layout: 2 rows of up to 3 KPIs each
        per_row = min(3, n_kpis)
        total_width = per_row * self.KPI_CARD_WIDTH + (per_row - 1) * self.KPI_GAP
        start_left = (self.SLIDE_WIDTH - total_width) / 2

        for i, kpi in enumerate(kpis[:n_kpis]):
            row = i // per_row
            col = i % per_row

            x = start_left + col * (self.KPI_CARD_WIDTH + self.KPI_GAP)
            y = self.CONTENT_TOP + row * (self.KPI_CARD_HEIGHT + self.KPI_GAP)

            cards.append(
                {
                    "label": kpi.label,
                    "value": f"{kpi.value}{kpi.unit}" if kpi.unit else str(kpi.value),
                    "icon": kpi.icon,
                    "comparison": kpi.comparison_label if kpi.comparison_value is not None else "",
                    "comparison_direction": kpi.comparison_direction,
                    "placement": {
                        "x": round(x, 2),
                        "y": round(y, 2),
                        "width": self.KPI_CARD_WIDTH,
                        "height": self.KPI_CARD_HEIGHT,
                    },
                }
            )

        return {
            "slide_number": slide_number,
            "layout": "kpi",
            "title": "Key Performance Indicators",
            "kpi_cards": cards,
            "speaker_notes": "Walk through the most important metrics and their trends.",
        }

    def _make_chart_slide(self, chart: ChartSpecification, slide_number: int) -> dict[str, Any]:
        """Create a chart slide with validated placement."""
        placement = {
            "x": self.CHART_LEFT,
            "y": self.CHART_TOP,
            "width": self.CHART_WIDTH,
            "height": self.CHART_HEIGHT,
        }

        # Store placement in the chart spec for PPTX rendering
        chart.pptx_placement = placement

        return {
            "slide_number": slide_number,
            "layout": "chart",
            "title": chart.title,
            "chart_id": chart.id,
            "chart_type": chart.chart_type,
            "chart_data": chart.data,
            "x_axis": chart.x_axis,
            "y_axis": chart.y_axis,
            "aggregation": chart.aggregation,
            "chart_placement": placement,
            "caption": chart.description,
            "reason": chart.reason,
            "speaker_notes": f"Discuss the {chart.chart_type} showing {chart.title}. {chart.reason}",
        }

    def _make_insights_slide(
        self, insights: list[InsightSpecification], slide_number: int
    ) -> dict[str, Any]:
        """Create an insights slide."""
        top_insights = insights[:5]
        content_lines = []
        for insight in top_insights:
            icon = (
                "⚠️"
                if insight.severity == "critical"
                else "✅" if insight.severity == "positive" else "•"
            )
            content_lines.append(f"{icon} {insight.title}: {insight.description}")

        return {
            "slide_number": slide_number,
            "layout": "bullets",
            "title": "Key Insights",
            "content": "\n".join(content_lines),
            "insights": [i.to_dict() for i in top_insights],
            "speaker_notes": "Discuss each insight with supporting evidence from the data.",
        }

    def _make_recommendations_slide(
        self, recommendations: list[str], slide_number: int
    ) -> dict[str, Any]:
        """Create a recommendations slide."""
        content = "\n".join(f"• {r}" for r in recommendations[:6])
        return {
            "slide_number": slide_number,
            "layout": "bullets",
            "title": "Recommendations",
            "content": content,
            "speaker_notes": "Present clear, actionable recommendations with expected impact.",
        }

    # ── Validation ──

    def _validate_presentation(self, slides: list[dict[str, Any]]) -> dict[str, Any]:
        """Validate that all chart placements are within slide bounds and no overlaps."""
        errors: list[str] = []
        warnings: list[str] = []

        for slide in slides:
            slide_num = slide.get("slide_number", 0)

            # Validate chart placement
            if slide.get("layout") == "chart":
                placement = slide.get("chart_placement", {})
                x = placement.get("x", 0)
                y = placement.get("y", 0)
                w = placement.get("width", 0)
                h = placement.get("height", 0)

                # Check bounds
                if x < 0 or y < 0:
                    errors.append(f"Slide {slide_num}: Chart placement has negative coordinates")
                if x + w > self.SLIDE_WIDTH:
                    errors.append(
                        f"Slide {slide_num}: Chart extends beyond slide width ({x+w:.2f} > {self.SLIDE_WIDTH})"
                    )
                if y + h > self.SLIDE_HEIGHT:
                    errors.append(
                        f"Slide {slide_num}: Chart extends beyond slide height ({y+h:.2f} > {self.SLIDE_HEIGHT})"
                    )
                if w < 2 or h < 2:
                    warnings.append(
                        f"Slide {slide_num}: Chart is too small ({w:.1f}×{h:.1f} inches)"
                    )

            # Validate KPI card placements
            if slide.get("layout") == "kpi":
                cards = slide.get("kpi_cards", [])
                for i, card in enumerate(cards):
                    p = card.get("placement", {})
                    x = p.get("x", 0)
                    y = p.get("y", 0)
                    w = p.get("width", 0)
                    h = p.get("height", 0)

                    if x < 0 or y < 0:
                        errors.append(f"Slide {slide_num}: KPI card {i} has negative coordinates")
                    if x + w > self.SLIDE_WIDTH:
                        errors.append(f"Slide {slide_num}: KPI card {i} extends beyond slide width")
                    if y + h > self.SLIDE_HEIGHT:
                        errors.append(
                            f"Slide {slide_num}: KPI card {i} extends beyond slide height"
                        )

                    # Check overlap with previous cards
                    for j in range(i):
                        prev = cards[j].get("placement", {})
                        if self._rectangles_overlap(
                            x,
                            y,
                            w,
                            h,
                            prev.get("x", 0),
                            prev.get("y", 0),
                            prev.get("width", 0),
                            prev.get("height", 0),
                        ):
                            errors.append(f"Slide {slide_num}: KPI cards {i} and {j} overlap")

        # Check for empty slides
        for slide in slides:
            layout = slide.get("layout", "")
            if layout == "bullets" and not slide.get("content"):
                warnings.append(
                    f"Slide {slide.get('slide_number', 0)}: Bullet slide has no content"
                )
            if layout == "chart" and not slide.get("chart_data"):
                warnings.append(
                    f"Slide {slide.get('slide_number', 0)}: Chart slide has no chart data"
                )

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "slide_count": len(slides),
        }

    @staticmethod
    def _rectangles_overlap(
        x1: float,
        y1: float,
        w1: float,
        h1: float,
        x2: float,
        y2: float,
        w2: float,
        h2: float,
    ) -> bool:
        """Check if two rectangles overlap."""
        return not (x1 + w1 <= x2 or x2 + w2 <= x1 or y1 + h1 <= y2 or y2 + h2 <= y1)
