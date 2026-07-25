"""Healthcare Predictive Analytics.

Admission forecasting and patient risk prediction.
"""

from __future__ import annotations

import pandas as pd

from predictive_analytics.base import (
    PredictiveAnalyticsBase,
    PredictiveAnalyticsRegistry,
    PredictiveIntelligenceResult,
)
from predictive_analytics.forecasting import TimeSeriesForecaster
from predictive_analytics.classification import RiskClassifier


class HealthcarePredictiveAnalytics(PredictiveAnalyticsBase):
    """Predictive analytics for healthcare sector."""

    def analyze(self, df: pd.DataFrame, col_mapping: dict) -> PredictiveIntelligenceResult:
        forecasts = []
        risk_assessments = []

        date_col = self._find_date_col(df, col_mapping)

        # 1. Admission/Billing Forecast
        billing_col = self._find_numeric_col(df, col_mapping, ["billing", "revenue", "amount", "cost"])
        if billing_col and date_col:
            forecast = TimeSeriesForecaster.forecast(
                df, billing_col, date_col,
                horizon=30, frequency="D",
                name="Admission Volume Forecast",
            )
            if forecast:
                forecasts.append(forecast)

        # 2. Patient count forecast (if we can count admissions per day)
        patient_col = self._find_col(df, col_mapping, ["patient", "patient_id"])
        if patient_col and date_col:
            # Count unique patients per day
            df_temp = df.copy()
            if not pd.api.types.is_datetime64_any_dtype(df_temp[date_col]):
                df_temp[date_col] = pd.to_datetime(df_temp[date_col], errors="coerce")
            df_temp = df_temp.dropna(subset=[date_col])
            if not df_temp.empty:
                daily_counts = df_temp.groupby(date_col)[patient_col].nunique().reset_index()
                daily_counts.columns = [date_col, "patient_count"]
                forecast = TimeSeriesForecaster.forecast(
                    daily_counts, "patient_count", date_col,
                    horizon=30, frequency="D",
                    name="Daily Patient Admissions Forecast",
                )
                if forecast:
                    forecasts.append(forecast)

        # 3. Patient Risk Assessment (rule-based)
        risk_factors = []
        age_col = self._find_numeric_col(df, col_mapping, ["age"])
        if age_col:
            risk_factors.append({
                "column": age_col,
                "condition": "above",
                "threshold": 65,
                "weight": 0.3,
                "label": "Age > 65",
            })

        # Check for readmission indicator (multiple visits)
        if patient_col and date_col:
            visit_counts = df.groupby(patient_col).size()
            high_visit_patients = set(visit_counts[visit_counts > 2].index)
            df["_frequent_visits"] = df[patient_col].isin(high_visit_patients).astype(int)
            risk_factors.append({
                "column": "_frequent_visits",
                "condition": "above",
                "threshold": 0,
                "weight": 0.3,
                "label": "Frequent hospital visits (>2)",
            })

        # Billing amount as risk indicator (high cost = complex case)
        if billing_col:
            median_billing = df[billing_col].median()
            risk_factors.append({
                "column": billing_col,
                "condition": "above",
                "threshold": median_billing,
                "weight": 0.2,
                "label": "Above-median billing amount",
            })

        # Diagnosis count as complexity indicator
        diagnosis_col = self._find_col(df, col_mapping, ["diagnosis", "diagnosis_code"])
        if diagnosis_col and patient_col:
            diag_counts = df.groupby(patient_col)[diagnosis_col].nunique()
            multi_diag_patients = set(diag_counts[diag_counts > 1].index)
            df["_multi_diagnosis"] = df[patient_col].isin(multi_diag_patients).astype(int)
            risk_factors.append({
                "column": "_multi_diagnosis",
                "condition": "above",
                "threshold": 0,
                "weight": 0.2,
                "label": "Multiple diagnoses",
            })

        if risk_factors and patient_col:
            risk = RiskClassifier.classify(
                df, patient_col, risk_factors,
                name="Patient Risk Assessment",
                target="patient_risk",
            )
            risk_assessments.append(risk)

        summary_parts = []
        if forecasts:
            summary_parts.append(f"{len(forecasts)} forecast(s) generated")
        if risk_assessments:
            summary_parts.append(f"{len(risk_assessments)} risk assessment(s) completed")
        summary = " | ".join(summary_parts) if summary_parts else "No predictions could be generated."

        return PredictiveIntelligenceResult(
            industry="healthcare",
            forecasts=forecasts,
            risk_assessments=risk_assessments,
            summary=summary,
        )


PredictiveAnalyticsRegistry.register("healthcare", HealthcarePredictiveAnalytics)
