"""Intelligent Automatic Analysis, Chart Selection & Layout Engine.

This package implements the automatic analysis pipeline:
  - Column semantic role detection
  - Intelligent chart selection with scoring & deduplication
  - Automatic KPI selection with computed values
  - Automatic insight generation from real data
  - Intelligent dashboard layout (responsive, no overlaps)
  - Automatic presentation layout with chart placement & validation
  - Canonical chart specifications (single source of truth)
  - Chart validation with fallback selection

All engines are deterministic â€” AI may explain results but never
invent statistical calculations or chart data.

The single entry point is VisualizationIntelligenceEngine:
  from services.auto import VisualizationIntelligenceEngine
  engine = VisualizationIntelligenceEngine()
  result = engine.generate(df, dataset_name="sales", industry="retail")
"""

from services.auto.engine import VisualizationIntelligenceEngine
from services.auto.validators import ChartValidator, ValidationResult

__all__ = [
    "VisualizationIntelligenceEngine",
    "ChartValidator",
    "ValidationResult",
]
