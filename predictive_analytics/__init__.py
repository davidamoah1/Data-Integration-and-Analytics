"""Predictive Analytics Engine.

Moves from analytics to intelligence with:
  - Time series forecasting (sales, admissions, demand)
  - Regression prediction (crop yield, demand)
  - Risk classification (student risk, patient risk)

Industry-specific modules:
  - Business: sales forecasting, demand prediction
  - Healthcare: admission forecasting
  - Education: student risk prediction
  - Agriculture: yield prediction

Works directly on DataFrames — no database or external service required.

Usage:
    from predictive_analytics import PredictiveAnalyticsEngine

    result = PredictiveAnalyticsEngine.analyze("retail", df, col_mapping)
    # result.forecasts → [ForecastResult(...), ...]
    # result.predictions → [PredictionResult(...), ...]
"""

from __future__ import annotations

import predictive_analytics.agriculture  # noqa: F401

# Import industry modules to register them
import predictive_analytics.business  # noqa: F401
import predictive_analytics.education  # noqa: F401
import predictive_analytics.healthcare  # noqa: F401
from predictive_analytics.base import (
    ForecastResult,
    PredictionResult,
    PredictiveAnalyticsBase,
    PredictiveAnalyticsRegistry,
    PredictiveIntelligenceResult,
    RiskAssessment,
)
from predictive_analytics.classification import RiskClassifier
from predictive_analytics.forecasting import TimeSeriesForecaster
from predictive_analytics.regression import RegressionPredictor

__all__ = [
    "ForecastResult",
    "PredictionResult",
    "RiskAssessment",
    "PredictiveAnalyticsRegistry",
    "PredictiveAnalyticsBase",
    "PredictiveIntelligenceResult",
    "TimeSeriesForecaster",
    "RegressionPredictor",
    "RiskClassifier",
]
