"""Clinical Validation Engine â€” checks clinical consistency, vital signs, and clinical outliers."""

from __future__ import annotations

import pandas as pd

from validation.business_rules import BusinessRuleFinding


class ClinicalValidationEngine:
    """Validates clinical consistency in hospital data."""

    @staticmethod
    def run(df: pd.DataFrame) -> list[BusinessRuleFinding]:
        findings: list[BusinessRuleFinding] = []

        findings.extend(ClinicalValidationEngine._check_bp_ranges(df))
        findings.extend(ClinicalValidationEngine._check_temperature_ranges(df))
        findings.extend(ClinicalValidationEngine._check_pulse_ranges(df))
        findings.extend(ClinicalValidationEngine._check_bmi(df))
        findings.extend(ClinicalValidationEngine._check_extreme_ages(df))
        findings.extend(ClinicalValidationEngine._check_impossible_lab_values(df))
        findings.extend(ClinicalValidationEngine._check_abnormal_billing(df))

        return findings

    @staticmethod
    def _find_col(df: pd.DataFrame, keywords: list[str]) -> str | None:
        for col in df.columns:
            col_lower = col.lower()
            if any(kw in col_lower for kw in keywords):
                return col
        return None

    @staticmethod
    def _check_bp_ranges(df: pd.DataFrame) -> list[BusinessRuleFinding]:
        findings = []
        systolic_col = ClinicalValidationEngine._find_col(
            df, ["systolic", "bp_systolic", "systolic_bp"]
        )
        diastolic_col = ClinicalValidationEngine._find_col(
            df, ["diastolic", "bp_diastolic", "diastolic_bp"]
        )

        for col, label, lo, hi in [
            (systolic_col, "systolic", 50, 300),
            (diastolic_col, "diastolic", 20, 200),
        ]:
            if not col or col not in df.columns:
                continue
            if not pd.api.types.is_numeric_dtype(df[col]):
                continue
            out_of_range = (df[col] < lo) | (df[col] > hi)
            count = int(out_of_range.sum())
            if count > 0:
                findings.append(
                    BusinessRuleFinding(
                        rule_name=f"bp_{label}_range",
                        category="clinical",
                        severity="warning",
                        column=col,
                        affected_rows=count,
                        message=f"Column '{col}': {count} {label} BP values outside range {lo}-{hi} mmHg.",
                        suggested_fix=f"Review {label} BP values outside physiological range.",
                        business_impact="Abnormal BP values may indicate data entry errors or critical patients.",
                    )
                )

        if (
            systolic_col
            and diastolic_col
            and systolic_col in df.columns
            and diastolic_col in df.columns
        ):
            if pd.api.types.is_numeric_dtype(df[systolic_col]) and pd.api.types.is_numeric_dtype(
                df[diastolic_col]
            ):
                invalid = df[systolic_col] <= df[diastolic_col]
                count = int((invalid & df[systolic_col].notna() & df[diastolic_col].notna()).sum())
                if count > 0:
                    findings.append(
                        BusinessRuleFinding(
                            rule_name="bp_systolic_gt_diastolic",
                            category="clinical",
                            severity="error",
                            column=f"{systolic_col} / {diastolic_col}",
                            affected_rows=count,
                            message=f"{count} records where systolic BP <= diastolic BP.",
                            suggested_fix="Correct blood pressure readings.",
                            business_impact="Systolic must exceed diastolic for valid BP.",
                        )
                    )
        return findings

    @staticmethod
    def _check_temperature_ranges(df: pd.DataFrame) -> list[BusinessRuleFinding]:
        findings = []
        col = ClinicalValidationEngine._find_col(df, ["temperature", "temp", "body_temp"])
        if not col or col not in df.columns:
            return findings
        if not pd.api.types.is_numeric_dtype(df[col]):
            return findings
        # Detect unit: if median > 50, assume Fahrenheit, else Celsius
        median_val = df[col].median()
        if pd.isna(median_val):
            return findings
        if median_val > 50:
            lo, hi, unit = 80, 115, "F"
        else:
            lo, hi, unit = 30, 45, "C"
        out_of_range = (df[col] < lo) | (df[col] > hi)
        count = int(out_of_range.sum())
        if count > 0:
            findings.append(
                BusinessRuleFinding(
                    rule_name="temperature_range",
                    category="clinical",
                    severity="warning",
                    column=col,
                    affected_rows=count,
                    message=f"Column '{col}': {count} temperature values outside range {lo}-{hi} {unit}.",
                    suggested_fix=f"Review temperature values outside physiological range ({unit}).",
                    business_impact="Abnormal temperatures may indicate data entry errors or critical patients.",
                )
            )
        return findings

    @staticmethod
    def _check_pulse_ranges(df: pd.DataFrame) -> list[BusinessRuleFinding]:
        findings = []
        col = ClinicalValidationEngine._find_col(df, ["pulse", "heart_rate", "hr"])
        if not col or col not in df.columns:
            return findings
        if not pd.api.types.is_numeric_dtype(df[col]):
            return findings
        out_of_range = (df[col] < 20) | (df[col] > 250)
        count = int(out_of_range.sum())
        if count > 0:
            findings.append(
                BusinessRuleFinding(
                    rule_name="pulse_range",
                    category="clinical",
                    severity="warning",
                    column=col,
                    affected_rows=count,
                    message=f"Column '{col}': {count} pulse values outside range 20-250 bpm.",
                    suggested_fix="Review pulse values outside physiological range.",
                    business_impact="Abnormal pulse may indicate data entry errors or critical patients.",
                )
            )
        return findings

    @staticmethod
    def _check_bmi(df: pd.DataFrame) -> list[BusinessRuleFinding]:
        findings = []
        bmi_col = ClinicalValidationEngine._find_col(df, ["bmi"])
        weight_col = ClinicalValidationEngine._find_col(df, ["weight"])
        height_col = ClinicalValidationEngine._find_col(df, ["height"])

        if bmi_col and bmi_col in df.columns and pd.api.types.is_numeric_dtype(df[bmi_col]):
            out_of_range = (df[bmi_col] < 5) | (df[bmi_col] > 80)
            count = int(out_of_range.sum())
            if count > 0:
                findings.append(
                    BusinessRuleFinding(
                        rule_name="bmi_range",
                        category="clinical",
                        severity="warning",
                        column=bmi_col,
                        affected_rows=count,
                        message=f"Column '{bmi_col}': {count} BMI values outside range 5-80.",
                        suggested_fix="Review BMI values outside normal range.",
                        business_impact="Abnormal BMI values may indicate data entry errors.",
                    )
                )

        if weight_col and height_col and weight_col in df.columns and height_col in df.columns:
            if pd.api.types.is_numeric_dtype(df[weight_col]) and pd.api.types.is_numeric_dtype(
                df[height_col]
            ):
                w = df[weight_col]
                h = df[height_col]
                # If height in cm, convert to m
                h_meters = h / 100 if h.median() > 10 else h
                h_meters = h_meters.replace(0, pd.NA)
                computed_bmi = w / (h_meters**2)
                if bmi_col and bmi_col in df.columns and pd.api.types.is_numeric_dtype(df[bmi_col]):
                    diff = (df[bmi_col] - computed_bmi).abs()
                    mismatch = diff > 2
                    count = int(mismatch.sum())
                    if count > 0:
                        findings.append(
                            BusinessRuleFinding(
                                rule_name="bmi_consistency",
                                category="clinical",
                                severity="info",
                                column=bmi_col,
                                affected_rows=count,
                                message=f"{count} BMI values don't match weight/height calculation (diff > 2).",
                                suggested_fix="Recalculate BMI from weight and height.",
                            )
                        )
        return findings

    @staticmethod
    def _check_extreme_ages(df: pd.DataFrame) -> list[BusinessRuleFinding]:
        findings = []
        col = ClinicalValidationEngine._find_col(df, ["age"])
        if not col or col not in df.columns:
            return findings
        if not pd.api.types.is_numeric_dtype(df[col]):
            return findings
        extreme = (df[col] > 120) | (df[col] < 0)
        count = int(extreme.sum())
        if count > 0:
            findings.append(
                BusinessRuleFinding(
                    rule_name="extreme_ages",
                    category="clinical",
                    severity="error",
                    column=col,
                    affected_rows=count,
                    message=f"{count} extreme age values (<0 or >120).",
                    suggested_fix="Review and correct extreme age values.",
                    business_impact="Extreme ages are likely data entry errors.",
                )
            )
        return findings

    @staticmethod
    def _check_impossible_lab_values(df: pd.DataFrame) -> list[BusinessRuleFinding]:
        findings = []
        # Glucose: 0-1000 mg/dL
        glucose_col = ClinicalValidationEngine._find_col(
            df, ["glucose", "blood_sugar", "blood_glucose"]
        )
        if (
            glucose_col
            and glucose_col in df.columns
            and pd.api.types.is_numeric_dtype(df[glucose_col])
        ):
            impossible = (df[glucose_col] < 0) | (df[glucose_col] > 2000)
            count = int(impossible.sum())
            if count > 0:
                findings.append(
                    BusinessRuleFinding(
                        rule_name="impossible_glucose",
                        category="clinical",
                        severity="error",
                        column=glucose_col,
                        affected_rows=count,
                        message=f"{count} impossible glucose values (<0 or >2000 mg/dL).",
                        suggested_fix="Review and correct glucose values.",
                    )
                )

        # Hemoglobin: 0-25 g/dL
        hgb_col = ClinicalValidationEngine._find_col(df, ["hemoglobin", "haemoglobin", "hgb"])
        if hgb_col and hgb_col in df.columns and pd.api.types.is_numeric_dtype(df[hgb_col]):
            impossible = (df[hgb_col] < 0) | (df[hgb_col] > 30)
            count = int(impossible.sum())
            if count > 0:
                findings.append(
                    BusinessRuleFinding(
                        rule_name="impossible_hemoglobin",
                        category="clinical",
                        severity="error",
                        column=hgb_col,
                        affected_rows=count,
                        message=f"{count} impossible hemoglobin values (<0 or >30 g/dL).",
                        suggested_fix="Review and correct hemoglobin values.",
                    )
                )
        return findings

    @staticmethod
    def _check_abnormal_billing(df: pd.DataFrame) -> list[BusinessRuleFinding]:
        findings = []
        # Find billing/amount column, excluding date columns
        billing_col = None
        for c in df.columns:
            c_lower = c.lower()
            if any(kw in c_lower for kw in ["discharge", "date", "timestamp"]):
                continue
            if any(kw in c_lower for kw in ["amount", "billing", "charge", "cost", "bill"]):
                billing_col = c
                break
        if not billing_col or billing_col not in df.columns:
            return findings
        if not pd.api.types.is_numeric_dtype(df[billing_col]):
            return findings
        # Flag negative and extremely high values
        negative = df[billing_col] < 0
        neg_count = int(negative.sum())
        if neg_count > 0:
            findings.append(
                BusinessRuleFinding(
                    rule_name="negative_billing",
                    category="clinical",
                    severity="error",
                    column=billing_col,
                    affected_rows=neg_count,
                    message=f"{neg_count} negative billing amounts.",
                    suggested_fix="Remove or correct negative billing values.",
                )
            )

        # Statistical outliers (> 10x median)
        median_val = df[billing_col].median()
        if pd.notna(median_val) and median_val > 0:
            extreme = df[billing_col] > median_val * 10
            extreme_count = int(extreme.sum())
            if extreme_count > 0:
                findings.append(
                    BusinessRuleFinding(
                        rule_name="abnormal_billing_outlier",
                        category="clinical",
                        severity="warning",
                        column=billing_col,
                        affected_rows=extreme_count,
                        message=f"{extreme_count} billing amounts >10x median (${median_val:,.0f}).",
                        suggested_fix="Review extreme billing amounts for accuracy.",
                        business_impact="Abnormal billing may indicate data entry errors or fraud.",
                    )
                )
        return findings
