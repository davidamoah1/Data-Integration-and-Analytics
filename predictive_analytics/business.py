"""Business Predictive Analytics.

Sales forecasting and demand prediction for retail/business sectors.
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


class BusinessPredictiveAnalytics(PredictiveAnalyticsBase):
    """Predictive analytics for business/retail sectors."""

    def analyze(self, df: pd.DataFrame, col_mapping: dict) -> PredictiveIntelligenceResult:
        forecasts = []
        predictions = []

        # 1. Sales/Revenue Forecast
        revenue_col = self._find_numeric_col(
            df, col_mapping, ["revenue", "sales", "billing", "amount"]
        )
        date_col = self._find_date_col(df, col_mapping)

        if revenue_col and date_col:
            forecast = TimeSeriesForecaster.forecast(
                df,
                revenue_col,
                date_col,
                horizon=30,
                frequency="D",
                name="Sales Forecast",
            )
            if forecast:
                forecasts.append(forecast)

        # 2. Profit Forecast (if available)
        profit_col = self._find_numeric_col(df, col_mapping, ["profit", "margin"])
        if profit_col and date_col:
            forecast = TimeSeriesForecaster.forecast(
                df,
                profit_col,
                date_col,
                horizon=30,
                frequency="D",
                name="Profit Forecast",
            )
            if forecast:
                forecasts.append(forecast)

        # 3. Demand Prediction (regression)
        # Predict revenue/quantity based on other numeric features
        if revenue_col:
            feature_cols = [
                c
                for c in df.columns
                if pd.api.types.is_numeric_dtype(df[c])
                and c != revenue_col
                and c != date_col
                and "id" not in c.lower()
            ]
            if len(feature_cols) >= 1:
                pred = RegressionPredictor.predict(
                    df,
                    revenue_col,
                    feature_cols=feature_cols,
                    name="Demand Prediction",
                )
                if pred:
                    predictions.append(pred)

        # 4. Quantity/Volume Forecast
        quantity_col = self._find_numeric_col(
            df, col_mapping, ["quantity", "volume", "count", "units"]
        )
        if quantity_col and date_col and quantity_col != revenue_col:
            forecast = TimeSeriesForecaster.forecast(
                df,
                quantity_col,
                date_col,
                horizon=30,
                frequency="D",
                name="Demand Volume Forecast",
            )
            if forecast:
                forecasts.append(forecast)

        summary_parts = []
        if forecasts:
            summary_parts.append(f"{len(forecasts)} forecast(s) generated")
        if predictions:
            summary_parts.append(f"{len(predictions)} prediction(s) generated")
        summary = (
            " | ".join(summary_parts) if summary_parts else "No predictions could be generated."
        )

        return PredictiveIntelligenceResult(
            industry="retail",
            forecasts=forecasts,
            predictions=predictions,
            summary=summary,
        )


# Register for multiple industry keys
for industry in ("retail", "business", "banking", "government", "manufacturing", "ngo"):
    PredictiveAnalyticsRegistry.register(industry, BusinessPredictiveAnalytics)
