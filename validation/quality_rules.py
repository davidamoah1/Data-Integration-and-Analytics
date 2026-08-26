"""Data Quality Rules Engine â€” detects missing values, duplicates, invalid formats."""

from __future__ import annotations

import re
from dataclasses import dataclass

import pandas as pd


@dataclass
class QualityFinding:
    rule_name: str
    category: str
    severity: str  # error, warning, info
    column: str | None
    affected_rows: int
    message: str
    suggested_fix: str | None = None
    business_impact: str | None = None


EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
PHONE_PATTERN = re.compile(r"^[\d\s\+\-\(\)]{7,20}$")
ICD10_PATTERN = re.compile(r"^[A-Z]\d{2}(\.[A-Z0-9]{1,4})?$")
CPT_PATTERN = re.compile(r"^\d{5}$")


class QualityRulesEngine:
    """Runs data quality checks on a DataFrame."""

    @staticmethod
    def run(df: pd.DataFrame) -> list[QualityFinding]:
        findings: list[QualityFinding] = []

        findings.extend(QualityRulesEngine._check_missing_values(df))
        findings.extend(QualityRulesEngine._check_blank_fields(df))
        findings.extend(QualityRulesEngine._check_duplicate_rows(df))
        findings.extend(QualityRulesEngine._check_duplicate_ids(df))
        findings.extend(QualityRulesEngine._check_empty_columns(df))
        findings.extend(QualityRulesEngine._check_high_null_columns(df))
        findings.extend(QualityRulesEngine._check_invalid_emails(df))
        findings.extend(QualityRulesEngine._check_invalid_phones(df))
        findings.extend(QualityRulesEngine._check_invalid_genders(df))
        findings.extend(QualityRulesEngine._check_invalid_diagnosis_codes(df))
        findings.extend(QualityRulesEngine._check_negative_values(df))
        findings.extend(QualityRulesEngine._check_constant_columns(df))

        return findings

    @staticmethod
    def _check_missing_values(df: pd.DataFrame) -> list[QualityFinding]:
        findings = []
        for col in df.columns:
            null_count = int(df[col].isnull().sum())
            if null_count > 0:
                pct = null_count / max(len(df), 1) * 100
                severity = "error" if pct > 50 else ("warning" if pct > 10 else "info")
                findings.append(
                    QualityFinding(
                        rule_name="missing_values",
                        category="completeness",
                        severity=severity,
                        column=col,
                        affected_rows=null_count,
                        message=f"Column '{col}' has {null_count} missing values ({pct:.1f}%).",
                        suggested_fix=f"Fill or remove missing values in '{col}'.",
                        business_impact="Missing data can lead to incorrect analytics and incomplete records.",
                    )
                )
        return findings

    @staticmethod
    def _check_blank_fields(df: pd.DataFrame) -> list[QualityFinding]:
        findings = []
        for col in df.columns:
            if df[col].dtype == "object":
                blank_count = int((df[col].astype(str).str.strip() == "").sum())
                if blank_count > 0:
                    findings.append(
                        QualityFinding(
                            rule_name="blank_fields",
                            category="completeness",
                            severity="warning",
                            column=col,
                            affected_rows=blank_count,
                            message=f"Column '{col}' has {blank_count} blank (empty string) values.",
                            suggested_fix=f"Replace blank strings with null or meaningful values in '{col}'.",
                        )
                    )
        return findings

    @staticmethod
    def _check_duplicate_rows(df: pd.DataFrame) -> list[QualityFinding]:
        findings = []
        dup_count = int(df.duplicated().sum())
        if dup_count > 0:
            findings.append(
                QualityFinding(
                    rule_name="duplicate_rows",
                    category="uniqueness",
                    severity="warning",
                    column=None,
                    affected_rows=dup_count,
                    message=f"{dup_count} duplicate rows found.",
                    suggested_fix="Remove duplicate rows or investigate data entry process.",
                    business_impact="Duplicate records inflate counts and skew analytics.",
                )
            )
        return findings

    @staticmethod
    def _check_duplicate_ids(df: pd.DataFrame) -> list[QualityFinding]:
        findings = []
        id_cols = [c for c in df.columns if "id" in c.lower() and "patient" in c.lower()]
        id_cols += [
            c
            for c in df.columns
            if c.lower() in ("patient_id", "visit_id", "admission_id", "lab_id", "lab_result_id")
        ]
        id_cols += [
            c
            for c in df.columns
            if "visit_id" in c.lower() or "admission_id" in c.lower() or "lab_id" in c.lower()
        ]

        seen = set()
        for col in id_cols:
            if col in seen:
                continue
            seen.add(col)
            if col not in df.columns:
                continue
            dup_count = int(df[col].duplicated(keep=False).sum())
            if dup_count > 0:
                findings.append(
                    QualityFinding(
                        rule_name="duplicate_ids",
                        category="uniqueness",
                        severity="error",
                        column=col,
                        affected_rows=dup_count,
                        message=f"Column '{col}' has {dup_count} duplicate ID values.",
                        suggested_fix=f"Ensure '{col}' values are unique. Investigate data entry.",
                        business_impact="Duplicate IDs can cause record conflicts and incorrect patient matching.",
                    )
                )
        return findings

    @staticmethod
    def _check_empty_columns(df: pd.DataFrame) -> list[QualityFinding]:
        findings = []
        for col in df.columns:
            if df[col].isnull().all():
                findings.append(
                    QualityFinding(
                        rule_name="empty_column",
                        category="completeness",
                        severity="error",
                        column=col,
                        affected_rows=len(df),
                        message=f"Column '{col}' is entirely empty.",
                        suggested_fix=f"Populate '{col}' or remove it from the dataset.",
                    )
                )
        return findings

    @staticmethod
    def _check_high_null_columns(df: pd.DataFrame) -> list[QualityFinding]:
        findings = []
        for col in df.columns:
            null_pct = df[col].isnull().sum() / max(len(df), 1)
            if 0.5 < null_pct < 1.0:
                findings.append(
                    QualityFinding(
                        rule_name="high_null_percentage",
                        category="completeness",
                        severity="warning",
                        column=col,
                        affected_rows=int(df[col].isnull().sum()),
                        message=f"Column '{col}' has {null_pct*100:.1f}% null values.",
                        suggested_fix=f"Consider whether '{col}' is needed or improve data capture.",
                    )
                )
        return findings

    @staticmethod
    def _check_invalid_emails(df: pd.DataFrame) -> list[QualityFinding]:
        findings = []
        email_cols = [c for c in df.columns if "email" in c.lower()]
        for col in email_cols:
            if col not in df.columns:
                continue
            non_null = df[col].dropna().astype(str)
            if len(non_null) == 0:
                continue
            invalid = ~non_null.str.match(EMAIL_PATTERN)
            invalid_count = int(invalid.sum())
            if invalid_count > 0:
                findings.append(
                    QualityFinding(
                        rule_name="invalid_emails",
                        category="validity",
                        severity="warning",
                        column=col,
                        affected_rows=invalid_count,
                        message=f"Column '{col}': {invalid_count} invalid email addresses.",
                        suggested_fix="Correct email format to user@domain.com.",
                    )
                )
        return findings

    @staticmethod
    def _check_invalid_phones(df: pd.DataFrame) -> list[QualityFinding]:
        findings = []
        phone_cols = [
            c
            for c in df.columns
            if "phone" in c.lower() or "mobile" in c.lower() or "tel" in c.lower()
        ]
        for col in phone_cols:
            if col not in df.columns:
                continue
            non_null = df[col].dropna().astype(str)
            if len(non_null) == 0:
                continue
            invalid = ~non_null.str.match(PHONE_PATTERN)
            invalid_count = int(invalid.sum())
            if invalid_count > 0:
                findings.append(
                    QualityFinding(
                        rule_name="invalid_phone_numbers",
                        category="validity",
                        severity="info",
                        column=col,
                        affected_rows=invalid_count,
                        message=f"Column '{col}': {invalid_count} invalid phone numbers.",
                        suggested_fix="Ensure phone numbers contain only digits, spaces, +, -, and parentheses.",
                    )
                )
        return findings

    @staticmethod
    def _check_invalid_genders(df: pd.DataFrame) -> list[QualityFinding]:
        findings = []
        gender_cols = [c for c in df.columns if "gender" in c.lower() or "sex" in c.lower()]
        valid_values = {
            "m",
            "f",
            "male",
            "female",
            "other",
            "unknown",
            "u",
            "o",
            "non-binary",
            "nonbinary",
        }
        for col in gender_cols:
            if col not in df.columns:
                continue
            non_null = df[col].dropna().astype(str).str.strip().str.lower()
            if len(non_null) == 0:
                continue
            invalid = ~non_null.isin(valid_values)
            invalid_count = int(invalid.sum())
            if invalid_count > 0:
                findings.append(
                    QualityFinding(
                        rule_name="invalid_gender_values",
                        category="validity",
                        severity="warning",
                        column=col,
                        affected_rows=invalid_count,
                        message=f"Column '{col}': {invalid_count} invalid gender values.",
                        suggested_fix="Use standard values: Male, Female, Other, or Unknown.",
                    )
                )
        return findings

    @staticmethod
    def _check_invalid_diagnosis_codes(df: pd.DataFrame) -> list[QualityFinding]:
        findings = []
        diag_cols = [c for c in df.columns if "diagnosis" in c.lower() and "code" in c.lower()]
        diag_cols += [
            c for c in df.columns if c.lower() in ("diagnosis_code", "icd_code", "icd10_code")
        ]
        for col in diag_cols:
            if col not in df.columns:
                continue
            non_null = df[col].dropna().astype(str).str.strip().str.upper()
            if len(non_null) == 0:
                continue
            invalid = ~non_null.str.match(ICD10_PATTERN)
            invalid_count = int(invalid.sum())
            if invalid_count > 0:
                findings.append(
                    QualityFinding(
                        rule_name="invalid_diagnosis_codes",
                        category="validity",
                        severity="warning",
                        column=col,
                        affected_rows=invalid_count,
                        message=f"Column '{col}': {invalid_count} values don't match ICD-10 format.",
                        suggested_fix="Use ICD-10 format (e.g., E11.9, J45.909).",
                    )
                )
        return findings

    @staticmethod
    def _check_negative_values(df: pd.DataFrame) -> list[QualityFinding]:
        findings = []
        skip_cols = {"id"}
        for col in df.columns:
            if not pd.api.types.is_numeric_dtype(df[col]):
                continue
            col_lower = col.lower()
            if any(kw in col_lower for kw in skip_cols):
                continue
            neg_count = int((df[col] < 0).sum())
            if neg_count > 0:
                findings.append(
                    QualityFinding(
                        rule_name="negative_values",
                        category="validity",
                        severity="warning",
                        column=col,
                        affected_rows=neg_count,
                        message=f"Column '{col}': {neg_count} negative values found.",
                        suggested_fix=f"Check if negative values in '{col}' are valid. Remove or correct if not.",
                    )
                )
        return findings

    @staticmethod
    def _check_constant_columns(df: pd.DataFrame) -> list[QualityFinding]:
        findings = []
        for col in df.columns:
            if df[col].nunique() == 1 and not df[col].isnull().all():
                findings.append(
                    QualityFinding(
                        rule_name="constant_column",
                        category="consistency",
                        severity="info",
                        column=col,
                        affected_rows=0,
                        message=f"Column '{col}' has only one unique value: '{df[col].iloc[0]}'.",
                        suggested_fix=f"Consider removing '{col}' if it provides no analytical value.",
                    )
                )
        return findings
