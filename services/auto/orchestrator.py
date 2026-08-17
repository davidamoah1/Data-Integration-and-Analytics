"""Auto Engine Orchestrator.

Ties all automatic engines together into a single pipeline:

  DataFrame + metadata
       │
       ▼
  AutomaticAnalysisEngine  → DatasetUnderstanding
       │
       ▼
  IntelligentChartSelectionEngine → list[ChartSpecification]
       │
       ▼
  AutomaticKPIEngine → list[KPISpecification]
       │
       ▼
  AutomaticInsightEngine → list[InsightSpecification]
       │
       ▼
  AutomaticFilterEngine → list[FilterSpecification]
       │
       ▼
  IntelligentDashboardLayoutEngine → DashboardSpecification
       │
       ▼
  PresentationLayoutEngine → PresentationSpecification

The DashboardSpecification and PresentationSpecification share the
SAME ChartSpecification objects — they are the single source of truth.
"""

from __future__ import annotations

import hashlib
import logging
from typing import Any

import pandas as pd

from services.auto.analysis_engine import AutomaticAnalysisEngine
from services.auto.chart_selection_engine import IntelligentChartSelectionEngine
from services.auto.chart_specification import (
    ChartSpecification,
    DashboardSpecification,
    PresentationSpecification,
)
from services.auto.dashboard_layout_engine import IntelligentDashboardLayoutEngine
from services.auto.filter_engine import AutomaticFilterEngine
from services.auto.insight_engine import AutomaticInsightEngine
from services.auto.kpi_engine import AutomaticKPIEngine
from services.auto.presentation_layout_engine import PresentationLayoutEngine

logger = logging.getLogger(__name__)


class AutoEngineOrchestrator:
    """Orchestrates the full automatic analysis → visualization → layout pipeline."""

    def __init__(self) -> None:
        self.analysis_engine = AutomaticAnalysisEngine()
        self.chart_engine = IntelligentChartSelectionEngine()
        self.kpi_engine = AutomaticKPIEngine()
        self.insight_engine = AutomaticInsightEngine()
        self.filter_engine = AutomaticFilterEngine()
        self.dashboard_layout_engine = IntelligentDashboardLayoutEngine()
        self.presentation_layout_engine = PresentationLayoutEngine()

    def generate(
        self,
        df: pd.DataFrame,
        dataset_name: str = "uploaded_dataset",
        industry: str = "unknown",
        quality_score: float = 0.0,
        max_charts: int | None = None,
        max_chart_slides: int | None = None,
        presentation_template: str = "executive",
    ) -> dict[str, Any]:
        """Run the full automatic pipeline.

        Args:
            df: The dataset DataFrame.
            dataset_name: Name of the dataset.
            industry: Detected industry.
            quality_score: Data quality score (0-100).
            max_charts: Maximum number of dashboard charts.
            max_chart_slides: Maximum number of presentation chart slides.
            presentation_template: Presentation template name.

        Returns:
            Dict containing:
              - understanding: DatasetUnderstanding
              - dashboard: DashboardSpecification
              - presentation: PresentationSpecification
        """
        # Compute dataset hash for versioning
        dataset_hash = self._compute_hash(df)

        # 1. Analyze dataset
        understanding = self.analysis_engine.analyze(
            df,
            dataset_name=dataset_name,
            industry=industry,
            quality_score=quality_score,
            dataset_hash=dataset_hash,
        )

        # 2. Select charts
        charts = self.chart_engine.select_charts(
            df,
            understanding,
            max_charts=max_charts,
        )

        # 3. Select KPIs
        kpis = self.kpi_engine.select_kpis(df, understanding)

        # 4. Generate insights
        insights = self.insight_engine.generate_insights(df, understanding)

        # 5. Select filters
        filters = self.filter_engine.select_filters(df, understanding)

        # 6. Generate recommendations from insights
        recommendations = [i.recommendation for i in insights if i.recommendation][:5]

        # 7. Generate dashboard layout
        dashboard = self.dashboard_layout_engine.generate_layout(
            title=f"{dataset_name} — Dashboard",
            subtitle=f"Auto-generated from {dataset_name} ({industry} industry)",
            industry=industry,
            dataset_name=dataset_name,
            dataset_hash=dataset_hash,
            kpis=kpis,
            charts=charts,
            filters=filters,
            insights=insights,
            recommendations=recommendations,
        )

        # 8. Generate presentation layout
        presentation = self.presentation_layout_engine.generate_presentation(
            dashboard=dashboard,
            template=presentation_template,
            max_chart_slides=max_chart_slides,
        )

        return {
            "understanding": understanding,
            "dashboard": dashboard,
            "presentation": presentation,
        }

    def generate_dashboard_only(
        self,
        df: pd.DataFrame,
        dataset_name: str = "uploaded_dataset",
        industry: str = "unknown",
        quality_score: float = 0.0,
        max_charts: int | None = None,
    ) -> DashboardSpecification:
        """Generate only the dashboard specification."""
        result = self.generate(
            df,
            dataset_name=dataset_name,
            industry=industry,
            quality_score=quality_score,
            max_charts=max_charts,
        )
        return result["dashboard"]

    def generate_presentation_only(
        self,
        df: pd.DataFrame,
        dataset_name: str = "uploaded_dataset",
        industry: str = "unknown",
        quality_score: float = 0.0,
        max_chart_slides: int | None = None,
        template: str = "executive",
    ) -> PresentationSpecification:
        """Generate only the presentation specification."""
        result = self.generate(
            df,
            dataset_name=dataset_name,
            industry=industry,
            quality_score=quality_score,
            max_chart_slides=max_chart_slides,
            presentation_template=template,
        )
        return result["presentation"]

    def explain_chart(self, chart: ChartSpecification) -> str:
        """Return the 'Why this chart?' explanation."""
        return self.chart_engine.explain_chart(chart)

    @staticmethod
    def _compute_hash(df: pd.DataFrame) -> str:
        """Compute a hash of the DataFrame for versioning."""
        try:
            # Use shape + column names + first/last rows for a quick hash
            content = f"{df.shape}|{list(df.columns)}|{df.head(1).to_csv()}|{df.tail(1).to_csv()}"
            return hashlib.sha256(content.encode()).hexdigest()[:16]
        except Exception:
            return ""
