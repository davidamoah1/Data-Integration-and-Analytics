"""Time-series forecasting engine.

Provides ARIMA, Exponential Smoothing, and optional Prophet support. Forecasts
include confidence intervals where applicable.
"""

from __future__ import annotations

from typing import Any

import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.holtwinters import ExponentialSmoothing

from ml.metrics import forecast_metrics


def _prepare_series(df: pd.DataFrame, date_col: str, target_col: str, freq: str = "D") -> pd.Series:
    """Return a regularly spaced DatetimeIndex series."""
    df = df[[date_col, target_col]].copy()
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=[date_col, target_col])
    series = df.set_index(date_col)[target_col].sort_index()
    series = series.asfreq(freq)
    series = series.interpolate(method="linear").ffill().bfill()
    return series


def forecast_arima(series: pd.Series, horizon: int) -> dict[str, Any]:
    """Run ARIMA forecast."""
    try:
        model = ARIMA(series, order=(1, 1, 1))
        fitted = model.fit()
        pred = fitted.get_forecast(steps=horizon)
        mean = pred.predicted_mean.values
        conf = pred.conf_int(alpha=0.05)
        return {
            "algorithm": "ARIMA",
            "values": mean.tolist(),
            "lower": conf.iloc[:, 0].values.tolist(),
            "upper": conf.iloc[:, 1].values.tolist(),
            "aic": float(fitted.aic),
        }
    except Exception as exc:
        return {"algorithm": "ARIMA", "error": str(exc)}


def forecast_ets(series: pd.Series, horizon: int, seasonal: str = "add") -> dict[str, Any]:
    """Run Exponential Smoothing forecast."""
    try:
        seasonal_periods = 7 if len(series) >= 14 else None
        if seasonal_periods:
            model = ExponentialSmoothing(
                series, trend="add", seasonal=seasonal, seasonal_periods=seasonal_periods
            )
        else:
            model = ExponentialSmoothing(series, trend="add")
        fitted = model.fit(optimized=True)
        pred = fitted.forecast(horizon)
        return {
            "algorithm": "ExponentialSmoothing",
            "values": pred.tolist(),
            "aic": float(fitted.aic) if hasattr(fitted, "aic") else None,
        }
    except Exception as exc:
        return {"algorithm": "ExponentialSmoothing", "error": str(exc)}


def forecast_prophet(
    df: pd.DataFrame, date_col: str, target_col: str, horizon: int, freq: str = "D"
) -> dict[str, Any]:
    """Run Prophet forecast if available."""
    try:
        from prophet import Prophet  # type: ignore
    except ImportError:
        return {"algorithm": "Prophet", "error": "Prophet not installed"}

    try:
        pdata = df[[date_col, target_col]].rename(columns={date_col: "ds", target_col: "y"})
        model = Prophet(daily_seasonality=True)
        model.fit(pdata)
        future = model.make_future_dataframe(periods=horizon, freq=freq)
        forecast = model.predict(future)
        forecast_tail = forecast.tail(horizon)
        return {
            "algorithm": "Prophet",
            "values": forecast_tail["yhat"].tolist(),
            "lower": forecast_tail["yhat_lower"].tolist(),
            "upper": forecast_tail["yhat_upper"].tolist(),
        }
    except Exception as exc:
        return {"algorithm": "Prophet", "error": str(exc)}


class ForecastingEngine:
    """Train and run forecasting models."""

    def __init__(self, algorithm: str = "auto", frequency: str = "D") -> None:
        self.algorithm = algorithm
        self.frequency = frequency
        self.last_values: pd.Series | None = None
        self.fitted_model: Any = None

    def fit(self, df: pd.DataFrame, date_col: str, target_col: str) -> dict[str, Any]:
        """Fit a forecasting model and return a summary."""
        self.last_values = _prepare_series(df, date_col, target_col, self.frequency)
        if len(self.last_values) < 3:
            return {"status": "failed", "error": "Need at least 3 observations"}

        if self.algorithm == "ARIMA":
            self.fitted_model = ARIMA(self.last_values, order=(1, 1, 1)).fit()
        elif self.algorithm == "ExponentialSmoothing":
            seasonal_periods = 7 if len(self.last_values) >= 14 else None
            if seasonal_periods:
                model = ExponentialSmoothing(
                    self.last_values, trend="add", seasonal="add", seasonal_periods=seasonal_periods
                )
            else:
                model = ExponentialSmoothing(self.last_values, trend="add")
            self.fitted_model = model.fit()
        else:
            # Auto-select: try ETS, fallback to ARIMA
            try:
                seasonal_periods = 7 if len(self.last_values) >= 14 else None
                if seasonal_periods:
                    model = ExponentialSmoothing(
                        self.last_values,
                        trend="add",
                        seasonal="add",
                        seasonal_periods=seasonal_periods,
                    )
                else:
                    model = ExponentialSmoothing(self.last_values, trend="add")
                self.fitted_model = model.fit()
                self.algorithm = "ExponentialSmoothing"
            except Exception:
                self.fitted_model = ARIMA(self.last_values, order=(1, 1, 1)).fit()
                self.algorithm = "ARIMA"

        return {
            "status": "completed",
            "algorithm": self.algorithm,
            "series_length": int(len(self.last_values)),
        }

    def predict(self, horizon: int) -> dict[str, Any]:
        """Generate a forecast for the given horizon."""
        if self.fitted_model is None or self.last_values is None:
            return {"status": "failed", "error": "Model not fitted"}

        if self.algorithm == "ARIMA":
            pred = self.fitted_model.get_forecast(steps=horizon)
            mean = pred.predicted_mean.values
            conf = pred.conf_int(alpha=0.05)
            return {
                "status": "completed",
                "algorithm": self.algorithm,
                "values": mean.tolist(),
                "lower": conf.iloc[:, 0].values.tolist(),
                "upper": conf.iloc[:, 1].values.tolist(),
            }

        values = self.fitted_model.forecast(horizon).values
        return {"status": "completed", "algorithm": self.algorithm, "values": values.tolist()}

    def evaluate_holdout(self, test_size: int = 7) -> dict[str, float]:
        """Evaluate the fitted model against a hold-out window."""
        if self.last_values is None or len(self.last_values) <= test_size + 3:
            return {}
        train = self.last_values.iloc[:-test_size]
        test = self.last_values.iloc[-test_size:]
        try:
            model = ARIMA(train, order=(1, 1, 1)).fit()
            pred = model.forecast(steps=test_size)
            return forecast_metrics(test.values, pred.values)
        except Exception:
            return {}
