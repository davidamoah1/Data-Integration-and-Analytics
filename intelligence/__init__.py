"""Intelligent Analysis Engine — automatic column understanding,
chart selection, scoring, and canonical chart specification generation.

This module sits between the existing semantic/profiling pipeline and
the dashboard/report/presentation layers. It produces a canonical
ChartSpecification that becomes the single source of truth for all
visualization subsystems.

Pipeline:
    DataFrame → ColumnAnalyzer → ChartSelector → ChartSpecification[]
                    ↓                ↓
              semantic roles     importance scores
              KPI candidates     deduplication
              insights           "why this chart" explanations
"""
from __future__ import annotations

from .column_analyzer import ColumnAnalyzer, ColumnSemanticRole, DatasetUnderstanding
from .chart_selector import ChartSelector, ChartSpecification, ChartSelectionResult
from .kpi_selector import KPISelector, KPICandidate
from .insight_generator import InsightGenerator, Insight
from .dashboard_layout import DashboardLayoutEngine, DashboardLayout
from .presentation_layout import PresentationLayoutEngine, PresentationPlan

__all__ = [
    "ColumnAnalyzer",
    "ColumnSemanticRole",
    "DatasetUnderstanding",
    "ChartSelector",
    "ChartSpecification",
    "ChartSelectionResult",
    "KPISelector",
    "KPICandidate",
    "InsightGenerator",
    "Insight",
    "DashboardLayoutEngine",
    "DashboardLayout",
    "PresentationLayoutEngine",
    "PresentationPlan",
]
