"""Enterprise Anomaly Detection Engine.

Enhances the existing AnomalyDetectionEngine with:
  - Semantic-aware column detection
  - "Why" explanations for each anomaly
  - Industry-specific sensitivity
  - Historical baseline comparison
  - Impact assessment
  - Integration with EnterpriseContextEngine and PromptOrchestrator
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session as DbSession

from ai.config import AI_ANOMALY_MIN_DATA_POINTS, AI_ANOMALY_SENSITIVITY
from ai.context_engine import EnterpriseAIContext, EnterpriseContextEngine
from ai.data_gatherer import DataGatherer
from ai.gateway import AIGateway
from ai.models import AIAnomalyAlert
from ai.prompt_orchestrator import PromptOrchestrator

logger = logging.getLogger(__name__)

# Industry-specific sensitivity overrides
INDUSTRY_SENSITIVITY = {
    "healthcare": 1.5,  # More sensitive for patient safety
    "finance": 2.0,  # Standard for financial data
    "retail": 2.5,  # Less sensitive â€” sales fluctuate
    "education": 2.0,  # Standard
    "government": 1.8,  # More sensitive for public funds
    "manufacturing": 2.0,
    "logistics": 2.5,
}


class EnterpriseAnomalyEngine:
    """Semantic-aware anomaly detection with explanations."""

    def __init__(self, db: DbSession | None = None):
        self.db = db
        self.gateway = AIGateway(db) if db else None
        self.context_engine = EnterpriseContextEngine(db)
        self.orchestrator = PromptOrchestrator()

    def detect(
        self,
        metric: str,
        df: pd.DataFrame | None = None,
        semantic_mappings: dict | None = None,
        industry: str = "unknown",
        sensitivity: float | None = None,
        user_id: int | None = None,
        organization_id: int | None = None,
        context: EnterpriseAIContext | None = None,
    ) -> dict:
        """Detect anomalies in the given metric.

        Args:
            metric: The metric to analyze (e.g., 'revenue', 'billing_amount').
            df: DataFrame with the dataset.
            semantic_mappings: Semantic entity-to-column mappings.
            industry: Detected industry (affects sensitivity).
            sensitivity: Override sensitivity (std deviations). Auto from industry if None.
            user_id: User ID.

        Returns:
            Dict with alerts, total_anomalies, summary, explanations.
        """
        # Build context if not provided
        if context is None:
            context = self.context_engine.build(
                assistant_type="data_copilot",
                user_id=user_id,
                df=df,
                semantic_mappings=semantic_mappings,
                industry=industry,
            )

        # Determine sensitivity
        if sensitivity is None:
            sensitivity = INDUSTRY_SENSITIVITY.get(industry, AI_ANOMALY_SENSITIVITY)

        # Gather data
        gatherer = DataGatherer(df, context)
        anomaly_data = gatherer.gather_for_anomaly(metric)

        if anomaly_data.get("note"):
            return {
                "alerts": [],
                "total_anomalies": 0,
                "summary": anomaly_data["note"],
                "explanations": [],
            }

        # Get time series
        time_series = anomaly_data.get("time_series", [])
        values = anomaly_data.get("values", [])
        stats = anomaly_data.get("stats", {})

        if not time_series and not values:
            return {
                "alerts": [],
                "total_anomalies": 0,
                "summary": f"No data available for anomaly detection in {metric}",
                "explanations": [],
            }

        # Detect anomalies
        alerts: list[dict] = []

        if time_series:
            ts_values = np.array([d["value"] for d in time_series])
            ts_dates = [d["date"] for d in time_series]
            if len(ts_values) >= AI_ANOMALY_MIN_DATA_POINTS:
                alerts.extend(self._detect_statistical(ts_values, ts_dates, metric, sensitivity))
                alerts.extend(self._detect_trend_breaks(ts_values, ts_dates, metric, sensitivity))
                alerts.extend(self._detect_missing_records(ts_dates, metric))
        elif len(values) >= AI_ANOMALY_MIN_DATA_POINTS:
            alerts.extend(self._detect_value_anomalies(values, metric, sensitivity))

        # Generate explanations for each anomaly
        explanations = self._explain_anomalies(alerts, stats, context, metric)

        # Generate summary
        summary = self._generate_summary(alerts, metric)

        # Save to database
        if self.db:
            for alert_data in alerts:
                try:
                    alert = AIAnomalyAlert(
                        alert_type=alert_data["alert_type"],
                        severity=alert_data["severity"],
                        title=alert_data["title"],
                        description=alert_data["description"],
                        metric_name=metric,
                        expected_value=alert_data.get("expected_value"),
                        actual_value=alert_data.get("actual_value"),
                        deviation_percentage=alert_data.get("deviation_percentage"),
                        context_data=alert_data.get("context_data"),
                        user_id=user_id,
                        organization_id=organization_id,
                    )
                    self.db.add(alert)
                    self.db.commit()
                except Exception as e:
                    logger.warning(f"Failed to save alert: {e}")

        return {
            "alerts": alerts,
            "total_anomalies": len(alerts),
            "summary": summary,
            "explanations": explanations,
            "metric": metric,
            "sensitivity": sensitivity,
            "industry": industry,
            "stats": stats,
        }

    def _detect_statistical(
        self, values: np.ndarray, dates: list[str], metric: str, sensitivity: float
    ) -> list[dict]:
        """Detect statistical anomalies using z-score."""
        alerts = []
        mean = np.mean(values)
        std = np.std(values)
        if std == 0:
            return alerts

        z_scores = np.abs((values - mean) / std)
        for _i, (date, value, z) in enumerate(zip(dates, values, z_scores, strict=False)):
            if z > sensitivity:
                deviation = ((value - mean) / mean) * 100 if mean != 0 else 0
                alert_type = "spike" if value > mean else "drop"
                severity = "critical" if z > sensitivity * 2 else "warning"
                alerts.append(
                    {
                        "alert_type": alert_type,
                        "severity": severity,
                        "title": f"{alert_type.title()} detected in {metric}",
                        "description": (
                            f"Value {value:.2f} on {date} deviates {z:.1f} standard deviations "
                            f"from the mean ({mean:.2f}). This is a {alert_type} of "
                            f"{abs(deviation):.1f}% from the expected value."
                        ),
                        "metric_name": metric,
                        "expected_value": round(float(mean), 2),
                        "actual_value": round(float(value), 2),
                        "deviation_percentage": round(float(deviation), 2),
                        "context_data": {
                            "date": date,
                            "z_score": round(float(z), 2),
                            "mean": round(float(mean), 2),
                            "std": round(float(std), 2),
                        },
                        "explanation": (
                            f"The value on {date} ({value:.2f}) is {z:.1f} standard deviations "
                            f"away from the historical average of {mean:.2f}. "
                            f"This {'spike' if value > mean else 'drop'} may indicate "
                            f"an unusual event, data quality issue, or significant business change."
                        ),
                    }
                )
        return alerts

    def _detect_trend_breaks(
        self, values: np.ndarray, dates: list[str], metric: str, sensitivity: float
    ) -> list[dict]:
        """Detect trend breaks and direction changes."""
        alerts = []
        if len(values) < 5:
            return alerts

        window = min(7, len(values) // 2)
        rolling_mean = pd.Series(values).rolling(window=window).mean()

        for i in range(window, len(values) - 1):
            if pd.isna(rolling_mean.iloc[i]):
                continue
            expected = rolling_mean.iloc[i]
            actual = values[i + 1]
            if expected == 0:
                continue
            deviation = abs((actual - expected) / expected)
            if deviation > sensitivity / 10:
                severity = "warning" if deviation < 0.5 else "critical"
                alerts.append(
                    {
                        "alert_type": "trend",
                        "severity": severity,
                        "title": f"Trend anomaly in {metric}",
                        "description": (
                            f"Value {actual:.2f} on {dates[i + 1]} breaks the expected trend ({expected:.2f}). "
                            f"Deviation: {deviation * 100:.1f}%."
                        ),
                        "metric_name": metric,
                        "expected_value": round(float(expected), 2),
                        "actual_value": round(float(actual), 2),
                        "deviation_percentage": round(float(deviation * 100), 2),
                        "context_data": {
                            "date": dates[i + 1],
                            "rolling_mean": round(float(expected), 2),
                        },
                        "explanation": (
                            f"The value on {dates[i + 1]} ({actual:.2f}) significantly deviates "
                            f"from the 7-period rolling average of {expected:.2f}. "
                            f"This trend break may indicate a structural change or external event."
                        ),
                    }
                )
        return alerts[:5]

    def _detect_missing_records(self, dates: list[str], metric: str) -> list[dict]:
        """Detect gaps in time series data."""
        alerts = []
        if len(dates) < 3:
            return alerts

        try:
            date_series = pd.to_datetime(dates)
            diffs = date_series.to_series().diff()
            expected_freq = diffs.mode().iloc[0]
            if pd.isna(expected_freq):
                return alerts

            large_gaps = diffs[diffs > expected_freq * 3]
            for gap_date, gap_size in large_gaps.items():
                prev_date = gap_date - gap_size
                alerts.append(
                    {
                        "alert_type": "missing",
                        "severity": "info",
                        "title": f"Missing records in {metric}",
                        "description": f"Gap of {gap_size.days} days detected between {prev_date.date()} and {gap_date.date()}.",
                        "metric_name": metric,
                        "expected_value": None,
                        "actual_value": None,
                        "deviation_percentage": None,
                        "context_data": {
                            "gap_days": gap_size.days,
                            "from_date": str(prev_date.date()),
                            "to_date": str(gap_date.date()),
                        },
                        "explanation": (
                            f"A data gap of {gap_size.days} days was detected between "
                            f"{prev_date.date()} and {gap_date.date()}. This may indicate "
                            f"missing records, system downtime, or a data collection issue."
                        ),
                    }
                )
        except Exception:
            pass
        return alerts[:3]

    def _detect_value_anomalies(self, values: list, metric: str, sensitivity: float) -> list[dict]:
        """Detect anomalies in non-time-series values."""
        alerts = []
        arr = np.array(values)
        mean = np.mean(arr)
        std = np.std(arr)
        if std == 0:
            return alerts

        z_scores = np.abs((arr - mean) / std)
        for i, (value, z) in enumerate(zip(values, z_scores, strict=False)):
            if z > sensitivity:
                deviation = ((value - mean) / mean) * 100 if mean != 0 else 0
                alert_type = "high_outlier" if value > mean else "low_outlier"
                severity = "critical" if z > sensitivity * 2 else "warning"
                alerts.append(
                    {
                        "alert_type": alert_type,
                        "severity": severity,
                        "title": f"{alert_type.replace('_', ' ').title()} in {metric}",
                        "description": (
                            f"Value {value:.2f} (index {i}) deviates {z:.1f} standard deviations "
                            f"from the mean ({mean:.2f})."
                        ),
                        "metric_name": metric,
                        "expected_value": round(float(mean), 2),
                        "actual_value": round(float(value), 2),
                        "deviation_percentage": round(float(deviation), 2),
                        "context_data": {
                            "index": i,
                            "z_score": round(float(z), 2),
                        },
                        "explanation": (
                            f"This value ({value:.2f}) is an outlier â€” {z:.1f} standard deviations "
                            f"from the average of {mean:.2f}. It may represent a data entry error, "
                            f"an exceptional case, or a genuine anomaly worth investigating."
                        ),
                    }
                )
        return alerts

    def _explain_anomalies(
        self, alerts: list[dict], stats: dict, context: EnterpriseAIContext, metric: str
    ) -> list[dict]:
        """Generate explanations for each anomaly."""
        explanations = []
        for alert in alerts:
            explanation = alert.get("explanation", alert.get("description", ""))

            # Add industry context
            if context.industry.industry != "unknown":
                industry_name = context.industry.display_name or context.industry.industry
                explanation += f" In the {industry_name} industry, this type of anomaly may warrant immediate investigation."

            # Add impact assessment
            if alert.get("deviation_percentage"):
                deviation = abs(alert["deviation_percentage"])
                if deviation > 50:
                    impact = "high"
                elif deviation > 25:
                    impact = "medium"
                else:
                    impact = "low"
                explanation += f" Estimated impact: {impact}."

            explanations.append(
                {
                    "alert_type": alert["alert_type"],
                    "title": alert["title"],
                    "explanation": explanation,
                    "impact": impact if alert.get("deviation_percentage") else "unknown",
                }
            )

        return explanations

    def _generate_summary(self, alerts: list[dict], metric: str) -> str:
        """Generate a summary of detected anomalies."""
        if not alerts:
            return f"No anomalies detected in {metric}."

        spikes = sum(1 for a in alerts if a["alert_type"] == "spike")
        drops = sum(1 for a in alerts if a["alert_type"] == "drop")
        trends = sum(1 for a in alerts if a["alert_type"] == "trend")
        missing = sum(1 for a in alerts if a["alert_type"] == "missing")
        outliers = sum(1 for a in alerts if "outlier" in a["alert_type"])
        critical = sum(1 for a in alerts if a["severity"] == "critical")

        parts = [f"Detected {len(alerts)} anomalies in {metric}."]
        if spikes:
            parts.append(f"{spikes} spike(s)")
        if drops:
            parts.append(f"{drops} drop(s)")
        if trends:
            parts.append(f"{trends} trend anomaly(ies)")
        if missing:
            parts.append(f"{missing} missing record gap(s)")
        if outliers:
            parts.append(f"{outliers} outlier(s)")
        if critical:
            parts.append(f"{critical} critical alert(s)")

        return " ".join(parts)
