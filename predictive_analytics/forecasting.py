"""Time Series Forecaster.

Core forecasting engine with 4 methods:
  - Linear regression (trend-based)
  - Exponential smoothing (weighted recent observations)
  - Moving average (stable series)
  - Seasonal decomposition (recurring patterns)

Auto-selects the best method based on data characteristics.
Produces forecasts with confidence intervals and accuracy metrics.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from predictive_analytics.base import ForecastPoint, ForecastResult


class TimeSeriesForecaster:
    """Time series forecasting with multiple methods and confidence intervals."""

    @staticmethod
    def forecast(
        df: pd.DataFrame,
        metric_col: str,
        date_col: str,
        horizon: int = 30,
        frequency: str = "D",
        method: str = "auto",
        name: str | None = None,
    ) -> ForecastResult | None:
        """Generate a forecast for a metric over time.

        Args:
            df: DataFrame with the data.
            metric_col: Column name of the metric to forecast.
            date_col: Column name of the date column.
            horizon: Number of periods to forecast.
            frequency: Resampling frequency (D, W, M, Q, Y).
            method: Forecasting method ("auto", "linear", "exponential",
                    "moving_average", "seasonal").
            name: Display name for the forecast.

        Returns:
            ForecastResult with predictions and accuracy, or None if
            insufficient data.
        """
        ts = TimeSeriesForecaster._prepare_time_series(df, metric_col, date_col, frequency)
        if ts is None or len(ts) < 5:
            return None

        if method == "auto":
            method = TimeSeriesForecaster._select_best_method(ts)

        predictions, accuracy = TimeSeriesForecaster._generate_forecast(
            ts, horizon, method, confidence_level=0.95
        )

        # Determine trend
        first_val = float(ts.iloc[0])
        last_val = float(ts.iloc[-1])
        if first_val != 0:
            trend_pct = ((last_val - first_val) / abs(first_val)) * 100
        else:
            trend_pct = 0.0
        if trend_pct > 5:
            trend = "increasing"
        elif trend_pct < -5:
            trend = "decreasing"
        else:
            trend = "stable"

        # Accuracy label
        if accuracy >= 0.8:
            accuracy_label = "high"
        elif accuracy >= 0.5:
            accuracy_label = "moderate"
        else:
            accuracy_label = "low"

        input_summary = {
            "data_points": len(ts),
            "date_range": [str(ts.index[0].date()), str(ts.index[-1].date())],
            "mean": round(float(ts.mean()), 2),
            "std": round(float(ts.std()), 2),
            "min": round(float(ts.min()), 2),
            "max": round(float(ts.max()), 2),
        }

        name = name or f"{metric_col.replace('_', ' ').title()} Forecast"

        summary = TimeSeriesForecaster._generate_summary(
            name, method, accuracy, accuracy_label, trend, trend_pct, predictions
        )

        return ForecastResult(
            name=name,
            metric=metric_col,
            method=method,
            horizon=horizon,
            predictions=predictions,
            accuracy=accuracy,
            accuracy_label=accuracy_label,
            trend=trend,
            trend_pct=trend_pct,
            summary=summary,
            input_summary=input_summary,
        )

    @staticmethod
    def _prepare_time_series(
        df: pd.DataFrame, metric_col: str, date_col: str, frequency: str
    ) -> pd.Series | None:
        """Prepare a time series from a DataFrame."""
        if metric_col not in df.columns or date_col not in df.columns:
            return None
        if not pd.api.types.is_numeric_dtype(df[metric_col]):
            return None

        df = df.copy()
        if not pd.api.types.is_datetime64_any_dtype(df[date_col]):
            df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        df = df.dropna(subset=[date_col, metric_col])

        if df.empty:
            return None

        df = df.set_index(date_col)
        ts = df[metric_col].resample(frequency).sum()
        ts = ts.ffill().bfill()

        return ts

    @staticmethod
    def _select_best_method(ts: pd.Series) -> str:
        """Automatically select the best forecasting method."""
        if len(ts) < 10:
            return "moving_average"
        if len(ts) >= 24:
            return "seasonal"
        first_half = ts.iloc[: len(ts) // 2].mean()
        second_half = ts.iloc[len(ts) // 2 :].mean()
        if abs(second_half - first_half) / max(abs(first_half), 1) > 0.1:
            return "linear"
        return "exponential"

    @staticmethod
    def _generate_forecast(
        ts: pd.Series, horizon: int, method: str, confidence_level: float
    ) -> tuple[list[ForecastPoint], float]:
        if method == "linear":
            return TimeSeriesForecaster._linear_forecast(ts, horizon, confidence_level)
        elif method == "exponential":
            return TimeSeriesForecaster._exponential_forecast(ts, horizon, confidence_level)
        elif method == "moving_average":
            return TimeSeriesForecaster._moving_average_forecast(ts, horizon, confidence_level)
        elif method == "seasonal":
            return TimeSeriesForecaster._seasonal_forecast(ts, horizon, confidence_level)
        else:
            return TimeSeriesForecaster._linear_forecast(ts, horizon, confidence_level)

    @staticmethod
    def _linear_forecast(ts: pd.Series, horizon: int, confidence_level: float) -> tuple[list[ForecastPoint], float]:
        x = np.arange(len(ts))
        y = ts.values

        coeffs = np.polyfit(x, y, 1)
        trend = np.poly1d(coeffs)

        future_x = np.arange(len(ts), len(ts) + horizon)
        predicted = trend(future_x)

        residuals = y - trend(x)
        std_error = float(np.std(residuals)) if len(residuals) > 1 else 0.0

        z = 1.96
        try:
            from scipy import stats
            z = float(stats.norm.ppf((1 + confidence_level) / 2))
        except Exception:
            pass

        ss_res = float(np.sum(residuals**2))
        ss_tot = float(np.sum((y - np.mean(y)) ** 2))
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

        future_dates = pd.date_range(ts.index[-1], periods=horizon + 1, freq=ts.index.freqstr)[1:]
        predictions = [
            ForecastPoint(
                date=str(d.date()),
                value=max(0, float(v)),
                lower_ci=max(0, float(v - z * std_error)),
                upper_ci=float(v + z * std_error),
            )
            for d, v in zip(future_dates, predicted, strict=False)
        ]

        return predictions, r_squared

    @staticmethod
    def _exponential_forecast(ts: pd.Series, horizon: int, confidence_level: float) -> tuple[list[ForecastPoint], float]:
        alpha = 0.3
        smoothed = [float(ts.iloc[0])]
        for i in range(1, len(ts)):
            smoothed.append(alpha * float(ts.iloc[i]) + (1 - alpha) * smoothed[-1])

        last_value = smoothed[-1]
        predicted = [last_value] * horizon

        residuals = ts.values - np.array(smoothed)
        std_error = float(np.std(residuals)) if len(residuals) > 1 else 0.0

        z = 1.96
        try:
            from scipy import stats
            z = float(stats.norm.ppf((1 + confidence_level) / 2))
        except Exception:
            pass

        mape = float(np.mean(np.abs(residuals / ts.values))) * 100 if len(residuals) > 0 else 0
        accuracy = max(0, 1 - mape / 100)

        future_dates = pd.date_range(ts.index[-1], periods=horizon + 1, freq=ts.index.freqstr)[1:]
        predictions = [
            ForecastPoint(
                date=str(d.date()),
                value=max(0, float(v)),
                lower_ci=max(0, float(v - z * std_error)),
                upper_ci=float(v + z * std_error),
            )
            for d, v in zip(future_dates, predicted, strict=False)
        ]

        return predictions, accuracy

    @staticmethod
    def _moving_average_forecast(ts: pd.Series, horizon: int, confidence_level: float) -> tuple[list[ForecastPoint], float]:
        window = min(7, len(ts))
        ma_value = float(ts.iloc[-window:].mean())
        predicted = [ma_value] * horizon

        rolling_ma = ts.rolling(window=window).mean().fillna(ts.mean())
        residuals = ts.values - rolling_ma.values
        residuals = residuals[~np.isnan(residuals)]
        std_error = float(np.std(residuals)) if len(residuals) > 1 else 0.0

        z = 1.96
        try:
            from scipy import stats
            z = float(stats.norm.ppf((1 + confidence_level) / 2))
        except Exception:
            pass

        future_dates = pd.date_range(ts.index[-1], periods=horizon + 1, freq=ts.index.freqstr)[1:]
        predictions = [
            ForecastPoint(
                date=str(d.date()),
                value=max(0, float(v)),
                lower_ci=max(0, float(v - z * std_error)),
                upper_ci=float(v + z * std_error),
            )
            for d, v in zip(future_dates, predicted, strict=False)
        ]

        return predictions, 0.5

    @staticmethod
    def _seasonal_forecast(ts: pd.Series, horizon: int, confidence_level: float) -> tuple[list[ForecastPoint], float]:
        period = min(12, len(ts) // 2)
        seasonal_avg = ts.iloc[-period:].values
        overall_avg = float(ts.mean())

        x = np.arange(len(ts))
        y = ts.values
        coeffs = np.polyfit(x, y, 1)
        trend = np.poly1d(coeffs)

        future_x = np.arange(len(ts), len(ts) + horizon)
        trend_values = trend(future_x)
        seasonal_indices = np.tile(seasonal_avg / overall_avg, horizon // period + 1)[:horizon]
        predicted = trend_values * seasonal_indices

        residuals = y - trend(x)
        std_error = float(np.std(residuals)) if len(residuals) > 1 else 0.0

        z = 1.96
        try:
            from scipy import stats
            z = float(stats.norm.ppf((1 + confidence_level) / 2))
        except Exception:
            pass

        ss_res = float(np.sum(residuals**2))
        ss_tot = float(np.sum((y - np.mean(y)) ** 2))
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

        future_dates = pd.date_range(ts.index[-1], periods=horizon + 1, freq=ts.index.freqstr)[1:]
        predictions = [
            ForecastPoint(
                date=str(d.date()),
                value=max(0, float(v)),
                lower_ci=max(0, float(v - z * std_error)),
                upper_ci=float(v + z * std_error),
            )
            for d, v in zip(future_dates, predicted, strict=False)
        ]

        return predictions, r_squared

    @staticmethod
    def _generate_summary(
        name: str, method: str, accuracy: float, accuracy_label: str,
        trend: str, trend_pct: float, predictions: list[ForecastPoint],
    ) -> str:
        parts = [f"{name} ({method} method):"]
        parts.append(f"Accuracy: {accuracy:.1%} ({accuracy_label})")
        parts.append(f"Trend: {trend} ({trend_pct:+.1f}%)")
        if predictions:
            first = predictions[0]
            last = predictions[-1]
            parts.append(
                f"Forecast: {first.value:,.0f} on {first.date} → "
                f"{last.value:,.0f} on {last.date} over {len(predictions)} periods"
            )
        return " | ".join(parts)
