"""Healthcare Intelligence — Patient analytics, disease trends, doctor performance, revenue.

Specialized analytics for hospitals, clinics, and healthcare facilities:
  - Patient demographics and volume
  - Disease/diagnosis trend analysis
  - Doctor performance and workload
  - Revenue and billing analysis
  - Department efficiency
"""

from __future__ import annotations

import pandas as pd

from industry_intelligence.base import (
    AnalyticsResult,
    Breakdown,
    IndustryAnalytics,
    IndustryAnalyticsRegistry,
    Insight,
    Trend,
)


class HealthcareAnalytics(IndustryAnalytics):
    industry = "healthcare"

    @classmethod
    def analyze(cls, df: pd.DataFrame, col_mapping: dict | None = None) -> AnalyticsResult:
        col_mapping = col_mapping or {}
        insights: list[Insight] = []
        breakdowns: list[Breakdown] = []
        trends: list[Trend] = []
        recommendations: list[str] = []
        alerts: list[str] = []

        # Find columns
        patient_col = cls._find_col(df, col_mapping, ["patient"])
        doctor_col = cls._find_col(df, col_mapping, ["doctor"])
        diagnosis_col = cls._find_col(df, col_mapping, ["diagnosis"])
        dept_col = cls._find_col(df, col_mapping, ["ward", "department"])
        billing_col = cls._find_numeric_col(df, col_mapping, ["billing", "revenue"])
        date_col = cls._find_date_col(df, col_mapping)
        insurance_col = cls._find_col(df, col_mapping, ["insurance"])
        admission_col = cls._find_col(df, col_mapping, ["admission", "appointment"])
        gender_col = cls._find_col(df, col_mapping, ["gender"])

        # ── Patient Analytics ────────────────────────────
        if patient_col and patient_col in df.columns:
            patient_count = int(df[patient_col].nunique())
            insights.append(Insight(
                title="Total Patients",
                value=patient_count,
                formatted=cls._fmt_number(patient_count),
                category="operational",
                description=f"Unique patients identified by column '{patient_col}'.",
            ))

            # Gender breakdown
            if gender_col and gender_col in df.columns:
                gender_bd = cls._compute_breakdown(df, gender_col, patient_col, "count")
                if gender_bd:
                    gender_bd.dimension = "Gender"
                    breakdowns.append(gender_bd)

        # Visits/admissions
        if admission_col and admission_col in df.columns:
            visit_count = int(df[admission_col].nunique())
            insights.append(Insight(
                title="Total Admissions",
                value=visit_count,
                formatted=cls._fmt_number(visit_count),
                category="operational",
                description=f"Unique admissions/appointments recorded.",
            ))

            if patient_col and patient_col in df.columns and patient_count > 0:
                visits_per_patient = len(df) / patient_count
                insights.append(Insight(
                    title="Visits per Patient",
                    value=visits_per_patient,
                    formatted=f"{visits_per_patient:.1f}",
                    category="operational",
                    description="Average number of visits per patient.",
                    alert="warning" if visits_per_patient > 5 else "ok",
                ))

        # ── Disease Trends ───────────────────────────────
        if diagnosis_col and diagnosis_col in df.columns:
            diag_count = int(df[diagnosis_col].nunique())
            insights.append(Insight(
                title="Unique Diagnoses",
                value=diag_count,
                formatted=cls._fmt_number(diag_count),
                category="clinical",
                description=f"Distinct diagnosis codes/types recorded.",
            ))

            # Top diagnoses
            diag_bd = cls._compute_breakdown(df, diagnosis_col, diagnosis_col, "count")
            if diag_bd:
                diag_bd.dimension = "Diagnosis"
                diag_bd.metric = "patient_count"
                breakdowns.append(diag_bd)

            # Disease trend over time
            if date_col:
                trend = cls._compute_trend(df, date_col, diagnosis_col, "count")
                if trend:
                    trend.metric = "diagnoses"
                    trends.append(trend)

        # ── Doctor Performance ───────────────────────────
        if doctor_col and doctor_col in df.columns:
            doctor_count = int(df[doctor_col].nunique())
            insights.append(Insight(
                title="Active Doctors",
                value=doctor_count,
                formatted=cls._fmt_number(doctor_count),
                category="operational",
                description=f"Unique doctors providing care.",
            ))

            # Doctor workload (patients per doctor)
            if patient_col and patient_col in df.columns and doctor_count > 0:
                doc_bd = cls._compute_breakdown(df, doctor_col, patient_col, "count")
                if doc_bd:
                    doc_bd.dimension = "Doctor"
                    doc_bd.metric = "patients"
                    breakdowns.append(doc_bd)

                    avg_patients = sum(doc_bd.values.values()) / len(doc_bd.values)
                    insights.append(Insight(
                        title="Avg Patients per Doctor",
                        value=avg_patients,
                        formatted=cls._fmt_number(avg_patients),
                        category="operational",
                        description="Average patient load across all doctors.",
                        alert="warning" if avg_patients > 50 else "ok",
                    ))

        # ── Revenue / Billing ────────────────────────────
        if billing_col and billing_col in df.columns:
            total_billing = float(df[billing_col].sum())
            insights.append(Insight(
                title="Total Billing",
                value=total_billing,
                formatted=cls._fmt_currency(total_billing),
                category="financial",
                description="Total billing amount across all records.",
            ))

            if patient_col and patient_col in df.columns:
                patient_count = max(int(df[patient_col].nunique()), 1)
                avg_bill = total_billing / patient_count
                insights.append(Insight(
                    title="Avg Bill per Patient",
                    value=avg_bill,
                    formatted=cls._fmt_currency(avg_bill),
                    category="financial",
                    description="Average billing amount per unique patient.",
                ))

            # Billing by department
            if dept_col and dept_col in df.columns:
                dept_bd = cls._compute_breakdown(df, dept_col, billing_col, "sum")
                if dept_bd:
                    dept_bd.dimension = "Department"
                    breakdowns.append(dept_bd)

            # Revenue trend
            if date_col:
                rev_trend = cls._compute_trend(df, date_col, billing_col, "sum")
                if rev_trend:
                    rev_trend.metric = "billing"
                    trends.append(rev_trend)

        # ── Department Efficiency ────────────────────────
        if dept_col and dept_col in df.columns:
            dept_count = int(df[dept_col].nunique())
            insights.append(Insight(
                title="Active Departments",
                value=dept_count,
                formatted=cls._fmt_number(dept_count),
                category="operational",
                description="Number of distinct departments/wards.",
            ))

            if patient_col and patient_col in df.columns:
                dept_patient_bd = cls._compute_breakdown(df, dept_col, patient_col, "count")
                if dept_patient_bd:
                    dept_patient_bd.dimension = "Department"
                    dept_patient_bd.metric = "patients"
                    breakdowns.append(dept_patient_bd)

        # ── Insurance Coverage ───────────────────────────
        if insurance_col and insurance_col in df.columns:
            ins_bd = cls._compute_breakdown(df, insurance_col, insurance_col, "count")
            if ins_bd:
                ins_bd.dimension = "Insurance"
                ins_bd.metric = "claims"
                breakdowns.append(ins_bd)

        # ── Recommendations ──────────────────────────────
        recommendations.extend([
            "Monitor patient volume by department to optimize staffing.",
            "Track readmission rates to identify quality-of-care issues.",
            "Analyze billing patterns by insurance provider for revenue optimization.",
            "Review doctor workload distribution for burnout prevention.",
        ])

        # ── Alerts ───────────────────────────────────────
        for insight in insights:
            if insight.alert == "warning":
                alerts.append(f"{insight.title}: {insight.formatted} — above normal threshold.")

        return AnalyticsResult(
            industry="healthcare",
            insights=insights,
            breakdowns=breakdowns,
            trends=trends,
            recommendations=recommendations,
            alerts=alerts,
        )


IndustryAnalyticsRegistry.register("healthcare", HealthcareAnalytics)
