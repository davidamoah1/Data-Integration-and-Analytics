"""Data Quality Intelligence.

Automated data quality checks with intelligent detection of:
  - Missing values and blank fields
  - Duplicate data (rows and IDs)
  - Invalid values (sentinels, out-of-range, format violations)
  - Data drift (statistical distribution changes between periods)
  - Schema changes (added/removed/modified columns between runs)
  - Type mismatches (mixed data types within columns)

Each check produces a QualityFinding with severity, affected rows,
business impact, and suggested fix. The QualityEngine orchestrates
all checks and produces a composite quality score.

Usage:
    from data_quality import QualityEngine

    engine = QualityEngine()
    result = engine.run(df)
    # result.score â†’ 78.5 (yellow)
    # result.findings â†’ [QualityFinding(...), ...]
    # result.summary â†’ "3 warnings, 1 error detected..."
"""

from __future__ import annotations

from data_quality.checks import QualityCheckEngine, QualityFinding, Severity
from data_quality.drift_detector import ColumnDrift, DriftDetector, DriftResult
from data_quality.quality_engine import QualityEngine, QualityIntelligenceResult
from data_quality.schema_monitor import SchemaChange, SchemaChangeResult, SchemaMonitor

__all__ = [
    "QualityEngine",
    "QualityIntelligenceResult",
    "QualityCheckEngine",
    "QualityFinding",
    "Severity",
    "DriftDetector",
    "DriftResult",
    "ColumnDrift",
    "SchemaMonitor",
    "SchemaChangeResult",
    "SchemaChange",
]
