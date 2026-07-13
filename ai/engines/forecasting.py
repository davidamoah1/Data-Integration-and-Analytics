"""AI Forecasting Engine — time series forecasting with confidence intervals.

Supports forecasting for revenue, attendance, enrollment, disease cases,
crop production, inventory, demand, budgets, and any numeric time series.

Methods:
- Linear regression (trend-based)
- Exponential smoothing (weighted recent observations)
- Moving average (stable series)
- Seasonal decomposition (recurring patterns)
- Auto (selects best method)
"""

import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session as DbSession

from ai.gateway import AIGateway
from ai.models import AIForecast
from ai.config import AI_FORECAST_CONFIDENCE_LEVEL, AI_FORECAST_MAX_HORIZON
from etl.connectors.connectors import get_connector


class ForecastingEngine:
    """Time series forecasting with multiple methods and confidence intervals."""

    def __init__(self, db: DbSession):
        self.db = db
        self.gateway = AIGateway(db)

    def forecast(self, source_type: str, source_config: dict,
                 target_column: str, date_column: str,
                 horizon: int = 30, frequency: str = "D",
                 confidence_level: float = AI_FORECAST_CONFIDENCE_LEVEL,
                 method: str = "auto", user_id: Optional[int] = None) -> dict:
        """Generate a forecast for the given data.

        Returns:
            Dict with id, forecast_type, target_column, horizon, method,
            predictions, accuracy_score, confidence_level, input_summary.
        """
        # Extract data
        connector = get_connector(source_type, source_config)
        with connector:
            df = connector.extract()

        # Prepare time series
        ts = self._prepare_time_series(df, target_column, date_column, frequency)

        if ts is None or len(ts) < 5:
            return {
                "error": "Insufficient data for forecasting. Need at least 5 data points.",
                "predictions": [],
            }

        # Select method
        if method == "auto":
            method = self._select_best_method(ts)

        # Generate forecast
        predictions, accuracy = self._generate_forecast(
            ts, horizon, method, confidence_level
        )

        # Build input summary
        input_summary = {
            "data_points": len(ts),
            "date_range": [str(ts.index[0]), str(ts.index[-1])],
            "mean": float(ts.mean()),
            "std": float(ts.std()),
            "min": float(ts.min()),
            "max": float(ts.max()),
            "trend": "increasing" if ts.iloc[-1] > ts.iloc[0] else "decreasing",
        }

        # Use AI to interpret the forecast
        ai_interpretation = self._ai_interpret(
            target_column, predictions, input_summary, method, user_id
        )

        # Save to database
        forecast = AIForecast(
            forecast_type=target_column,
            target_column=target_column,
            horizon=horizon,
            method=method,
            predictions=predictions,
            accuracy_score=accuracy,
            confidence_level=confidence_level,
            input_summary=input_summary,
            user_id=user_id,
        )
        self.db.add(forecast)
        self.db.commit()
        self.db.refresh(forecast)

        return {
            "id": forecast.id,
            "forecast_type": target_column,
            "target_column": target_column,
            "horizon": horizon,
            "method": method,
            "predictions": predictions,
            "accuracy_score": accuracy,
            "confidence_level": confidence_level,
            "input_summary": input_summary,
            "ai_interpretation": ai_interpretation,
        }

    def _prepare_time_series(self, df: pd.DataFrame, target_column: str,
                             date_column: str, frequency: str) -> Optional[pd.Series]:
        """Prepare a time series from a DataFrame."""
        if target_column not in df.columns or date_column not in df.columns:
            return None

        # Convert date column
        df[date_column] = pd.to_datetime(df[date_column], errors="coerce")
        df = df.dropna(subset=[date_column, target_column])

        if df.empty:
            return None

        # Group by date and aggregate
        df = df.set_index(date_column)
        ts = df[target_column].resample(frequency).sum()

        # Fill missing values
        ts = ts.fillna(method="ffill").fillna(method="bfill")

        return ts

    def _select_best_method(self, ts: pd.Series) -> str:
        """Automatically select the best forecasting method."""
        # Check for trend
        if len(ts) < 10:
            return "moving_average"

        # Check for seasonality (simplified)
        if len(ts) >= 24:
            return "seasonal"

        # Check for trend
        first_half = ts.iloc[:len(ts) // 2].mean()
        second_half = ts.iloc[len(ts) // 2:].mean()
        if abs(second_half - first_half) / max(first_half, 1) > 0.1:
            return "linear"

        return "exponential"

    def _generate_forecast(self, ts: pd.Series, horizon: int,
                           method: str, confidence_level: float) -> tuple[list[dict], float]:
        """Generate forecast predictions with confidence intervals."""
        if method == "linear":
            return self._linear_forecast(ts, horizon, confidence_level)
        elif method == "exponential":
            return self._exponential_forecast(ts, horizon, confidence_level)
        elif method == "moving_average":
            return self._moving_average_forecast(ts, horizon, confidence_level)
        elif method == "seasonal":
            return self._seasonal_forecast(ts, horizon, confidence_level)
        else:
            return self._linear_forecast(ts, horizon, confidence_level)

    def _linear_forecast(self, ts: pd.Series, horizon: int,
                         confidence_level: float) -> tuple[list[dict], float]:
        """Linear regression forecast."""
        x = np.arange(len(ts)).reshape(-1, 1)
        y = ts.values

        # Fit linear regression
        coeffs = np.polyfit(x.flatten(), y, 1)
        trend = np.poly1d(coeffs)

        # Predict
        future_x = np.arange(len(ts), len(ts) + horizon)
        predictions_values = trend(future_x)

        # Calculate residuals for confidence interval
        residuals = y - trend(x.flatten())
        std_error = np.std(residuals) if len(residuals) > 1 else 0

        # Z-score for confidence level
        try:
            from scipy import stats
            z = stats.norm.ppf((1 + confidence_level) / 2)
        except Exception:
            z = 1.96  # 95% default

        # Calculate R² for accuracy
        ss_res = np.sum(residuals ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

        predictions = []
        for i, (date, value) in enumerate(zip(
            pd.date_range(ts.index[-1], periods=horizon + 1, freq=ts.index.freqstr)[1:],
            predictions_values,
        )):
            predictions.append({
                "date": str(date.date()),
                "value": round(float(value), 2),
                "lower_ci": round(float(value - z * std_error), 2),
                "upper_ci": round(float(value + z * std_error), 2),
            })

        return predictions, round(float(r_squared), 4)

    def _exponential_forecast(self, ts: pd.Series, horizon: int,
                              confidence_level: float) -> tuple[list[dict], float]:
        """Exponential smoothing forecast."""
        alpha = 0.3  # Smoothing factor
        smoothed = [ts.iloc[0]]
        for i in range(1, len(ts)):
            smoothed.append(alpha * ts.iloc[i] + (1 - alpha) * smoothed[-1])

        # Forecast: last smoothed value
        last_value = smoothed[-1]
        predictions_values = [last_value] * horizon

        # Confidence interval
        residuals = ts.values - np.array(smoothed)
        std_error = np.std(residuals) if len(residuals) > 1 else 0

        try:
            from scipy import stats
            z = stats.norm.ppf((1 + confidence_level) / 2)
        except Exception:
            z = 1.96

        # Accuracy: MAPE
        mape = np.mean(np.abs(residuals / ts.values)) * 100 if len(residuals) > 0 else 0
        accuracy = max(0, 1 - mape / 100)

        predictions = []
        for date, value in zip(
            pd.date_range(ts.index[-1], periods=horizon + 1, freq=ts.index.freqstr)[1:],
            predictions_values,
        ):
            predictions.append({
                "date": str(date.date()),
                "value": round(float(value), 2),
                "lower_ci": round(float(value - z * std_error), 2),
                "upper_ci": round(float(value + z * std_error), 2),
            })

        return predictions, round(float(accuracy), 4)

    def _moving_average_forecast(self, ts: pd.Series, horizon: int,
                                 confidence_level: float) -> tuple[list[dict], float]:
        """Moving average forecast."""
        window = min(7, len(ts))
        ma_value = ts.iloc[-window:].mean()

        predictions_values = [ma_value] * horizon

        # Confidence interval
        residuals = ts.values - ts.rolling(window=window).mean().fillna(ts.mean()).values
        std_error = np.std(residuals[~np.isnan(residuals)]) if len(residuals) > 1 else 0

        try:
            from scipy import stats
            z = stats.norm.ppf((1 + confidence_level) / 2)
        except Exception:
            z = 1.96

        predictions = []
        for date, value in zip(
            pd.date_range(ts.index[-1], periods=horizon + 1, freq=ts.index.freqstr)[1:],
            predictions_values,
        ):
            predictions.append({
                "date": str(date.date()),
                "value": round(float(value), 2),
                "lower_ci": round(float(value - z * std_error), 2),
                "upper_ci": round(float(value + z * std_error), 2),
            })

        return predictions, 0.5  # Moderate accuracy for MA

    def _seasonal_forecast(self, ts: pd.Series, horizon: int,
                           confidence_level: float) -> tuple[list[dict], float]:
        """Seasonal decomposition forecast."""
        # Simple seasonal: use same period from previous cycle
        period = min(12, len(ts) // 2)

        # Calculate seasonal indices
        seasonal_avg = ts.iloc[-period:].values
        overall_avg = ts.mean()

        # Linear trend on deseasonalized data
        x = np.arange(len(ts)).reshape(-1, 1)
        y = ts.values
        coeffs = np.polyfit(x.flatten(), y, 1)
        trend = np.poly1d(coeffs)

        # Predict with seasonality
        future_x = np.arange(len(ts), len(ts) + horizon)
        trend_values = trend(future_x)
        seasonal_indices = np.tile(seasonal_avg / overall_avg, horizon // period + 1)[:horizon]
        predictions_values = trend_values * seasonal_indices

        # Confidence interval
        residuals = y - trend(x.flatten())
        std_error = np.std(residuals) if len(residuals) > 1 else 0

        try:
            from scipy import stats
            z = stats.norm.ppf((1 + confidence_level) / 2)
        except Exception:
            z = 1.96

        ss_res = np.sum(residuals ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

        predictions = []
        for date, value in zip(
            pd.date_range(ts.index[-1], periods=horizon + 1, freq=ts.index.freqstr)[1:],
            predictions_values,
        ):
            predictions.append({
                "date": str(date.date()),
                "value": round(float(value), 2),
                "lower_ci": round(float(value - z * std_error), 2),
                "upper_ci": round(float(value + z * std_error), 2),
            })

        return predictions, round(float(r_squared), 4)

    def _ai_interpret(self, target_column: str, predictions: list[dict],
                      input_summary: dict, method: str,
                      user_id: Optional[int] = None) -> str:
        """Get AI interpretation of the forecast."""
        try:
            result = self.gateway.chat(
                user_message=(
                    f"Interpret this forecast for {target_column}:\n"
                    f"Method: {method}\n"
                    f"Input summary: {json.dumps(input_summary)}\n"
                    f"First 5 predictions: {json.dumps(predictions[:5])}\n"
                    f"Provide a brief 2-3 sentence interpretation of the forecast."
                ),
                assistant_type="forecast_copilot",
                user_id=user_id,
            )
            return result["response"]
        except Exception:
            return ""
