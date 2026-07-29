"""Research Studio service — research projects, hypotheses, and publication-ready reports."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from studios.models import ResearchHypothesis, ResearchProject, ResearchReport


class ResearchStudioService:
    """Service for the Research Studio."""

    def __init__(self, db: DbSession):
        self.db = db

    # ─── Projects ────────────────────────────────────────────

    def create_project(
        self,
        org_id: int,
        user_id: int,
        title: str,
        research_question: str | None = None,
        methodology: str | None = None,
        industry: str | None = None,
    ) -> ResearchProject:
        project = ResearchProject(
            organization_id=org_id,
            title=title,
            research_question=research_question,
            methodology=methodology,
            industry=industry,
            created_by=user_id,
        )
        self.db.add(project)
        self.db.commit()
        return project

    def list_projects(self, org_id: int) -> list[ResearchProject]:
        return self.db.execute(
            select(ResearchProject)
            .where(ResearchProject.organization_id == org_id)
            .order_by(ResearchProject.updated_at.desc())
        ).scalars().all()

    def get_project(self, project_id: int, org_id: int) -> ResearchProject | None:
        return self.db.execute(
            select(ResearchProject).where(
                ResearchProject.id == project_id,
                ResearchProject.organization_id == org_id,
            )
        ).scalar_one_or_none()

    def update_project(self, project_id: int, org_id: int, **kwargs) -> ResearchProject:
        project = self.get_project(project_id, org_id)
        if not project:
            raise ValueError("Project not found")
        for k, v in kwargs.items():
            if hasattr(project, k):
                setattr(project, k, v)
        self.db.commit()
        return project

    # ─── Hypotheses ──────────────────────────────────────────

    def create_hypothesis(
        self,
        project_id: int,
        hypothesis: str,
        null_hypothesis: str | None = None,
        alternative_hypothesis: str | None = None,
        test_type: str | None = None,
        significance_level: float = 0.05,
    ) -> ResearchHypothesis:
        hyp = ResearchHypothesis(
            project_id=project_id,
            hypothesis=hypothesis,
            null_hypothesis=null_hypothesis,
            alternative_hypothesis=alternative_hypothesis,
            test_type=test_type,
            significance_level=significance_level,
        )
        self.db.add(hyp)
        self.db.commit()
        return hyp

    def list_hypotheses(self, project_id: int) -> list[ResearchHypothesis]:
        return self.db.execute(
            select(ResearchHypothesis)
            .where(ResearchHypothesis.project_id == project_id)
            .order_by(ResearchHypothesis.created_at.desc())
        ).scalars().all()

    def update_hypothesis_status(
        self,
        hypothesis_id: int,
        status: str,
        result_summary: str | None = None,
        analysis_id: int | None = None,
    ) -> ResearchHypothesis:
        hyp = self.db.execute(
            select(ResearchHypothesis).where(ResearchHypothesis.id == hypothesis_id)
        ).scalar_one_or_none()
        if not hyp:
            raise ValueError("Hypothesis not found")
        hyp.status = status
        if result_summary:
            hyp.result_summary = result_summary
        if analysis_id:
            hyp.analysis_id = analysis_id
        self.db.commit()
        return hyp

    # ─── AI Research Assistant ───────────────────────────────

    @staticmethod
    def suggest_research_design(research_question: str, industry: str | None = None) -> dict:
        """AI-suggested research design based on the research question."""
        question = research_question.lower()

        design = {
            "research_question": research_question,
            "suggested_design": "observational",
            "suggested_methodology": "",
            "suggested_tests": [],
            "sample_size_consideration": "",
            "ethical_considerations": [],
        }

        # Detect comparison questions
        if any(w in question for w in ["compare", "difference", "versus", "vs", "effect of"]):
            design["suggested_design"] = "comparative"
            design["suggested_methodology"] = "Compare groups using appropriate statistical tests"
            design["suggested_tests"] = ["t-test (2 groups)", "ANOVA (3+ groups)", "Mann-Whitney U (non-parametric)"]
            design["sample_size_consideration"] = "Ensure adequate power (typically n≥30 per group)"

        # Detect relationship questions
        elif any(w in question for w in ["relationship", "correlation", "associate", "predict"]):
            design["suggested_design"] = "correlational"
            design["suggested_methodology"] = "Examine relationships between variables"
            design["suggested_tests"] = ["Pearson/Spearman correlation", "Linear/Multiple regression", "Chi-square (categorical)"]
            design["sample_size_consideration"] = "At least 10 observations per predictor variable"

        # Detect causal questions
        elif any(w in question for w in ["cause", "impact", "influence", "affect"]):
            design["suggested_design"] = "experimental"
            design["suggested_methodology"] = "Randomized controlled trial or quasi-experiment"
            design["suggested_tests"] = ["ANOVA", "Regression with controls", "Difference-in-differences"]
            design["sample_size_consideration"] = "Power analysis recommended before data collection"

        # Detect descriptive questions
        elif any(w in question for w in ["what", "how many", "describe", "characterize"]):
            design["suggested_design"] = "descriptive"
            design["suggested_methodology"] = "Describe characteristics of the population"
            design["suggested_tests"] = ["Descriptive statistics", "Frequency analysis", "Cross-tabulation"]
            design["sample_size_consideration"] = "Representative sample of the population"

        # Industry-specific additions
        if industry:
            industry_kpis = {
                "healthcare": ["patient outcomes", "treatment efficacy", "readmission rates"],
                "education": ["student performance", "teaching effectiveness", "graduation rates"],
                "banking": ["credit risk", "loan default", "customer profitability"],
                "agriculture": ["crop yield", "soil health", "weather impact"],
            }
            if industry in industry_kpis:
                design["industry_relevant_metrics"] = industry_kpis[industry]

        design["ethical_considerations"] = [
            "Informed consent from participants",
            "Data privacy and anonymization",
            "Conflicts of interest disclosure",
        ]

        return design

    @staticmethod
    def generate_hypothesis(research_question: str, variables: list[str]) -> list[dict]:
        """AI-generated hypotheses based on research question and available variables."""
        hypotheses = []

        # Pairwise hypotheses
        if len(variables) >= 2:
            for i in range(min(len(variables), 3)):
                for j in range(i + 1, min(len(variables), 4)):
                    v1, v2 = variables[i], variables[j]
                    hypotheses.append({
                        "hypothesis": f"There is a significant relationship between {v1} and {v2}",
                        "null_hypothesis": f"There is no significant relationship between {v1} and {v2}",
                        "alternative_hypothesis": f"There is a significant relationship between {v1} and {v2}",
                        "suggested_test": "Correlation analysis" if i != j else "Descriptive",
                    })

        # Group comparison
        if len(variables) >= 2:
            hypotheses.append({
                "hypothesis": f"There is a significant difference in {variables[0]} across groups of {variables[1]}",
                "null_hypothesis": f"There is no significant difference in {variables[0]} across groups of {variables[1]}",
                "alternative_hypothesis": f"There is a significant difference in {variables[0]} across groups of {variables[1]}",
                "suggested_test": "ANOVA or t-test",
            })

        return hypotheses[:5]  # Limit to top 5

    # ─── Reports ─────────────────────────────────────────────

    def create_report(
        self,
        project_id: int,
        title: str,
        sections: list[dict] | None = None,
        methodology_text: str | None = None,
        is_publication_ready: bool = False,
    ) -> ResearchReport:
        report = ResearchReport(
            project_id=project_id,
            title=title,
            sections=sections or [],
            methodology_text=methodology_text,
            is_publication_ready=is_publication_ready,
        )
        self.db.add(report)
        self.db.commit()
        return report

    def list_reports(self, project_id: int) -> list[ResearchReport]:
        return self.db.execute(
            select(ResearchReport)
            .where(ResearchReport.project_id == project_id)
            .order_by(ResearchReport.created_at.desc())
        ).scalars().all()

    @staticmethod
    def generate_report_sections(
        project: ResearchProject,
        hypotheses: list[ResearchHypothesis],
        analyses: list[dict],
    ) -> list[dict]:
        """Generate publication-ready report sections from project data."""
        sections = [
            {
                "title": "Abstract",
                "content": f"This study investigates: {project.research_question or project.title}",
            },
            {
                "title": "Introduction",
                "content": f"Research question: {project.research_question or 'Not specified'}\n\n"
                           f"This research aims to contribute to understanding in the {project.industry or 'relevant'} domain.",
            },
            {
                "title": "Methodology",
                "content": project.methodology or "Methodology to be specified.",
            },
            {
                "title": "Hypotheses",
                "content": "\n".join([
                    f"H{i+1}: {h.hypothesis}\n"
                    f"  Null: {h.null_hypothesis}\n"
                    f"  Test: {h.test_type}\n"
                    f"  Status: {h.status}"
                    for i, h in enumerate(hypotheses)
                ]),
            },
            {
                "title": "Results",
                "content": "\n".join([
                    f"Analysis: {a.get('test_name', 'Unknown')}\n"
                    f"Result: {a.get('interpretation', 'N/A')}\n"
                    for a in analyses
                ]) or "No analyses performed yet.",
            },
            {
                "title": "Discussion",
                "content": "The findings are discussed in the context of the research question and existing literature.",
            },
            {
                "title": "Conclusion",
                "content": "Conclusions are drawn based on the statistical evidence presented.",
            },
            {
                "title": "Limitations",
                "content": "All studies have limitations. These should be acknowledged and addressed in future research.",
            },
        ]
        return sections
