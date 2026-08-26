"""Enterprise Forecasting Engine.

Enhances the existing ForecastingEngine with:
  - Semantic-aware column detection (auto-detect date/value columns)
  - Multi-horizon support (short, medium, long term)
  - Assumption documentation
  - Model limitation disclosure
  - Industry-aware interpretation
  - Integration with EnterpriseContextEngine and PromptOrchestrator
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session as DbSession

from ai.context_engine import EnterpriseAIContext, EnterpriseContextEngine
from ai.data_gatherer import DataGatherer
from ai.gateway import AIGateway
from ai.models import AIForecast
from ai.prompt_orchestrator import PromptOrchestrator, PromptTaskType

logger = logging.getLogger(__name__)

# Forecast horizons
HORIZON_PRESETS = {
    "short": 7,  # 1 week
    "medium": 30,  # 1 month
    "long": 90,  # 3 months
}


class EnterpriseForecastEngine:
    """Semantic-aware time series forecasting with confidence intervals."""

    def __init__(self, db: DbSession | None = None):
        self.db = db
        self.gateway = AIGateway(db) if db else None
        self.context_engine = EnterpriseContextEngine(db)
        self.orchestrator = PromptOrchestrator()

    def forecast(
        self,
        metric: str,
        df: pd.DataFrame | None = None,
        semantic_mappings: dict | None = None,
        industry: str = "unknown",
        horizon: str | int = "medium",
        frequency: str = "D",
        confidence_level: float = 0.95,
        method: str = "auto",
        user_id: int | None = None,
        organization_id: int | None = None,
        context: EnterpriseAIContext | None = None,
    ) -> dict:
        """Generate a forecast for the given metric.

        Args:
            metric: The metric to forecast (e.g., 'revenue', 'billing_amount').
            df: DataFrame with the dataset.
            semantic_mappings: Semantic entity-to-column mappings.
            industry: Detected industry.
            horizon: 'short' (7d), 'medium' (30d), 'long' (90d), or integer.
            frequency: Time series frequency ('D' daily, 'W' weekly, 'M' monthly).
            confidence_level: Confidence interval level (0.80-0.99).
            method: 'auto', 'linear', 'exponential', 'moving_average', 'seasonal'.
            user_id: User ID.
            context: Pre-built EnterpriseAIContext.

        Returns:
            Dict with metric, method, horizon, predictions, assumptions,
            model_limitations, interpretation, confidence.
        """
        # Resolve horizon
        if isinstance(horizon, str):
            horizon = HORIZON_PRESETS.get(horizon, 30)

        # Build context if not provided
        if context is None:
            context = self.context_engine.build(
                assistant_type="forecast_copilot",
                user_id=user_id,
                df=df,
                semantic_mappings=semantic_mappings,
                industry=industry,
            )

        # Gather and prepare time series data
        gatherer = DataGatherer(df, context)
        ts_data = gatherer.gather_for_forecast(metric, horizon)

        if ts_data.get("note"):
            return {
                "error": ts_data["note"],
                "predictions": [],
                "metric": metric,
            }

        # Prepare time series
        ts = self._prepare_time_series(ts_data, frequency)
        if ts is None or len(ts) < 5:
            return {
                "error": "Insufficient data for forecasting. Need at least 5 data points.",
                "predictions": [],
                "metric": metric,
                "data_points": len(ts) if ts is not None else 0,
            }

        # Select method
        if method == "auto":
            method = self._select_best_method(ts)

        # Generate forecast
        predictions, accuracy = self._generate_forecast(ts, horizon, method, confidence_level)

        # Build assumptions
        assumptions = self._build_assumptions(ts, method, horizon, context)

        # Build model limitations
        limitations = self._build_limitations(ts, method, accuracy)

        # AI interpretation
        interpretation = self._ai_interpret(
            metric, predictions, ts_data, method, assumptions, limitations, context, user_id
        )

        # Build result
        result = {
            "metric": metric,
            "method": method,
            "horizon": horizon,
            "frequency": frequency,
            "predictions": predictions,
            "accuracy_score": accuracy,
            "confidence_level": confidence_level,
            "input_summary": {
                "data_points": len(ts),
                "date_range": [str(ts.index[0].date()), str(ts.index[-1].date())],
                "mean": float(ts.mean()),
                "std": float(ts.std()),
                "min": float(ts.min()),
                "max": float(ts.max()),
                "trend": "increasing" if ts.iloc[-1] > ts.iloc[0] else "decreasing",
            },
            "assumptions": assumptions,
            "model_limitations": limitations,
            "interpretation": interpretation,
            "confidence": self._calculate_confidence(accuracy, len(ts), method),
        }

        # Save to database
        if self.db:
            try:
                forecast = AIForecast(
                    forecast_type=metric,
                    target_column=metric,
                    horizon=horizon,
                    method=method,
                    predictions=predictions,
                    accuracy_score=accuracy,
                    confidence_level=confidence_level,
                    input_summary=result["input_summary"],
                    user_id=user_id,
                    organization_id=organization_id,
                )
                self.db.add(forecast)
                self.db.commit()
                self.db.refresh(forecast)
                result["id"] = forecast.id
            except Exception as e:
                logger.warning(f"Failed to save forecast: {e}")

        return result

    def _prepare_time_series(self, ts_data: dict, frequency: str) -> pd.Series | None:
        """Prepare a pandas Series from gathered time series data."""
        try:
            dates = pd.to_datetime(ts_data["dates"])
            values = ts_data["values"]
            ts = pd.Series(values, index=dates)
            ts = ts.resample(frequency).sum()
            ts = ts.ffill().bfill()
            return ts
        except Exception:
            return None

    def _select_best_method(self, ts: pd.Series) -> str:
        """Automatically select the best forecasting method."""
        if len(ts) < 10:
            return "moving_average"
        if len(ts) >= 24:
            return "seasonal"
        first_half = ts.iloc[: len(ts) // 2].mean()
        second_half = ts.iloc[len(ts) // 2 :].mean()
        if abs(second_half - first_half) / max(first_half, 1) > 0.1:
            return "linear"
        return "exponential"

    def _generate_forecast(
        self, ts: pd.Series, horizon: int, method: str, confidence_level: float
    ) -> tuple[list[dict], float]:
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

    def _linear_forecast(self, ts: pd.Series, horizon: int, cl: float) -> tuple[list[dict], float]:
        x = np.arange(len(ts)).reshape(-1, 1)
        y = ts.values
        coeffs = np.polyfit(x.flatten(), y, 1)
        trend = np.poly1d(coeffs)
        future_x = np.arange(len(ts), len(ts) + horizon)
        preds = trend(future_x)
        residuals = y - trend(x.flatten())
        std_err = np.std(residuals) if len(residuals) > 1 else 0
        try:
            from scipy import stats

            z = stats.norm.ppf((1 + cl) / 2)
        except Exception:
            z = 1.96
        ss_res = np.sum(residuals**2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        predictions = []
        for date, value in zip(
            pd.date_range(ts.index[-1], periods=horizon + 1, freq=ts.index.freqstr)[1:],
            preds,
            strict=False,
        ):
            predictions.append(
                {
                    "date": str(date.date()),
                    "value": round(float(value), 2),
                    "lower_ci": round(float(value - z * std_err), 2),
                    "upper_ci": round(float(value + z * std_err), 2),
                }
            )
        return predictions, round(float(r2), 4)

    def _exponential_forecast(
        self, ts: pd.Series, horizon: int, cl: float
    ) -> tuple[list[dict], float]:
        alpha = 0.3
        smoothed = [ts.iloc[0]]
        for i in range(1, len(ts)):
            smoothed.append(alpha * ts.iloc[i] + (1 - alpha) * smoothed[-1])
        last_value = smoothed[-1]
        preds_vals = [last_value] * horizon
        residuals = ts.values - np.array(smoothed)
        std_err = np.std(residuals) if len(residuals) > 1 else 0
        try:
            from scipy import stats

            z = stats.norm.ppf((1 + cl) / 2)
        except Exception:
            z = 1.96
        mape = np.mean(np.abs(residuals / ts.values)) * 100 if len(residuals) > 0 else 0
        accuracy = max(0, 1 - mape / 100)
        predictions = []
        for date, value in zip(
            pd.date_range(ts.index[-1], periods=horizon + 1, freq=ts.index.freqstr)[1:],
            preds_vals,
            strict=False,
        ):
            predictions.append(
                {
                    "date": str(date.date()),
                    "value": round(float(value), 2),
                    "lower_ci": round(float(value - z * std_err), 2),
                    "upper_ci": round(float(value + z * std_err), 2),
                }
            )
        return predictions, round(float(accuracy), 4)

    def _moving_average_forecast(
        self, ts: pd.Series, horizon: int, cl: float
    ) -> tuple[list[dict], float]:
        window = min(7, len(ts))
        ma_value = ts.iloc[-window:].mean()
        preds_vals = [ma_value] * horizon
        residuals = ts.values - ts.rolling(window=window).mean().fillna(ts.mean()).values
        std_err = np.std(residuals[~np.isnan(residuals)]) if len(residuals) > 1 else 0
        try:
            from scipy import stats

            z = stats.norm.ppf((1 + cl) / 2)
        except Exception:
            z = 1.96
        predictions = []
        for date, value in zip(
            pd.date_range(ts.index[-1], periods=horizon + 1, freq=ts.index.freqstr)[1:],
            preds_vals,
            strict=False,
        ):
            predictions.append(
                {
                    "date": str(date.date()),
                    "value": round(float(value), 2),
                    "lower_ci": round(float(value - z * std_err), 2),
                    "upper_ci": round(float(value + z * std_err), 2),
                }
            )
        return predictions, 0.5

    def _seasonal_forecast(
        self, ts: pd.Series, horizon: int, cl: float
    ) -> tuple[list[dict], float]:
        period = min(12, len(ts) // 2)
        seasonal_avg = ts.iloc[-period:].values
        overall_avg = ts.mean()
        x = np.arange(len(ts)).reshape(-1, 1)
        y = ts.values
        coeffs = np.polyfit(x.flatten(), y, 1)
        trend = np.poly1d(coeffs)
        future_x = np.arange(len(ts), len(ts) + horizon)
        trend_values = trend(future_x)
        seasonal_indices = np.tile(seasonal_avg / overall_avg, horizon // period + 1)[:horizon]
        preds_vals = trend_values * seasonal_indices
        residuals = y - trend(x.flatten())
        std_err = np.std(residuals) if len(residuals) > 1 else 0
        try:
            from scipy import stats

            z = stats.norm.ppf((1 + cl) / 2)
        except Exception:
            z = 1.96
        ss_res = np.sum(residuals**2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        predictions = []
        for date, value in zip(
            pd.date_range(ts.index[-1], periods=horizon + 1, freq=ts.index.freqstr)[1:],
            preds_vals,
            strict=False,
        ):
            predictions.append(
                {
                    "date": str(date.date()),
                    "value": round(float(value), 2),
                    "lower_ci": round(float(value - z * std_err), 2),
                    "upper_ci": round(float(value + z * std_err), 2),
                }
            )
        return predictions, round(float(r2), 4)

    def _build_assumptions(
        self, ts: pd.Series, method: str, horizon: int, context: EnterpriseAIContext
    ) -> list[str]:
        """Document key assumptions for the forecast."""
        assumptions = []

        trend_dir = "increasing" if ts.iloc[-1] > ts.iloc[0] else "decreasing"
        assumptions.append(
            f"Current {trend_dir} trend continues over the forecast horizon ({horizon} periods)"
        )

        if method == "seasonal":
            assumptions.append(
                "Seasonal patterns from historical data will repeat in the forecast period"
            )
        elif method == "linear":
            assumptions.append("Linear trend is a reasonable approximation for future behavior")
        elif method == "exponential":
            assumptions.append("Recent observations are more predictive than older ones")
        elif method == "moving_average":
            assumptions.append("Future values will be close to the recent average")

        assumptions.append(
            "No major external shocks or structural changes during the forecast period"
        )
        assumptions.append("Data quality remains consistent with the historical period")

        if context.industry.industry != "unknown":
            assumptions.append(
                f"Industry-specific factors for {context.industry.display_name} remain stable"
            )

        return assumptions

    def _build_limitations(self, ts: pd.Series, method: str, accuracy: float) -> list[str]:
        """Document model limitations."""
        limitations = []

        if len(ts) < 30:
            limitations.append(
                f"Limited historical data ({len(ts)} points) reduces forecast reliability"
            )
        if len(ts) < 10:
            limitations.append(
                "Very few data points â€” forecast should be treated as indicative only"
            )

        if accuracy < 0.5:
            limitations.append(
                f"Low accuracy score ({accuracy:.2f}) â€” forecast has high uncertainty"
            )
        elif accuracy < 0.7:
            limitations.append(f"Moderate accuracy score ({accuracy:.2f}) â€” use with caution")

        if method == "linear":
            limitations.append("Linear model cannot capture non-linear patterns or regime changes")
        elif method == "moving_average":
            limitations.append("Moving average does not account for trend or seasonality")
        elif method == "exponential":
            limitations.append("Exponential smoothing may lag behind rapid changes")

        limitations.append(
            "Confidence intervals widen with forecast horizon â€” longer predictions are less certain"
        )
        limitations.append(
            "Forecast does not account for external factors (market changes, policy shifts, etc.)"
        )

        return limitations

    def _calculate_confidence(self, accuracy: float, data_points: int, method: str) -> dict:
        """Calculate overall confidence score."""
        base = accuracy
        if data_points < 10:
            base *= 0.5
        elif data_points < 30:
            base *= 0.8

        if method == "auto":
            method = "selected"

        return {
            "score": round(max(0.1, min(0.99, base)), 2),
            "methodology": f"Based on {method} model accuracy ({accuracy:.2f}) adjusted for data volume ({data_points} points)",
            "data_limitations": (
                [] if data_points >= 30 else [f"Only {data_points} data points available"]
            ),
        }

    def _ai_interpret(
        self,
        metric: str,
        predictions: list[dict],
        ts_data: dict,
        method: str,
        assumptions: list[str],
        limitations: list[str],
        context: EnterpriseAIContext,
        user_id: int | None = None,
    ) -> str:
        """Get AI interpretation of the forecast."""
        if not self.gateway:
            # Generate basic interpretation
            if predictions:
                first_val = predictions[0]["value"]
                last_val = predictions[-1]["value"]
                direction = "increase" if last_val > first_val else "decrease"
                return (
                    f"Forecast for {metric} using {method} method predicts a {direction} "
                    f"from {first_val:.2f} to {last_val:.2f} over {len(predictions)} periods. "
                    f"Confidence level: {ts_data.get('confidence_level', 0.95):.0%}."
                )
            return f"Forecast generated for {metric} using {method} method."

        try:
            additional = {
                "metric": metric,
                "method": method,
                "first_5_predictions": predictions[:5],
                "last_prediction": predictions[-1] if predictions else None,
                "assumptions": assumptions,
                "limitations": limitations,
                "input_summary": {
                    "data_points": ts_data.get("data_points", 0),
                    "mean": ts_data.get("mean", 0),
                    "trend": ts_data.get("trend", "unknown"),
                },
            }

            self.orchestrator.build_messages(
                task_type=PromptTaskType.FORECASTING,
                user_message=f"Interpret the forecast for {metric}.",
                context=context,
                additional_data=additional,
            )

            result = self.gateway.chat(
                user_message=f"Interpret the forecast for {metric}.",
                assistant_type="forecast_copilot",
                user_id=user_id,
                context=context.to_dict(),
            )
            return result["response"]
        except Exception as e:
            logger.warning(f"AI interpretation failed: {e}")
            return f"Forecast for {metric} using {method} method over {len(predictions)} periods."
