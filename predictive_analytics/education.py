"""Education Predictive Analytics.

Student risk prediction using rule-based classification.
Identifies students at risk of failing or dropping out based on:
  - Low grades/scores
  - High absenteeism
  - Declining performance
"""

from __future__ import annotations

import pandas as pd

from predictive_analytics.base import (
    PredictiveAnalyticsBase,
    PredictiveAnalyticsRegistry,
    PredictiveIntelligenceResult,
)
from predictive_analytics.classification import RiskClassifier
from predictive_analytics.forecasting import TimeSeriesForecaster


class EducationPredictiveAnalytics(PredictiveAnalyticsBase):
    """Predictive analytics for education sector."""

    def analyze(self, df: pd.DataFrame, col_mapping: dict) -> PredictiveIntelligenceResult:
        forecasts = []
        risk_assessments = []

        date_col = self._find_date_col(df, col_mapping)
        student_col = self._find_col(df, col_mapping, ["student", "student_id", "enrollment"])

        # 1. Enrollment/Attendance Forecast
        attendance_col = self._find_numeric_col(
            df, col_mapping, ["attendance", "attendance_rate", "enrollment"]
        )
        if attendance_col and date_col:
            forecast = TimeSeriesForecaster.forecast(
                df,
                attendance_col,
                date_col,
                horizon=30,
                frequency="D",
                name="Attendance Trend Forecast",
            )
            if forecast:
                forecasts.append(forecast)

        # 2. Student Risk Prediction
        risk_factors = []

        # Low grade/score
        grade_col = self._find_numeric_col(
            df, col_mapping, ["grade", "score", "gpa", "mark", "result"]
        )
        if grade_col:
            median_grade = df[grade_col].median()
            risk_factors.append(
                {
                    "column": grade_col,
                    "condition": "below",
                    "threshold": median_grade,
                    "weight": 0.35,
                    "label": f"Below-median grade (<{median_grade:.1f})",
                }
            )

        # Low attendance rate
        if attendance_col:
            risk_factors.append(
                {
                    "column": attendance_col,
                    "condition": "below",
                    "threshold": 80,
                    "weight": 0.30,
                    "label": "Low attendance (<80%)",
                }
            )

        # High absenteeism (if absences column exists)
        absence_col = self._find_numeric_col(
            df, col_mapping, ["absence", "absent", "absenteeism", "days_absent"]
        )
        if absence_col:
            risk_factors.append(
                {
                    "column": absence_col,
                    "condition": "above",
                    "threshold": 10,
                    "weight": 0.20,
                    "label": "High absenteeism (>10 days)",
                }
            )

        # Low participation or engagement
        participation_col = self._find_numeric_col(
            df, col_mapping, ["participation", "engagement", "activity"]
        )
        if participation_col:
            risk_factors.append(
                {
                    "column": participation_col,
                    "condition": "below",
                    "threshold": 50,
                    "weight": 0.15,
                    "label": "Low participation (<50%)",
                }
            )

        if risk_factors and student_col:
            risk = RiskClassifier.classify(
                df,
                student_col,
                risk_factors,
                name="Student Risk Prediction",
                target="student_risk",
                high_threshold=0.5,
                medium_threshold=0.25,
            )
            risk_assessments.append(risk)

        summary_parts = []
        if forecasts:
            summary_parts.append(f"{len(forecasts)} forecast(s) generated")
        if risk_assessments:
            ra = risk_assessments[0]
            summary_parts.append(
                f"{ra.high_risk_count} high-risk, {ra.medium_risk_count} medium-risk students identified"
            )
        summary = (
            " | ".join(summary_parts) if summary_parts else "No predictions could be generated."
        )

        return PredictiveIntelligenceResult(
            industry="education",
            forecasts=forecasts,
            risk_assessments=risk_assessments,
            summary=summary,
        )


PredictiveAnalyticsRegistry.register("education", EducationPredictiveAnalytics)
