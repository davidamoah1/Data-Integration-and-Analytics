"""Auto Engine Orchestrator.

Ties all automatic engines together into a single pipeline:

  DataFrame + metadata
       â”‚
       â–¼
  AutomaticAnalysisEngine  â†’ DatasetUnderstanding
       â”‚
       â–¼
  IntelligentChartSelectionEngine â†’ list[ChartSpecification]
       â”‚
       â–¼
  AutomaticKPIEngine â†’ list[KPISpecification]
       â”‚
       â–¼
  AutomaticInsightEngine â†’ list[InsightSpecification]
       â”‚
       â–¼
  AutomaticFilterEngine â†’ list[FilterSpecification]
       â”‚
       â–¼
  IntelligentDashboardLayoutEngine â†’ DashboardSpecification
       â”‚
       â–¼
  PresentationLayoutEngine â†’ PresentationSpecification

The DashboardSpecification and PresentationSpecification share the
SAME ChartSpecification objects â€” they are the single source of truth.
"""

from __future__ import annotations

import hashlib
import logging
from typing import Any

import pandas as pd

from services.auto.chart_specification import (
    ChartSpecification,
    DashboardSpecification,
    PresentationSpecification,
)
from services.auto.engine import VisualizationIntelligenceEngine

logger = logging.getLogger(__name__)


class AutoEngineOrchestrator:
    """Orchestrates the full automatic analysis â†’ visualization â†’ layout pipeline.

    This is a thin wrapper around VisualizationIntelligenceEngine that
    preserves the existing API. New code should use
    VisualizationIntelligenceEngine directly.
    """

    def __init__(self) -> None:
        self._engine = VisualizationIntelligenceEngine()
        # Expose sub-engines for backward compatibility
        self.analysis_engine = self._engine.analysis_engine
        self.chart_engine = self._engine.chart_engine
        self.kpi_engine = self._engine.kpi_engine
        self.insight_engine = self._engine.insight_engine
        self.filter_engine = self._engine.filter_engine
        self.dashboard_layout_engine = self._engine.dashboard_layout_engine
        self.presentation_layout_engine = self._engine.presentation_layout_engine
        self.validator = self._engine.validator

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

        Delegates to VisualizationIntelligenceEngine which includes
        chart validation and fallback.
        """
        return self._engine.generate(
            df,
            dataset_name=dataset_name,
            industry=industry,
            quality_score=quality_score,
            max_charts=max_charts,
            max_chart_slides=max_chart_slides,
            presentation_template=presentation_template,
        )

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
