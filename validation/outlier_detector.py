"""Outlier Detector — detects statistical anomalies and impossible values."""

from __future__ import annotations

import pandas as pd

from validation.business_rules import BusinessRuleFinding


class OutlierDetector:
    """Detects outliers using IQR, z-score, and domain-specific rules."""

    @staticmethod
    def run(df: pd.DataFrame) -> list[BusinessRuleFinding]:
        findings: list[BusinessRuleFinding] = []

        findings.extend(OutlierDetector._detect_iqr_outliers(df))
        findings.extend(OutlierDetector._detect_duplicate_admissions(df))
        findings.extend(OutlierDetector._detect_impossible_dates(df))
        findings.extend(OutlierDetector._detect_duplicate_claims(df))

        return findings

    @staticmethod
    def _detect_iqr_outliers(df: pd.DataFrame) -> list[BusinessRuleFinding]:
        findings = []
        numeric_cols = [
            c for c in df.columns if pd.api.types.is_numeric_dtype(df[c]) and "id" not in c.lower()
        ]
        for col in numeric_cols:
            data = df[col].dropna()
            if len(data) < 10:
                continue
            q1 = data.quantile(0.25)
            q3 = data.quantile(0.75)
            iqr = q3 - q1
            if iqr == 0:
                continue
            lower = q1 - 3 * iqr
            upper = q3 + 3 * iqr
            outliers = (df[col] < lower) | (df[col] > upper)
            count = int(outliers.sum())
            if count > 0:
                findings.append(
                    BusinessRuleFinding(
                        rule_name="iqr_outlier",
                        category="outlier",
                        severity="info",
                        column=col,
                        affected_rows=count,
                        message=f"Column '{col}': {count} statistical outliers (IQR method, 3x IQR).",
                        suggested_fix=f"Review outliers in '{col}' — values outside [{lower:.2f}, {upper:.2f}].",
                        business_impact="Outliers may indicate data entry errors or genuine extreme cases.",
                    )
                )
        return findings

    @staticmethod
    def _detect_duplicate_admissions(df: pd.DataFrame) -> list[BusinessRuleFinding]:
        findings = []
        patient_col = None
        for c in df.columns:
            if "patient_id" in c.lower():
                patient_col = c
                break
        adm_col = None
        for c in df.columns:
            if "admission_date" in c.lower() or "admit_date" in c.lower():
                adm_col = c
                break
        if not patient_col or not adm_col:
            return findings
        if patient_col not in df.columns or adm_col not in df.columns:
            return findings
        try:
            adm_dates = pd.to_datetime(df[adm_col], errors="coerce")
        except Exception:
            return findings
        combined = df[patient_col].astype(str) + "|" + adm_dates.dt.strftime("%Y-%m-%d")
        dup_mask = combined.duplicated(keep=False)
        count = int(dup_mask.sum())
        if count > 0:
            findings.append(
                BusinessRuleFinding(
                    rule_name="duplicate_admissions",
                    category="outlier",
                    severity="warning",
                    column=f"{patient_col} / {adm_col}",
                    affected_rows=count,
                    message=f"{count} duplicate admissions (same patient, same admission date).",
                    suggested_fix="Review duplicate admissions — may be readmissions or data entry errors.",
                    business_impact="Duplicate admissions inflate admission counts.",
                )
            )
        return findings

    @staticmethod
    def _detect_impossible_dates(df: pd.DataFrame) -> list[BusinessRuleFinding]:
        findings = []
        date_cols = [
            c for c in df.columns if any(kw in c.lower() for kw in ["date", "dob", "timestamp"])
        ]
        today = pd.Timestamp.now()
        for col in date_cols:
            if col not in df.columns:
                continue
            try:
                dates = pd.to_datetime(df[col], errors="coerce")
            except Exception:
                continue
            future = dates > today
            future_count = int(future.sum())
            if future_count > 0:
                findings.append(
                    BusinessRuleFinding(
                        rule_name="future_dates",
                        category="outlier",
                        severity="error",
                        column=col,
                        affected_rows=future_count,
                        message=f"Column '{col}': {future_count} dates in the future.",
                        suggested_fix="Correct future dates to valid past or present dates.",
                    )
                )

            far_past = dates < pd.Timestamp("1900-01-01")
            past_count = int(far_past.sum())
            if past_count > 0:
                findings.append(
                    BusinessRuleFinding(
                        rule_name="impossible_past_dates",
                        category="outlier",
                        severity="warning",
                        column=col,
                        affected_rows=past_count,
                        message=f"Column '{col}': {past_count} dates before 1900.",
                        suggested_fix="Review dates before 1900 — likely data entry errors.",
                    )
                )
        return findings

    @staticmethod
    def _detect_duplicate_claims(df: pd.DataFrame) -> list[BusinessRuleFinding]:
        findings = []
        claim_col = None
        for c in df.columns:
            if "claim" in c.lower() and "id" in c.lower():
                claim_col = c
                break
        if not claim_col or claim_col not in df.columns:
            return findings
        dup_mask = df[claim_col].duplicated(keep=False)
        count = int(dup_mask.sum())
        if count > 0:
            findings.append(
                BusinessRuleFinding(
                    rule_name="duplicate_claims",
                    category="outlier",
                    severity="error",
                    column=claim_col,
                    affected_rows=count,
                    message=f"{count} duplicate insurance claim IDs.",
                    suggested_fix="Ensure claim IDs are unique.",
                    business_impact="Duplicate claims may indicate fraud or billing errors.",
                )
            )
        return findings
