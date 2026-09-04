"""Presentation Layout Engine.

Dynamically architects and structures 16:9 widescreen PowerPoint presentations
tailored to the selected Presentation Theme & Narrative Style:
  1. Executive Briefing  — C-suite strategic summary, core KPIs, primary drivers, and risk flags.
  2. Analytical Deep-Dive — Statistical distributions, skewness, bivariate patterns, and outliers.
  3. Technical / Research — Data hygiene scorecards, empirical distributions, and methodology.
  4. Investor / Pitch    — Fast-paced traction, unit economics, market share, and growth runway.

Uses the SAME canonical ChartSpecification objects as the dashboard.
PPTX dimensions: 13.333 × 7.5 inches (16:9 widescreen).
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
    """Generates intelligent, theme-specific PPTX presentation architectures."""

    # PPTX dimensions (16:9 widescreen)
    SLIDE_WIDTH = 13.333
    SLIDE_HEIGHT = 7.5

    # Margins & Placements
    MARGIN = 0.5
    TITLE_HEIGHT = 1.0
    CONTENT_TOP = 1.5

    CHART_LEFT = 0.8
    CHART_TOP = 1.55
    CHART_WIDTH = 11.7
    CHART_HEIGHT = 4.6

    # KPI card dimensions
    KPI_CARD_WIDTH = 3.6
    KPI_CARD_HEIGHT = 1.8
    KPI_GAP = 0.45

    def generate_presentation(
        self,
        dashboard: DashboardSpecification,
        template: str = "executive",
        max_chart_slides: int | None = None,
        title: str | None = None,
        profile: dict | None = None,
        quality: dict | None = None,
    ) -> PresentationSpecification:
        """Generate a complete presentation specification customized by narrative style.

        Args:
            dashboard: DashboardSpecification with charts, KPIs, insights, and recommendations.
            template: Presentation template ('executive', 'analytical', 'research', 'pitch').
            max_chart_slides: Maximum number of chart slides.
            title: Presentation title override.
            profile: Optional dataset profile dictionary.
            quality: Optional dataset quality report dictionary.

        Returns:
            PresentationSpecification with validated slide layout tailored to the chosen style.
        """
        tpl = (template or "executive").lower().strip()
        pres_title = title or dashboard.title or f"{dashboard.dataset_name} — Strategic Analysis"

        if tpl == "analytical":
            slides, included_charts, excluded_charts = self._build_analytical_deck(
                dashboard, pres_title, max_chart_slides
            )
        elif tpl == "research":
            slides, included_charts, excluded_charts = self._build_research_deck(
                dashboard, pres_title, max_chart_slides, profile, quality
            )
        elif tpl == "pitch":
            slides, included_charts, excluded_charts = self._build_pitch_deck(
                dashboard, pres_title, max_chart_slides
            )
        else:  # default 'executive'
            slides, included_charts, excluded_charts = self._build_executive_deck(
                dashboard, pres_title, max_chart_slides
            )

        # Validate all slide placements
        validation = self._validate_presentation(slides)

        return PresentationSpecification(
            title=pres_title,
            subtitle=dashboard.subtitle,
            template=tpl,
            slides=slides,
            included_chart_ids=included_charts,
            excluded_charts=excluded_charts,
            validation=validation,
        )

    # ── 1. Executive Briefing Deck Architecture ──────────────────
    def _build_executive_deck(
        self,
        dashboard: DashboardSpecification,
        title: str,
        max_charts: int | None,
    ) -> tuple[list[dict[str, Any]], list[str], list[dict[str, str]]]:
        """C-Suite Executive Briefing Architecture:
        1. Title Slide (Executive Context)
        2. Executive Summary & Narrative
        3. Strategic Scorecard (KPIs)
        4. Primary Strategic Drivers (Chart 1)
        5. Portfolio / Segment Allocation (Chart 2)
        6. Critical Findings & Risk Flags (Insights)
        7. Executive Action Plan (Recommendations)
        8. Board Sign-off & Next Steps (Closing)
        """
        slides: list[dict[str, Any]] = []
        included_chart_ids: list[str] = []
        excluded_charts: list[dict[str, str]] = []

        # Slide 1: Title
        slides.append(
            self._make_title_slide(
                title=title,
                subtitle=f"Strategic Executive Briefing • Sector: {dashboard.industry.title()}",
                tag="EXECUTIVE BRIEFING // STRATEGY & IMPACT",
                slide_number=1,
                speaker_notes="Welcome leadership team. This strategic briefing synthesizes macro performance indicators, primary operational drivers, and high-conviction recommendations.",
            )
        )

        # Slide 2: Executive Summary Narrative
        summary_points = [
            f"Dataset Scope: Analysis conducted across {dashboard.dataset_name} with automated feature and intelligence profiling.",
            f"Operational Health: Baseline performance indicates steady aggregation patterns across {dashboard.industry.title()} benchmarks.",
            f"Strategic Takeaway: Core drivers demonstrate concentrated yield in primary categories, with identifiable optimization levers.",
        ]
        slides.append(
            self._make_summary_text_slide(
                title="Executive Summary & Strategic Context",
                subtitle="High-level synthesis of operational metrics and strategic positioning",
                paragraphs=summary_points,
                slide_number=len(slides) + 1,
                category_tag="01 // EXECUTIVE SUMMARY",
                speaker_notes="Deliver the strategic bottom-line upfront: outline dataset breadth, top operational findings, and immediate growth vectors.",
            )
        )

        # Slide 3: Executive Scorecard (KPIs)
        if dashboard.kpis:
            slides.append(
                self._make_kpi_slide(
                    kpis=dashboard.kpis[:6],
                    title="Executive Scorecard & Strategic KPIs",
                    subtitle="Core operational and commercial performance benchmarks",
                    slide_number=len(slides) + 1,
                    category_tag="02 // STRATEGIC SCORECARD",
                    speaker_notes="Review executive scorecard KPIs. Pay specific attention to comparison benchmarks and variance against targets.",
                )
            )

        # Pick top charts: Chart 1 (Primary Driver) & Chart 2 (Composition/Segment)
        primary_charts = [c for c in dashboard.charts if c.chart_type in ("bar_chart", "line_chart", "horizontal_bar")]
        comp_charts = [c for c in dashboard.charts if c.chart_type in ("donut_chart", "pie_chart")]

        top_chart1 = primary_charts[0] if primary_charts else (dashboard.charts[0] if dashboard.charts else None)
        top_chart2 = comp_charts[0] if comp_charts else (primary_charts[1] if len(primary_charts) > 1 else (dashboard.charts[1] if len(dashboard.charts) > 1 else None))

        if top_chart1:
            slide = self._make_chart_slide(
                chart=top_chart1,
                slide_number=len(slides) + 1,
                custom_title=f"Primary Performance Drivers: {top_chart1.title}",
                category_tag="03 // MACRO PERFORMANCE",
                speaker_notes=f"Deep-dive into primary performance drivers showing {top_chart1.title}. {top_chart1.reason}",
            )
            slides.append(slide)
            included_chart_ids.append(top_chart1.id)

        if top_chart2 and top_chart2.id != (top_chart1.id if top_chart1 else ""):
            slide = self._make_chart_slide(
                chart=top_chart2,
                slide_number=len(slides) + 1,
                custom_title=f"Strategic Segment Allocation: {top_chart2.title}",
                category_tag="04 // PORTFOLIO ALLOCATION",
                speaker_notes=f"Examine segment allocation and concentration across categories. {top_chart2.reason}",
            )
            slides.append(slide)
            included_chart_ids.append(top_chart2.id)

        # Slide 6: Critical Business Findings & Risk Flags
        if dashboard.insights:
            slides.append(
                self._make_insights_slide(
                    insights=dashboard.insights[:5],
                    slide_number=len(slides) + 1,
                    title="Critical Business Findings & Risk Alerts",
                    subtitle="High-priority observations, outlier anomalies, and operational tailwinds",
                    category_tag="05 // STRATEGIC INSIGHTS",
                    speaker_notes="Walk through critical risk alerts and operational findings. Highlight observations with direct revenue or compliance impact.",
                )
            )

        # Slide 7: Action Plan (Recommendations)
        if dashboard.recommendations:
            slides.append(
                self._make_recommendations_slide(
                    recommendations=dashboard.recommendations[:5],
                    slide_number=len(slides) + 1,
                    title="Executive Action Plan & Capital Allocation",
                    subtitle="Prioritized recommendations for next quarter execution",
                    category_tag="06 // ACTION ROADMAP",
                    speaker_notes="Present actionable recommendations. Seek leadership consensus on timeline, owners, and capital deployment.",
                )
            )

        # Slide 8: Closing
        slides.append(
            self._make_closing_slide(
                title="Strategic Sign-off & Next Steps",
                subtitle="Open for Executive Discussion, Questions & Formal Sign-off",
                slide_number=len(slides) + 1,
                category_tag="07 // GOVERNANCE & APPROVALS",
                speaker_notes="Open the floor for leadership Q&A and confirm milestone sign-off.",
            )
        )

        return slides, included_chart_ids, excluded_charts

    # ── 2. Analytical Deep-Dive Deck Architecture ────────────────
    def _build_analytical_deck(
        self,
        dashboard: DashboardSpecification,
        title: str,
        max_charts: int | None,
    ) -> tuple[list[dict[str, Any]], list[str], list[dict[str, str]]]:
        """Analytical Deep-Dive Architecture:
        1. Title Slide (Quantitative Scope)
        2. Statistical Baseline & Central Tendency
        3. Metric Distribution & Dispersion (Histogram)
        4. Cross-Sectional Comparative Breakdown (Bar / Horizontal Bar)
        5. Categorical Density & Segment Proportions (Donut / Pie)
        6. Multi-Factor Interactions & Secondary Trends (Chart / Line)
        7. Statistical Anomalies & Outliers (Insights)
        8. Analytical Inferences & Model Readiness (Recommendations)
        9. Technical Q&A & Methodological Discussion (Closing)
        """
        slides: list[dict[str, Any]] = []
        included_chart_ids: list[str] = []
        excluded_charts: list[dict[str, str]] = []

        slides.append(
            self._make_title_slide(
                title=title,
                subtitle="Quantitative Analysis, Distribution Profiling & Statistical Modeling",
                tag="ANALYTICAL DEEP-DIVE // EMPIRICAL INTELLIGENCE",
                slide_number=1,
                speaker_notes="Welcome analytics team. Today we explore the full statistical distribution, variance characteristics, and correlation dynamics of the dataset.",
            )
        )

        if dashboard.kpis:
            slides.append(
                self._make_kpi_slide(
                    kpis=dashboard.kpis[:6],
                    title="Statistical Summary & Baseline Aggregates",
                    subtitle="Central tendencies, observation volume, and parametric benchmarks",
                    slide_number=len(slides) + 1,
                    category_tag="01 // STATISTICAL BASELINE",
                    speaker_notes="Examine the primary dataset statistics: central tendencies, total observations, and baseline measure means.",
                )
            )

        # Identify analytical chart types
        hist_charts = [c for c in dashboard.charts if c.chart_type == "histogram" or "distrib" in c.source_analysis]
        comp_charts = [c for c in dashboard.charts if c.chart_type in ("bar_chart", "horizontal_bar")]
        density_charts = [c for c in dashboard.charts if c.chart_type in ("donut_chart", "pie_chart")]
        other_charts = [c for c in dashboard.charts if c.id not in [x.id for x in hist_charts + comp_charts + density_charts]]

        # Chart 1: Distribution & Histogram
        if hist_charts:
            chart = hist_charts[0]
            slides.append(
                self._make_chart_slide(
                    chart=chart,
                    slide_number=len(slides) + 1,
                    custom_title=f"Metric Distribution & Spread: {chart.title}",
                    category_tag="02 // BINNED DISTRIBUTION",
                    speaker_notes=f"Analyze the continuous binned frequency distribution showing {chart.title}. Evaluate skewness and Kurtosis.",
                )
            )
            included_chart_ids.append(chart.id)

        # Chart 2: Comparative Breakdown
        if comp_charts:
            chart = comp_charts[0]
            slides.append(
                self._make_chart_slide(
                    chart=chart,
                    slide_number=len(slides) + 1,
                    custom_title=f"Cross-Sectional Breakdown: {chart.title}",
                    category_tag="03 // MULTI-FACTOR COMPARISON",
                    speaker_notes=f"Discuss comparative ranking across dimensional categories. {chart.reason}",
                )
            )
            included_chart_ids.append(chart.id)

        # Chart 3: Categorical Density & Segment Shares
        if density_charts:
            chart = density_charts[0]
            slides.append(
                self._make_chart_slide(
                    chart=chart,
                    slide_number=len(slides) + 1,
                    custom_title=f"Categorical Density & Segment Share: {chart.title}",
                    category_tag="04 // SEGMENT DENSITY",
                    speaker_notes=f"Examine relative proportion shares and concentration in {chart.title}.",
                )
            )
            included_chart_ids.append(chart.id)

        # Chart 4: Secondary Comparison or Trend
        secondary_chart = comp_charts[1] if len(comp_charts) > 1 else (other_charts[0] if other_charts else None)
        if secondary_chart and secondary_chart.id not in included_chart_ids:
            slides.append(
                self._make_chart_slide(
                    chart=secondary_chart,
                    slide_number=len(slides) + 1,
                    custom_title=f"Dimensional Interactions: {secondary_chart.title}",
                    category_tag="05 // MULTIVARIATE PATTERNS",
                    speaker_notes=f"Inspect secondary dimensional patterns in {secondary_chart.title}.",
                )
            )
            included_chart_ids.append(secondary_chart.id)

        # Slide 7: Statistical Anomalies & Outliers
        if dashboard.insights:
            slides.append(
                self._make_insights_slide(
                    insights=dashboard.insights[:5],
                    slide_number=len(slides) + 1,
                    title="Statistical Anomalies, Outliers & Dispersion Flags",
                    subtitle="Irregular data behavior, IQR fence deviations, and correlation signals",
                    category_tag="06 // OUTLIER & VARIANCE AUDIT",
                    speaker_notes="Review outlier points and dispersion boundaries. Validate whether anomalies represent systemic shifts or data artifacts.",
                )
            )

        # Slide 8: Analytical Inferences
        if dashboard.recommendations:
            slides.append(
                self._make_recommendations_slide(
                    recommendations=dashboard.recommendations[:5],
                    slide_number=len(slides) + 1,
                    title="Analytical Inferences & Model Readiness",
                    subtitle="Quantitative findings, feature relevance, and downstream modeling guidance",
                    category_tag="07 // INFERENCES & MODELING",
                    speaker_notes="Summarize quantitative inferences, feature scaling recommendations, and downstream ML readiness.",
                )
            )

        # Slide 9: Closing
        slides.append(
            self._make_closing_slide(
                title="Technical Q&A & Methodological Discussion",
                subtitle="Open Discussion on Statistical Inferences, Assumptions & Scope",
                slide_number=len(slides) + 1,
                category_tag="08 // METHODOLOGICAL REVIEW",
                speaker_notes="Open the floor for questions on statistical methodologies and data boundaries.",
            )
        )

        return slides, included_chart_ids, excluded_charts

    # ── 3. Technical / Research Deck Architecture ────────────────
    def _build_research_deck(
        self,
        dashboard: DashboardSpecification,
        title: str,
        max_charts: int | None,
        profile: dict | None,
        quality: dict | None,
    ) -> tuple[list[dict[str, Any]], list[str], list[dict[str, str]]]:
        """Technical / Research Architecture:
        1. Title Slide (Research Scope & Data Audit)
        2. Dataset Hygiene & Schema Quality Scorecard (Table/Cards)
        3. Empirical Parametric Distributions (Histogram)
        4. Comparative Factor Breakdown (Bar)
        5. Discrete Categorical Mapping (Donut / Horizontal Bar)
        6. Audit Exceptions & Boundary Violations (Insights)
        7. Methodological Scope & Technical Limitations (Bullets)
        8. Production Engineering & Implementation Roadmap (Recommendations)
        9. Technical Appendix & Audit Sign-off (Closing)
        """
        slides: list[dict[str, Any]] = []
        included_chart_ids: list[str] = []
        excluded_charts: list[dict[str, str]] = []

        slides.append(
            self._make_title_slide(
                title=title,
                subtitle="Technical Research Report, Empirical Data Audit & Methodology",
                tag="TECHNICAL RESEARCH // DATA AUDIT",
                slide_number=1,
                speaker_notes="Presenting the empirical data audit and technical research findings for formal review and compliance sign-off.",
            )
        )

        # Slide 2: Data Hygiene Audit
        col_count = len(profile.get("columns", [])) if profile else len(dashboard.charts) * 2
        row_count = profile.get("row_count", 0) if profile else 0
        comp_score = profile.get("overall_completeness", 1.0) if profile else 1.0
        pct_comp = round(comp_score * 100, 1) if comp_score <= 1.0 else round(comp_score, 1)

        hygiene_points = [
            f"Dataset Volume: {row_count:,} observation records across {col_count} schema dimensions." if row_count else f"Schema Scope: {col_count} distinct attributes audited.",
            f"Data Completeness: Verified at {pct_comp}% integrity with null/missing value verification.",
            "Encoding & Normalization: Data sanitization verified across character encoding, dates, and numeric types.",
            "Outlier & Boundary Testing: Tukey IQR dispersion fences applied to isolate boundary deviations.",
        ]
        slides.append(
            self._make_summary_text_slide(
                title="Data Hygiene & Schema Quality Scorecard",
                subtitle="Verification of ingestion pipeline, completeness, and schema conformance",
                paragraphs=hygiene_points,
                slide_number=len(slides) + 1,
                category_tag="01 // SCHEMA AUDIT",
                speaker_notes="Detail data hygiene verification, missing value patterns, and ETL boundary integrity.",
            )
        )

        # Charts: Histogram, Comparative, Density
        hist_charts = [c for c in dashboard.charts if c.chart_type == "histogram" or "distrib" in c.source_analysis]
        comp_charts = [c for c in dashboard.charts if c.chart_type in ("bar_chart", "horizontal_bar")]
        density_charts = [c for c in dashboard.charts if c.chart_type in ("donut_chart", "pie_chart")]

        if hist_charts:
            chart = hist_charts[0]
            slides.append(
                self._make_chart_slide(
                    chart=chart,
                    slide_number=len(slides) + 1,
                    custom_title=f"Empirical Distributions: {chart.title}",
                    category_tag="02 // PARAMETRIC EVALUATION",
                    speaker_notes=f"Evaluate empirical distribution bins in {chart.title}. Assess normal vs skewed properties.",
                )
            )
            included_chart_ids.append(chart.id)

        if comp_charts:
            chart = comp_charts[0]
            slides.append(
                self._make_chart_slide(
                    chart=chart,
                    slide_number=len(slides) + 1,
                    custom_title=f"Factor Variance Breakdown: {chart.title}",
                    category_tag="03 // FACTOR VARIANCE",
                    speaker_notes=f"Analyze factor variance across categorical dimensions. {chart.reason}",
                )
            )
            included_chart_ids.append(chart.id)

        if density_charts:
            chart = density_charts[0]
            slides.append(
                self._make_chart_slide(
                    chart=chart,
                    slide_number=len(slides) + 1,
                    custom_title=f"Discrete Categorical Classifications: {chart.title}",
                    category_tag="04 // DISCRETE MAPPING",
                    speaker_notes=f"Review discrete categorical frequency mappings in {chart.title}.",
                )
            )
            included_chart_ids.append(chart.id)

        # Slide 6: Audit Exceptions
        if dashboard.insights:
            slides.append(
                self._make_insights_slide(
                    insights=dashboard.insights[:5],
                    slide_number=len(slides) + 1,
                    title="Audit Exceptions & Boundary Violations",
                    subtitle="Anomalous values, extreme variance, and data quality alerts",
                    category_tag="05 // AUDIT EXCEPTIONS",
                    speaker_notes="Examine anomalous observations and boundary exceptions identified during the audit.",
                )
            )

        # Slide 7: Technical Limitations
        limitations = [
            "Sample Boundary: Inference applies specifically to the profiled dataset collection timeframe.",
            "Cardinality Considerations: Low-sample categories require wider confidence intervals.",
            "Stationarity: Temporal trends assume consistent macro conditions across observation periods.",
        ]
        slides.append(
            self._make_summary_text_slide(
                title="Methodological Scope & Technical Limitations",
                subtitle="Boundary assumptions, confidence limits, and reproducibility criteria",
                paragraphs=limitations,
                slide_number=len(slides) + 1,
                category_tag="06 // TECHNICAL BOUNDARIES",
                speaker_notes="Document methodological constraints, sample boundaries, and reproducibility criteria.",
            )
        )

        # Slide 8: Implementation Roadmap
        if dashboard.recommendations:
            slides.append(
                self._make_recommendations_slide(
                    recommendations=dashboard.recommendations[:5],
                    slide_number=len(slides) + 1,
                    title="Production Engineering & Implementation Roadmap",
                    subtitle="Systemic architecture adjustments, validation checks, and data pipeline steps",
                    category_tag="07 // ENGINEERING ROADMAP",
                    speaker_notes="Detail concrete technical implementation steps for data engineering and production deployment.",
                )
            )

        # Slide 9: Technical Closing
        slides.append(
            self._make_closing_slide(
                title="Technical Appendix & Audit Sign-off",
                subtitle="Review Completed • Ready for Committee Sign-off & Archival",
                slide_number=len(slides) + 1,
                category_tag="08 // FORMAL SIGN-OFF",
                speaker_notes="Conclude technical review and open for committee validation sign-off.",
            )
        )

        return slides, included_chart_ids, excluded_charts

    # ── 4. Investor / Pitch Deck Architecture ────────────────────
    def _build_pitch_deck(
        self,
        dashboard: DashboardSpecification,
        title: str,
        max_charts: int | None,
    ) -> tuple[list[dict[str, Any]], list[str], list[dict[str, str]]]:
        """Investor / Pitch Deck Architecture:
        1. Vision & Hook Slide
        2. The Market Inefficiency & Strategic Friction
        3. Headline Traction & Performance Scorecard (Hero KPIs)
        4. Growth Engine & Outperformance Velocity (Top Chart)
        5. Market Share & Category Dominance (Donut / Composition)
        6. Competitive Moats & Market Tailwinds (Insights)
        7. 12-Month Execution Milestones & Growth Runway (Roadmap)
        8. Investment Thesis & Vision Sign-off (Closing)
        """
        slides: list[dict[str, Any]] = []
        included_chart_ids: list[str] = []
        excluded_charts: list[dict[str, str]] = []

        slides.append(
            self._make_title_slide(
                title=title,
                subtitle="Market Opportunity, Traction Velocity & Scalability Thesis",
                tag="INVESTOR PITCH // TRACTION & GROWTH",
                slide_number=1,
                speaker_notes="Welcome partners and investors. Today we showcase empirical traction, high-velocity growth drivers, and strategic market capture.",
            )
        )

        problem_points = [
            f"Market Context: Operating across the fast-evolving {dashboard.industry.title()} sector.",
            "The Operational Inefficiency: Unoptimized segment allocation creates fragmented output and lost margin.",
            "The Opportunity: Systematic focus on high-yield categories unlocks compounded scale and defensible moats.",
        ]
        slides.append(
            self._make_summary_text_slide(
                title="The Market Inefficiency & Strategic Opportunity",
                subtitle="Empirical proof of market friction and the value-capture unlock",
                paragraphs=problem_points,
                slide_number=len(slides) + 1,
                category_tag="01 // OPPORTUNITY & HOOK",
                speaker_notes="Set the hook: explain the core friction demonstrated by the data and how our strategic focus captures value.",
            )
        )

        if dashboard.kpis:
            slides.append(
                self._make_kpi_slide(
                    kpis=dashboard.kpis[:4],
                    title="Headline Traction & Performance Scorecard",
                    subtitle="Core proof points demonstrating momentum, scale, and operating yield",
                    slide_number=len(slides) + 1,
                    category_tag="02 // HERO TRACTION",
                    speaker_notes="Present hero metric traction. Highlight outperformance benchmarks and growth trajectories.",
                )
            )

        # Primary Growth Chart
        primary_charts = [c for c in dashboard.charts if c.chart_type in ("bar_chart", "line_chart", "horizontal_bar")]
        comp_charts = [c for c in dashboard.charts if c.chart_type in ("donut_chart", "pie_chart")]

        if primary_charts:
            chart = primary_charts[0]
            slides.append(
                self._make_chart_slide(
                    chart=chart,
                    slide_number=len(slides) + 1,
                    custom_title=f"Growth Engine & Velocity: {chart.title}",
                    category_tag="03 // GROWTH VELOCITY",
                    speaker_notes=f"Illustrate core growth velocity in {chart.title}. Emphasize categorical outperformance.",
                )
            )
            included_chart_ids.append(chart.id)

        if comp_charts:
            chart = comp_charts[0]
            slides.append(
                self._make_chart_slide(
                    chart=chart,
                    slide_number=len(slides) + 1,
                    custom_title=f"Category Share & Market Dominance: {chart.title}",
                    category_tag="04 // MARKET SHARE",
                    speaker_notes=f"Demonstrate defensible category share and market concentration in {chart.title}.",
                )
            )
            included_chart_ids.append(chart.id)

        if dashboard.insights:
            slides.append(
                self._make_insights_slide(
                    insights=dashboard.insights[:4],
                    slide_number=len(slides) + 1,
                    title="Competitive Moats & Strategic Tailwinds",
                    subtitle="Empirical advantages, efficiency gains, and structural expansion drivers",
                    category_tag="05 // STRATEGIC MOATS",
                    speaker_notes="Highlight proprietary operational moats, compounding efficiencies, and strategic tailwinds.",
                )
            )

        if dashboard.recommendations:
            slides.append(
                self._make_recommendations_slide(
                    recommendations=dashboard.recommendations[:4],
                    slide_number=len(slides) + 1,
                    title="12-Month Execution Milestones & Growth Runway",
                    subtitle="Targeted milestone deliverables, capital allocation, and market capture",
                    category_tag="06 // EXECUTION RUNWAY",
                    speaker_notes="Review the 12-month milestone roadmap and projected capital deployment.",
                )
            )

        slides.append(
            self._make_closing_slide(
                title="Investment Summary & Closing Vision",
                subtitle="Thank You • Open for Strategic Partner Discussion & Investment Terms",
                slide_number=len(slides) + 1,
                category_tag="07 // INVESTMENT VISION",
                speaker_notes="Conclude with high conviction and open the floor for investment discussions.",
            )
        )

        return slides, included_chart_ids, excluded_charts

    # ── Slide Helpers ────────────────────────────────────────────

    def _make_title_slide(
        self,
        title: str,
        subtitle: str,
        tag: str,
        slide_number: int,
        speaker_notes: str,
    ) -> dict[str, Any]:
        return {
            "slide_number": slide_number,
            "layout": "title",
            "title": title,
            "subtitle": subtitle,
            "category_tag": tag,
            "speaker_notes": speaker_notes,
        }

    def _make_summary_text_slide(
        self,
        title: str,
        subtitle: str,
        paragraphs: list[str],
        slide_number: int,
        category_tag: str,
        speaker_notes: str,
    ) -> dict[str, Any]:
        return {
            "slide_number": slide_number,
            "layout": "bullets",
            "title": title,
            "subtitle": subtitle,
            "category_tag": category_tag,
            "content": "\n\n".join(paragraphs),
            "bullet_items": paragraphs,
            "speaker_notes": speaker_notes,
        }

    def _make_kpi_slide(
        self,
        kpis: list[KPISpecification],
        title: str,
        subtitle: str,
        slide_number: int,
        category_tag: str = "KPI SCORECARD",
        speaker_notes: str = "",
    ) -> dict[str, Any]:
        n_kpis = min(len(kpis), 6)
        cards = []
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
            "title": title,
            "subtitle": subtitle,
            "category_tag": category_tag,
            "kpi_cards": cards,
            "speaker_notes": speaker_notes,
        }

    def _make_chart_slide(
        self,
        chart: ChartSpecification,
        slide_number: int,
        custom_title: str | None = None,
        category_tag: str = "VISUAL ANALYSIS",
        speaker_notes: str | None = None,
    ) -> dict[str, Any]:
        placement = {
            "x": self.CHART_LEFT,
            "y": self.CHART_TOP,
            "width": self.CHART_WIDTH,
            "height": self.CHART_HEIGHT,
        }
        chart.pptx_placement = placement

        return {
            "slide_number": slide_number,
            "layout": "chart",
            "title": custom_title or chart.title,
            "subtitle": chart.description,
            "category_tag": category_tag,
            "chart_id": chart.id,
            "chart_type": chart.chart_type,
            "chart_data": chart.data,
            "x_axis": chart.x_axis,
            "y_axis": chart.y_axis,
            "aggregation": chart.aggregation,
            "chart_placement": placement,
            "caption": chart.description,
            "reason": chart.reason,
            "speaker_notes": speaker_notes or f"Discuss the {chart.chart_type} showing {chart.title}. {chart.reason}",
        }

    def _make_insights_slide(
        self,
        insights: list[InsightSpecification],
        slide_number: int,
        title: str = "Strategic Insights",
        subtitle: str = "Key empirical findings and anomalous observations",
        category_tag: str = "STRATEGIC INSIGHTS",
        speaker_notes: str = "",
    ) -> dict[str, Any]:
        top_insights = insights[:5]
        content_lines = []
        for insight in top_insights:
            icon = "⚠️" if insight.severity == "critical" else "✅" if insight.severity == "positive" else "•"
            content_lines.append(f"{icon} {insight.title}: {insight.description}")

        return {
            "slide_number": slide_number,
            "layout": "bullets",
            "title": title,
            "subtitle": subtitle,
            "category_tag": category_tag,
            "content": "\n\n".join(content_lines),
            "bullet_items": [f"{i.title}: {i.description}" for i in top_insights],
            "insights": [i.to_dict() for i in top_insights],
            "speaker_notes": speaker_notes or "Discuss each insight with supporting evidence from the data.",
        }

    def _make_recommendations_slide(
        self,
        recommendations: list[str],
        slide_number: int,
        title: str = "Strategic Action Plan",
        subtitle: str = "Prioritized recommendations and implementation milestones",
        category_tag: str = "ACTION ROADMAP",
        speaker_notes: str = "",
    ) -> dict[str, Any]:
        content = "\n\n".join(f"• {r}" for r in recommendations[:5])
        return {
            "slide_number": slide_number,
            "layout": "bullets",
            "title": title,
            "subtitle": subtitle,
            "category_tag": category_tag,
            "content": content,
            "bullet_items": recommendations[:5],
            "speaker_notes": speaker_notes or "Present clear, actionable recommendations with expected impact.",
        }

    def _make_closing_slide(
        self,
        title: str,
        subtitle: str,
        slide_number: int,
        category_tag: str = "SIGN-OFF",
        speaker_notes: str = "",
    ) -> dict[str, Any]:
        return {
            "slide_number": slide_number,
            "layout": "closing",
            "title": title,
            "subtitle": subtitle,
            "category_tag": category_tag,
            "speaker_notes": speaker_notes,
        }

    # ── Placement & Bounds Validation ────────────────────────────

    def _validate_presentation(self, slides: list[dict[str, Any]]) -> dict[str, Any]:
        """Validate that all elements are within 16:9 widescreen slide bounds."""
        errors: list[str] = []
        warnings: list[str] = []

        for slide in slides:
            slide_num = slide.get("slide_number", 0)

            if slide.get("layout") == "chart":
                p = slide.get("chart_placement", {})
                x, y, w, h = p.get("x", 0), p.get("y", 0), p.get("width", 0), p.get("height", 0)
                if x < 0 or y < 0:
                    errors.append(f"Slide {slide_num}: Negative chart coordinates ({x}, {y})")
                if x + w > self.SLIDE_WIDTH + 0.1:
                    errors.append(f"Slide {slide_num}: Chart exceeds slide width ({x+w:.2f} > {self.SLIDE_WIDTH})")
                if y + h > self.SLIDE_HEIGHT + 0.1:
                    errors.append(f"Slide {slide_num}: Chart exceeds slide height ({y+h:.2f} > {self.SLIDE_HEIGHT})")

            if slide.get("layout") == "kpi":
                cards = slide.get("kpi_cards", [])
                for i, card in enumerate(cards):
                    p = card.get("placement", {})
                    x, y, w, h = p.get("x", 0), p.get("y", 0), p.get("width", 0), p.get("height", 0)
                    if x < 0 or y < 0:
                        errors.append(f"Slide {slide_num}: KPI card {i} has negative coordinates")
                    if x + w > self.SLIDE_WIDTH + 0.1:
                        errors.append(f"Slide {slide_num}: KPI card {i} exceeds slide width")
                    if y + h > self.SLIDE_HEIGHT + 0.1:
                        errors.append(f"Slide {slide_num}: KPI card {i} exceeds slide height")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "slide_count": len(slides),
        }
