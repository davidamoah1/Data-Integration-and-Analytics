"""Agriculture Predictive Analytics.

Crop yield prediction using regression analysis based on:
  - Rainfall
  - Fertilizer usage
  - Temperature
  - Farm area
  - Crop type
"""

from __future__ import annotations

import pandas as pd

from predictive_analytics.base import (
    PredictiveAnalyticsBase,
    PredictiveAnalyticsRegistry,
    PredictiveIntelligenceResult,
)
from predictive_analytics.forecasting import TimeSeriesForecaster
from predictive_analytics.regression import RegressionPredictor


class AgriculturePredictiveAnalytics(PredictiveAnalyticsBase):
    """Predictive analytics for agriculture sector."""

    def analyze(self, df: pd.DataFrame, col_mapping: dict) -> PredictiveIntelligenceResult:
        forecasts = []
        predictions = []

        date_col = self._find_date_col(df, col_mapping)

        # 1. Production/Harvest Forecast
        production_col = self._find_numeric_col(df, col_mapping, ["production", "harvest", "output", "yield"])
        if production_col and date_col:
            forecast = TimeSeriesForecaster.forecast(
                df, production_col, date_col,
                horizon=30, frequency="D",
                name="Production Forecast",
            )
            if forecast:
                forecasts.append(forecast)

        # 2. Yield Prediction (regression)
        # Predict yield based on rainfall, fertilizer, temperature, area
        yield_col = self._find_numeric_col(df, col_mapping, ["yield", "yield_per_hectare", "productivity"])
        if yield_col:
            feature_cols = []
            for entity in ["rainfall", "temperature", "fertilizer", "area", "humidity", "irrigation"]:
                col = self._find_numeric_col(df, col_mapping, [entity])
                if col and col != yield_col:
                    feature_cols.append(col)

            # Also include any other numeric columns that might be features
            for c in df.columns:
                if c not in feature_cols and c != yield_col and pd.api.types.is_numeric_dtype(df[c]):
                    col_lower = c.lower()
                    if any(kw in col_lower for kw in ("rain", "temp", "fertil", "area", "humid", "irrig", "water", "soil", "nitrogen", "phosphorus", "potassium")):
                        feature_cols.append(c)

            if feature_cols:
                pred = RegressionPredictor.predict(
                    df, yield_col, feature_cols=feature_cols,
                    name="Yield Prediction",
                )
                if pred:
                    predictions.append(pred)

        # 3. Production prediction (if no yield column, try production)
        if not predictions and production_col:
            feature_cols = []
            for entity in ["rainfall", "temperature", "fertilizer", "area", "humidity", "irrigation"]:
                col = self._find_numeric_col(df, col_mapping, [entity])
                if col and col != production_col:
                    feature_cols.append(col)

            for c in df.columns:
                if c not in feature_cols and c != production_col and pd.api.types.is_numeric_dtype(df[c]):
                    col_lower = c.lower()
                    if any(kw in col_lower for kw in ("rain", "temp", "fertil", "area", "humid", "irrig", "water", "soil")):
                        feature_cols.append(c)

            if feature_cols:
                pred = RegressionPredictor.predict(
                    df, production_col, feature_cols=feature_cols,
                    name="Production Prediction",
                )
                if pred:
                    predictions.append(pred)

        summary_parts = []
        if forecasts:
            summary_parts.append(f"{len(forecasts)} forecast(s) generated")
        if predictions:
            pred = predictions[0]
            summary_parts.append(f"R²={pred.r_squared:.2f} for {pred.name}")
        summary = " | ".join(summary_parts) if summary_parts else "No predictions could be generated."

        return PredictiveIntelligenceResult(
            industry="agriculture",
            forecasts=forecasts,
            predictions=predictions,
            summary=summary,
        )


PredictiveAnalyticsRegistry.register("agriculture", AgriculturePredictiveAnalytics)
