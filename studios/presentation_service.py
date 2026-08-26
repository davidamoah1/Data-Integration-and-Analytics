"""Presentation Studio â€” AI-generated presentations from analysis results."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from studios.models import Presentation


class PresentationStudioService:
    """Service for generating presentations from analyses, research, and dashboards."""

    def __init__(self, db: DbSession):
        self.db = db

    def create_presentation(
        self,
        org_id: int,
        user_id: int,
        title: str,
        source_type: str,
        source_id: int | None = None,
        template: str = "executive",
    ) -> Presentation:
        pres = Presentation(
            organization_id=org_id,
            title=title,
            source_type=source_type,
            source_id=source_id,
            template=template,
            created_by=user_id,
        )
        self.db.add(pres)
        self.db.commit()
        return pres

    def list_presentations(self, org_id: int) -> list[Presentation]:
        return (
            self.db.execute(
                select(Presentation)
                .where(Presentation.organization_id == org_id)
                .order_by(Presentation.created_at.desc())
            )
            .scalars()
            .all()
        )

    def get_presentation(self, pres_id: int, org_id: int) -> Presentation | None:
        return self.db.execute(
            select(Presentation).where(
                Presentation.id == pres_id,
                Presentation.organization_id == org_id,
            )
        ).scalar_one_or_none()

    @staticmethod
    def generate_slides(
        source_type: str,
        source_data: dict,
        template: str = "executive",
    ) -> list[dict]:
        """Generate presentation slides from source data.

        Templates:
          - executive: High-level summary for C-suite
          - analytical: Detailed findings for analysts
          - research: Academic-style with methodology
          - pitch: Persuasive format for stakeholders
        """
        slides = []

        if template == "executive":
            slides = [
                {
                    "slide_number": 1,
                    "layout": "title",
                    "title": source_data.get("title", "Analysis Report"),
                    "content": source_data.get("subtitle", ""),
                    "speaker_notes": "Welcome the audience and set the context for this presentation.",
                },
                {
                    "slide_number": 2,
                    "layout": "bullets",
                    "title": "Executive Summary",
                    "content": source_data.get("summary", "Key findings will be presented here."),
                    "speaker_notes": "Provide a high-level overview of the main findings and recommendations.",
                },
                {
                    "slide_number": 3,
                    "layout": "chart",
                    "title": "Key Metrics",
                    "content": "Overview of primary performance indicators.",
                    "chart_config": source_data.get("chart_config"),
                    "speaker_notes": "Walk through the most important metrics and their trends.",
                },
                {
                    "slide_number": 4,
                    "layout": "bullets",
                    "title": "Findings",
                    "content": source_data.get("findings", "Detailed findings from the analysis."),
                    "speaker_notes": "Discuss each finding with supporting evidence.",
                },
                {
                    "slide_number": 5,
                    "layout": "bullets",
                    "title": "Recommendations",
                    "content": source_data.get(
                        "recommendations", "Actionable recommendations based on findings."
                    ),
                    "speaker_notes": "Present clear, actionable recommendations with expected impact.",
                },
                {
                    "slide_number": 6,
                    "layout": "bullets",
                    "title": "Next Steps",
                    "content": source_data.get("next_steps", "Proposed next steps and timeline."),
                    "speaker_notes": "Outline the path forward and invite questions.",
                },
            ]

        elif template == "analytical":
            slides = [
                {
                    "slide_number": 1,
                    "layout": "title",
                    "title": source_data.get("title", "Analytical Report"),
                    "content": "Detailed Analysis and Findings",
                },
                {
                    "slide_number": 2,
                    "layout": "bullets",
                    "title": "Data Overview",
                    "content": source_data.get(
                        "data_overview", "Dataset description and methodology."
                    ),
                },
                {
                    "slide_number": 3,
                    "layout": "chart",
                    "title": "Descriptive Statistics",
                    "content": "Summary of key statistical measures.",
                    "chart_config": source_data.get("stats_chart"),
                },
                {
                    "slide_number": 4,
                    "layout": "chart",
                    "title": "Trend Analysis",
                    "content": "Time series and trend analysis results.",
                    "chart_config": source_data.get("trend_chart"),
                },
                {
                    "slide_number": 5,
                    "layout": "bullets",
                    "title": "Statistical Tests",
                    "content": source_data.get(
                        "test_results", "Results of statistical tests performed."
                    ),
                },
                {
                    "slide_number": 6,
                    "layout": "bullets",
                    "title": "Detailed Findings",
                    "content": source_data.get("findings", "Comprehensive analysis findings."),
                },
                {
                    "slide_number": 7,
                    "layout": "bullets",
                    "title": "Limitations & Assumptions",
                    "content": source_data.get("limitations", "Known limitations and assumptions."),
                },
                {
                    "slide_number": 8,
                    "layout": "bullets",
                    "title": "Conclusions",
                    "content": source_data.get("conclusions", "Analytical conclusions."),
                },
            ]

        elif template == "research":
            slides = [
                {
                    "slide_number": 1,
                    "layout": "title",
                    "title": source_data.get("title", "Research Report"),
                    "content": source_data.get("subtitle", "Research Findings Presentation"),
                },
                {
                    "slide_number": 2,
                    "layout": "bullets",
                    "title": "Research Question",
                    "content": source_data.get(
                        "research_question", "The research question being investigated."
                    ),
                },
                {
                    "slide_number": 3,
                    "layout": "bullets",
                    "title": "Methodology",
                    "content": source_data.get("methodology", "Research design and methodology."),
                },
                {
                    "slide_number": 4,
                    "layout": "bullets",
                    "title": "Hypotheses",
                    "content": source_data.get("hypotheses", "Research hypotheses tested."),
                },
                {
                    "slide_number": 5,
                    "layout": "chart",
                    "title": "Results",
                    "content": "Statistical results and findings.",
                    "chart_config": source_data.get("results_chart"),
                },
                {
                    "slide_number": 6,
                    "layout": "table",
                    "title": "Statistical Summary",
                    "content": source_data.get(
                        "statistical_summary", "Summary table of test results."
                    ),
                },
                {
                    "slide_number": 7,
                    "layout": "bullets",
                    "title": "Discussion",
                    "content": source_data.get("discussion", "Interpretation of findings."),
                },
                {
                    "slide_number": 8,
                    "layout": "bullets",
                    "title": "Conclusions & Future Work",
                    "content": source_data.get(
                        "conclusions", "Conclusions and directions for future research."
                    ),
                },
            ]

        elif template == "pitch":
            slides = [
                {
                    "slide_number": 1,
                    "layout": "title",
                    "title": source_data.get("title", "Opportunity Analysis"),
                    "content": "Data-Driven Decision Support",
                },
                {
                    "slide_number": 2,
                    "layout": "bullets",
                    "title": "The Opportunity",
                    "content": source_data.get(
                        "opportunity", "What the data reveals about the opportunity."
                    ),
                },
                {
                    "slide_number": 3,
                    "layout": "chart",
                    "title": "Market Evidence",
                    "content": "Data supporting the opportunity.",
                    "chart_config": source_data.get("market_chart"),
                },
                {
                    "slide_number": 4,
                    "layout": "bullets",
                    "title": "Key Insights",
                    "content": source_data.get("insights", "Top insights from the data."),
                },
                {
                    "slide_number": 5,
                    "layout": "bullets",
                    "title": "Expected Impact",
                    "content": source_data.get(
                        "impact", "Projected impact of acting on these insights."
                    ),
                },
                {
                    "slide_number": 6,
                    "layout": "bullets",
                    "title": "Call to Action",
                    "content": source_data.get("call_to_action", "Recommended next steps."),
                },
            ]

        return slides

    def generate_and_save(
        self,
        org_id: int,
        user_id: int,
        title: str,
        source_type: str,
        source_data: dict,
        template: str = "executive",
    ) -> Presentation:
        """Generate slides and save the presentation."""
        slides = self.generate_slides(source_type, source_data, template)
        pres = self.create_presentation(
            org_id=org_id,
            user_id=user_id,
            title=title,
            source_type=source_type,
            template=template,
        )
        pres.slides = slides
        pres.is_generated = True
        self.db.commit()
        return pres
