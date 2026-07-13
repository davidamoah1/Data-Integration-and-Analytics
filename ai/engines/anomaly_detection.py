"""AI Anomaly Detection Engine — detects unexpected patterns in data.

Detects:
- Unexpected spikes
- Sudden drops
- Fraud indicators
- Abnormal trends
- Missing records

Generates alerts with severity, expected vs actual values, and deviation.
"""

import json
from datetime import datetime
import numpy as np
import pandas as pd
from typing import Optional
from sqlalchemy.orm import Session as DbSession

from ai.gateway import AIGateway
from ai.models import AIAnomalyAlert
from ai.config import AI_ANOMALY_SENSITIVITY, AI_ANOMALY_MIN_DATA_POINTS
from etl.connectors.connectors import get_connector


class AnomalyDetectionEngine:
    """Detects anomalies in time series and tabular data."""

    def __init__(self, db: DbSession):
        self.db = db
        self.gateway = AIGateway(db)

    def detect(self, source_type: str, source_config: dict,
               metric_column: str, date_column: str,
               sensitivity: float = AI_ANOMALY_SENSITIVITY,
               user_id: Optional[int] = None) -> dict:
        """Detect anomalies in the given data.

        Returns:
            Dict with alerts, total_anomalies, summary.
        """
        # Extract data
        connector = get_connector(source_type, source_config)
        with connector:
            df = connector.extract()

        # Prepare time series
        if date_column not in df.columns or metric_column not in df.columns:
            return {"alerts": [], "total_anomalies": 0, "summary": "Invalid columns specified"}

        df[date_column] = pd.to_datetime(df[date_column], errors="coerce")
        df = df.dropna(subset=[date_column, metric_column]).sort_values(date_column)

        if len(df) < AI_ANOMALY_MIN_DATA_POINTS:
            return {"alerts": [], "total_anomalies": 0,
                    "summary": f"Insufficient data. Need at least {AI_ANOMALY_MIN_DATA_POINTS} data points."}

        # Aggregate by date
        ts = df.groupby(date_column)[metric_column].sum()

        alerts = []

        # 1. Statistical anomaly detection (z-score based)
        alerts.extend(self._detect_statistical_anomalies(
            ts, metric_column, sensitivity, user_id
        ))

        # 2. Trend anomaly detection
        alerts.extend(self._detect_trend_anomalies(
            ts, metric_column, sensitivity, user_id
        ))

        # 3. Missing records detection
        alerts.extend(self._detect_missing_records(
            ts, metric_column, user_id
        ))

        # Generate summary
        summary = self._generate_summary(alerts, metric_column)

        # Save alerts to database
        for alert_data in alerts:
            alert = AIAnomalyAlert(
                alert_type=alert_data["alert_type"],
                severity=alert_data["severity"],
                title=alert_data["title"],
                description=alert_data["description"],
                metric_name=metric_column,
                expected_value=alert_data.get("expected_value"),
                actual_value=alert_data.get("actual_value"),
                deviation_percentage=alert_data.get("deviation_percentage"),
                context_data=alert_data.get("context_data"),
                user_id=user_id,
            )
            self.db.add(alert)
        self.db.commit()

        return {
            "alerts": alerts,
            "total_anomalies": len(alerts),
            "summary": summary,
        }

    def _detect_statistical_anomalies(self, ts: pd.Series, metric: str,
                                      sensitivity: float, user_id: int) -> list[dict]:
        """Detect anomalies using z-score method."""
        alerts = []
        values = ts.values
        mean = np.mean(values)
        std = np.std(values)

        if std == 0:
            return alerts

        z_scores = np.abs((values - mean) / std)

        for i, (date, value, z) in enumerate(zip(ts.index, values, z_scores)):
            if z > sensitivity:
                deviation = ((value - mean) / mean) * 100 if mean != 0 else 0
                alert_type = "spike" if value > mean else "drop"
                severity = "critical" if z > sensitivity * 2 else "warning"

                alerts.append({
                    "alert_type": alert_type,
                    "severity": severity,
                    "title": f"{alert_type.title()} detected in {metric}",
                    "description": f"Value {value:.2f} on {date.date()} deviates {z:.1f} standard deviations from the mean ({mean:.2f}).",
                    "metric_name": metric,
                    "expected_value": round(float(mean), 2),
                    "actual_value": round(float(value), 2),
                    "deviation_percentage": round(float(deviation), 2),
                    "context_data": {"date": str(date.date()), "z_score": round(float(z), 2)},
                })

        return alerts

    def _detect_trend_anomalies(self, ts: pd.Series, metric: str,
                                sensitivity: float, user_id: int) -> list[dict]:
        """Detect trend breaks and direction changes."""
        alerts = []
        if len(ts) < 5:
            return alerts

        # Calculate rolling average
        window = min(7, len(ts) // 2)
        rolling_mean = ts.rolling(window=window).mean()

        # Detect sudden direction changes
        for i in range(window, len(ts) - 1):
            if pd.isna(rolling_mean.iloc[i]):
                continue

            expected = rolling_mean.iloc[i]
            actual = ts.iloc[i + 1]

            if expected == 0:
                continue

            deviation = abs((actual - expected) / expected)

            if deviation > sensitivity / 10:  # Scale sensitivity for trend
                alert_type = "trend"
                severity = "warning" if deviation < 0.5 else "critical"

                alerts.append({
                    "alert_type": alert_type,
                    "severity": severity,
                    "title": f"Trend anomaly in {metric}",
                    "description": f"Value {actual:.2f} on {ts.index[i + 1].date()} breaks the expected trend ({expected:.2f}).",
                    "metric_name": metric,
                    "expected_value": round(float(expected), 2),
                    "actual_value": round(float(actual), 2),
                    "deviation_percentage": round(float(deviation * 100), 2),
                    "context_data": {
                        "date": str(ts.index[i + 1].date()),
                        "rolling_mean": round(float(expected), 2),
                    },
                })

        return alerts[:5]  # Limit trend alerts

    def _detect_missing_records(self, ts: pd.Series, metric: str,
                                user_id: int) -> list[dict]:
        """Detect missing records (gaps in time series)."""
        alerts = []
        if len(ts) < 2:
            return alerts

        # Check for gaps in dates
        expected_freq = ts.index.to_series().diff().mode().iloc[0] if len(ts) > 2 else None
        if expected_freq is None or pd.isna(expected_freq):
            return alerts

        gaps = ts.index.to_series().diff()
        large_gaps = gaps[gaps > expected_freq * 3]

        for gap_date, gap_size in large_gaps.items():
            prev_date = gap_date - gap_size
            alerts.append({
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
            })

        return alerts[:3]  # Limit missing record alerts

    def _generate_summary(self, alerts: list[dict], metric: str) -> str:
        """Generate a summary of detected anomalies."""
        if not alerts:
            return f"No anomalies detected in {metric}."

        spikes = sum(1 for a in alerts if a["alert_type"] == "spike")
        drops = sum(1 for a in alerts if a["alert_type"] == "drop")
        trends = sum(1 for a in alerts if a["alert_type"] == "trend")
        missing = sum(1 for a in alerts if a["alert_type"] == "missing")
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
        if critical:
            parts.append(f"{critical} critical alert(s)")

        return " ".join(parts)

    def get_alerts(self, is_resolved: Optional[bool] = False,
                   limit: int = 50) -> list[dict]:
        """Get anomaly alerts."""
        query = self.db.query(AIAnomalyAlert).filter(
            AIAnomalyAlert.is_resolved == is_resolved
        )
        alerts = query.order_by(AIAnomalyAlert.created_at.desc()).limit(limit).all()
        return [
            {
                "id": a.id,
                "alert_type": a.alert_type,
                "severity": a.severity,
                "title": a.title,
                "description": a.description,
                "metric_name": a.metric_name,
                "expected_value": a.expected_value,
                "actual_value": a.actual_value,
                "deviation_percentage": a.deviation_percentage,
                "is_resolved": a.is_resolved,
                "created_at": str(a.created_at) if a.created_at else None,
            }
            for a in alerts
        ]

    def resolve_alert(self, alert_id: int, user_id: int) -> bool:
        """Mark an alert as resolved."""
        alert = self.db.query(AIAnomalyAlert).filter(AIAnomalyAlert.id == alert_id).first()
        if not alert:
            return False
        alert.is_resolved = True
        alert.resolved_by = user_id
        alert.resolved_at = datetime.utcnow()
        self.db.commit()
        return True
