"""Quality Check Engine — automated data quality checks.

Detects:
  - Missing values (nulls, blanks, empty strings)
  - Duplicate rows and duplicate IDs
  - Sentinel/placeholder values (999, -1, "N/A", "UNKNOWN")
  - Out-of-range numeric values
  - Invalid format values (emails, phones, dates, codes)
  - Type mismatches (mixed types within a column)
  - Constant columns (no variance)
  - High-cardinality warnings (too many unique values)
  - Mixed-case inconsistencies
"""

from __future__ import annotations

import contextlib
import re
from dataclasses import dataclass, field
from enum import Enum

import pandas as pd


class Severity(Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    CRITICAL = "critical"


@dataclass
class QualityFinding:
    """A single data quality finding."""

    check_name: str
    category: str
    severity: Severity
    column: str | None
    affected_rows: int
    affected_pct: float
    message: str
    suggested_fix: str = ""
    business_impact: str = ""
    sample_values: list = field(default_factory=list)

    @property
    def severity_value(self) -> str:
        return self.severity.value

    def to_dict(self) -> dict:
        return {
            "check_name": self.check_name,
            "category": self.category,
            "severity": self.severity.value,
            "column": self.column,
            "affected_rows": self.affected_rows,
            "affected_pct": round(self.affected_pct, 2),
            "message": self.message,
            "suggested_fix": self.suggested_fix,
            "business_impact": self.business_impact,
            "sample_values": self.sample_values[:5],
        }


# Common sentinel/placeholder values that indicate missing data
SENTINEL_VALUES_NUMERIC = {999, 9999, -1, -999, -9999, 999.99, -999.99, 0}
SENTINEL_VALUES_TEXT = {
    "n/a",
    "na",
    "n/a ",
    "n.a.",
    "n.a",
    "null",
    "none",
    "nil",
    "unknown",
    "unk",
    "unkn",
    "missing",
    "not applicable",
    "tbd",
    "tba",
    "pending",
    "unspecified",
    "default",
    "test",
    "dummy",
    "placeholder",
    "temp",
    "temporary",
    "-",
    "--",
    "---",
    "?",
    "??",
    "???",
}

# Regex patterns for format validation
EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
PHONE_PATTERN = re.compile(r"^[\d\s\+\-\(\)]{7,20}$")
ICD10_PATTERN = re.compile(r"^[A-Z]\d{2}(\.[A-Z0-9]{1,4})?$")
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class QualityCheckEngine:
    """Runs automated data quality checks on a DataFrame."""

    @staticmethod
    def run(df: pd.DataFrame, col_mapping: dict[str, str] | None = None) -> list[QualityFinding]:
        """Run all quality checks and return findings sorted by severity.

        Args:
            df: DataFrame to check.
            col_mapping: Optional column-to-entity mapping for context.

        Returns:
            List of QualityFinding objects, sorted by severity (critical > error > warning > info).
        """
        col_mapping = col_mapping or {}
        findings: list[QualityFinding] = []

        findings.extend(QualityCheckEngine._check_missing_values(df))
        findings.extend(QualityCheckEngine._check_blank_fields(df))
        findings.extend(QualityCheckEngine._check_duplicate_rows(df))
        findings.extend(QualityCheckEngine._check_duplicate_ids(df))
        findings.extend(QualityCheckEngine._check_empty_columns(df))
        findings.extend(QualityCheckEngine._check_high_null_columns(df))
        findings.extend(QualityCheckEngine._check_sentinel_values(df))
        findings.extend(QualityCheckEngine._check_out_of_range(df))
        findings.extend(QualityCheckEngine._check_invalid_formats(df))
        findings.extend(QualityCheckEngine._check_type_mismatches(df))
        findings.extend(QualityCheckEngine._check_constant_columns(df))
        findings.extend(QualityCheckEngine._check_negative_values(df))
        findings.extend(QualityCheckEngine._check_mixed_case(df))
        findings.extend(QualityCheckEngine._check_invalid_dates(df))
        findings.extend(QualityCheckEngine._check_invalid_numeric(df))

        # Sort by severity
        severity_order = {
            Severity.CRITICAL: 0,
            Severity.ERROR: 1,
            Severity.WARNING: 2,
            Severity.INFO: 3,
        }
        findings.sort(key=lambda f: severity_order.get(f.severity, 99))

        return findings

    # ── Completeness Checks ──────────────────────────────

    @staticmethod
    def _check_missing_values(df: pd.DataFrame) -> list[QualityFinding]:
        findings = []
        total_rows = max(len(df), 1)
        for col in df.columns:
            null_count = int(df[col].isnull().sum())
            if null_count > 0:
                pct = null_count / total_rows * 100
                severity = (
                    Severity.CRITICAL
                    if pct > 50
                    else (Severity.ERROR if pct > 20 else Severity.WARNING)
                )
                findings.append(
                    QualityFinding(
                        check_name="missing_values",
                        category="completeness",
                        severity=severity,
                        column=col,
                        affected_rows=null_count,
                        affected_pct=pct,
                        message=f"Column '{col}' has {null_count} missing values ({pct:.1f}%).",
                        suggested_fix=f"Fill or remove missing values in '{col}'. Consider imputation for small gaps.",
                        business_impact="Missing data leads to incomplete analytics and biased results.",
                    )
                )
        return findings

    @staticmethod
    def _check_blank_fields(df: pd.DataFrame) -> list[QualityFinding]:
        findings = []
        total_rows = max(len(df), 1)
        for col in df.columns:
            if df[col].dtype == "object":
                blank_count = int((df[col].astype(str).str.strip() == "").sum())
                if blank_count > 0:
                    pct = blank_count / total_rows * 100
                    findings.append(
                        QualityFinding(
                            check_name="blank_fields",
                            category="completeness",
                            severity=Severity.WARNING,
                            column=col,
                            affected_rows=blank_count,
                            affected_pct=pct,
                            message=f"Column '{col}' has {blank_count} blank (empty string) values.",
                            suggested_fix=f"Replace blank strings with null or meaningful values in '{col}'.",
                            business_impact="Blank strings may be treated differently from nulls, causing inconsistency.",
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
                        check_name="empty_column",
                        category="completeness",
                        severity=Severity.ERROR,
                        column=col,
                        affected_rows=len(df),
                        affected_pct=100.0,
                        message=f"Column '{col}' is entirely empty.",
                        suggested_fix=f"Populate '{col}' or remove it from the dataset.",
                        business_impact="Empty columns waste storage and confuse analysis tools.",
                    )
                )
        return findings

    @staticmethod
    def _check_high_null_columns(df: pd.DataFrame) -> list[QualityFinding]:
        findings = []
        total_rows = max(len(df), 1)
        for col in df.columns:
            null_pct = df[col].isnull().sum() / total_rows
            if 0.5 < null_pct < 1.0:
                findings.append(
                    QualityFinding(
                        check_name="high_null_percentage",
                        category="completeness",
                        severity=Severity.WARNING,
                        column=col,
                        affected_rows=int(df[col].isnull().sum()),
                        affected_pct=null_pct * 100,
                        message=f"Column '{col}' has {null_pct*100:.1f}% null values.",
                        suggested_fix=f"Consider whether '{col}' is needed or improve data capture processes.",
                        business_impact="Columns with >50% nulls provide limited analytical value.",
                    )
                )
        return findings

    # ── Uniqueness Checks ────────────────────────────────

    @staticmethod
    def _check_duplicate_rows(df: pd.DataFrame) -> list[QualityFinding]:
        findings = []
        total_rows = max(len(df), 1)
        dup_count = int(df.duplicated().sum())
        if dup_count > 0:
            pct = dup_count / total_rows * 100
            severity = Severity.ERROR if pct > 10 else Severity.WARNING
            findings.append(
                QualityFinding(
                    check_name="duplicate_rows",
                    category="uniqueness",
                    severity=severity,
                    column=None,
                    affected_rows=dup_count,
                    affected_pct=pct,
                    message=f"{dup_count} duplicate rows found ({pct:.1f}%).",
                    suggested_fix="Remove duplicate rows or investigate data entry process.",
                    business_impact="Duplicate records inflate counts and skew analytics.",
                )
            )
        return findings

    @staticmethod
    def _check_duplicate_ids(df: pd.DataFrame) -> list[QualityFinding]:
        findings = []
        total_rows = max(len(df), 1)
        id_cols = [c for c in df.columns if "id" in c.lower() and df[c].nunique() < total_rows]
        for col in id_cols:
            if col not in df.columns:
                continue
            dup_count = int(df[col].duplicated(keep=False).sum())
            if dup_count > 0:
                pct = dup_count / total_rows * 100
                findings.append(
                    QualityFinding(
                        check_name="duplicate_ids",
                        category="uniqueness",
                        severity=Severity.ERROR,
                        column=col,
                        affected_rows=dup_count,
                        affected_pct=pct,
                        message=f"Column '{col}' has {dup_count} duplicate ID values.",
                        suggested_fix=f"Ensure '{col}' values are unique. Investigate data entry process.",
                        business_impact="Duplicate IDs cause record conflicts and incorrect joins.",
                    )
                )
        return findings

    # ── Validity Checks ──────────────────────────────────

    @staticmethod
    def _check_sentinel_values(df: pd.DataFrame) -> list[QualityFinding]:
        """Detect sentinel/placeholder values like 999 in Age, -1 in Revenue."""
        findings = []
        total_rows = max(len(df), 1)

        for col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                series = df[col].dropna()
                for sentinel in SENTINEL_VALUES_NUMERIC:
                    if sentinel == 0:
                        # Only flag 0 for columns that shouldn't have zero
                        col_lower = col.lower()
                        if any(
                            kw in col_lower
                            for kw in (
                                "age",
                                "price",
                                "amount",
                                "revenue",
                                "billing",
                                "cost",
                                "salary",
                            )
                        ):
                            count = int((series == 0).sum())
                            if count > 0:
                                pct = count / total_rows * 100
                                findings.append(
                                    QualityFinding(
                                        check_name="sentinel_value",
                                        category="validity",
                                        severity=Severity.WARNING,
                                        column=col,
                                        affected_rows=count,
                                        affected_pct=pct,
                                        message=f"Column '{col}' contains {count} zero values — possible placeholder for missing data.",
                                        suggested_fix=f"Verify if 0 in '{col}' is a valid value or should be treated as missing.",
                                        business_impact="Sentinel values like 0 can skew averages and totals.",
                                        sample_values=[0],
                                    )
                                )
                    else:
                        count = int((series == sentinel).sum())
                        if count > 0:
                            pct = count / total_rows * 100
                            severity = Severity.WARNING if pct < 10 else Severity.ERROR
                            findings.append(
                                QualityFinding(
                                    check_name="sentinel_value",
                                    category="validity",
                                    severity=severity,
                                    column=col,
                                    affected_rows=count,
                                    affected_pct=pct,
                                    message=f"Column '{col}' contains {count} sentinel value(s) of {sentinel} — likely placeholder for missing data.",
                                    suggested_fix=f"Replace {sentinel} in '{col}' with null or the actual missing value representation.",
                                    business_impact=f"Sentinel value {sentinel} can skew statistics and is often mistaken for real data.",
                                    sample_values=[sentinel],
                                )
                            )

            elif df[col].dtype == "object":
                series = df[col].dropna().astype(str).str.strip().str.lower()
                for sentinel in SENTINEL_VALUES_TEXT:
                    count = int((series == sentinel).sum())
                    if count > 0:
                        pct = count / total_rows * 100
                        findings.append(
                            QualityFinding(
                                check_name="sentinel_value",
                                category="validity",
                                severity=Severity.WARNING,
                                column=col,
                                affected_rows=count,
                                affected_pct=pct,
                                message=f"Column '{col}' contains {count} placeholder value(s) '{sentinel}' — likely indicates missing data.",
                                suggested_fix=f"Replace '{sentinel}' in '{col}' with null or a proper value.",
                                business_impact="Placeholder text values are often missed by null checks and can skew category counts.",
                                sample_values=[sentinel],
                            )
                        )

        return findings

    @staticmethod
    def _check_out_of_range(df: pd.DataFrame) -> list[QualityFinding]:
        """Detect values outside plausible ranges for known column types."""
        findings = []
        total_rows = max(len(df), 1)

        range_rules = {
            "age": (0, 120),
            "temperature": (-50, 60),
            "humidity": (0, 100),
            "percentage": (0, 100),
            "attendance_rate": (0, 100),
            "yield_rate": (0, 100),
            "grade": (0, 100),
            "gpa": (0, 4),
            "heart_rate": (30, 250),
            "blood_pressure_systolic": (60, 300),
            "blood_pressure_diastolic": (30, 200),
            "bmi": (10, 80),
        }

        for col in df.columns:
            if not pd.api.types.is_numeric_dtype(df[col]):
                continue
            col_lower = col.lower().replace(" ", "_")
            for pattern, (lo, hi) in range_rules.items():
                if pattern in col_lower:
                    series = df[col].dropna()
                    out_of_range = series[(series < lo) | (series > hi)]
                    count = len(out_of_range)
                    if count > 0:
                        pct = count / total_rows * 100
                        findings.append(
                            QualityFinding(
                                check_name="out_of_range",
                                category="validity",
                                severity=Severity.WARNING,
                                column=col,
                                affected_rows=count,
                                affected_pct=pct,
                                message=f"Column '{col}' has {count} values outside expected range [{lo}, {hi}].",
                                suggested_fix=f"Review and correct values in '{col}' that fall outside [{lo}, {hi}].",
                                business_impact="Out-of-range values indicate data entry errors or sensor malfunctions.",
                                sample_values=[float(v) for v in out_of_range.head(5).tolist()],
                            )
                        )
                    break

        return findings

    @staticmethod
    def _check_invalid_formats(df: pd.DataFrame) -> list[QualityFinding]:
        """Detect invalid format values (emails, phones, diagnosis codes)."""
        findings = []
        total_rows = max(len(df), 1)

        # Emails
        email_cols = [c for c in df.columns if "email" in c.lower()]
        for col in email_cols:
            non_null = df[col].dropna().astype(str)
            if len(non_null) == 0:
                continue
            invalid = ~non_null.str.match(EMAIL_PATTERN)
            count = int(invalid.sum())
            if count > 0:
                findings.append(
                    QualityFinding(
                        check_name="invalid_emails",
                        category="validity",
                        severity=Severity.WARNING,
                        column=col,
                        affected_rows=count,
                        affected_pct=count / total_rows * 100,
                        message=f"Column '{col}': {count} invalid email addresses.",
                        suggested_fix="Correct email format to user@domain.com.",
                        business_impact="Invalid emails cause communication failures.",
                        sample_values=non_null[invalid].head(5).tolist(),
                    )
                )

        # Phones
        phone_cols = [
            c for c in df.columns if any(kw in c.lower() for kw in ("phone", "mobile", "tel"))
        ]
        for col in phone_cols:
            non_null = df[col].dropna().astype(str)
            if len(non_null) == 0:
                continue
            invalid = ~non_null.str.match(PHONE_PATTERN)
            count = int(invalid.sum())
            if count > 0:
                findings.append(
                    QualityFinding(
                        check_name="invalid_phones",
                        category="validity",
                        severity=Severity.INFO,
                        column=col,
                        affected_rows=count,
                        affected_pct=count / total_rows * 100,
                        message=f"Column '{col}': {count} invalid phone numbers.",
                        suggested_fix="Ensure phone numbers contain only digits, spaces, +, -, and parentheses.",
                        sample_values=non_null[invalid].head(5).tolist(),
                    )
                )

        # Diagnosis codes (ICD-10)
        diag_cols = [c for c in df.columns if "diagnosis" in c.lower() and "code" in c.lower()]
        for col in diag_cols:
            non_null = df[col].dropna().astype(str).str.strip().str.upper()
            if len(non_null) == 0:
                continue
            invalid = ~non_null.str.match(ICD10_PATTERN)
            count = int(invalid.sum())
            if count > 0:
                findings.append(
                    QualityFinding(
                        check_name="invalid_diagnosis_codes",
                        category="validity",
                        severity=Severity.WARNING,
                        column=col,
                        affected_rows=count,
                        affected_pct=count / total_rows * 100,
                        message=f"Column '{col}': {count} values don't match ICD-10 format.",
                        suggested_fix="Use ICD-10 format (e.g., E11.9, J45.909).",
                        sample_values=non_null[invalid].head(5).tolist(),
                    )
                )

        return findings

    @staticmethod
    def _check_type_mismatches(df: pd.DataFrame) -> list[QualityFinding]:
        """Detect columns with mixed data types (e.g., numbers stored as text)."""
        findings = []
        max(len(df), 1)

        for col in df.columns:
            if df[col].dtype == "object":
                non_null = df[col].dropna()
                if len(non_null) == 0:
                    continue

                # Check if column has mixed types
                types = non_null.apply(type).nunique()
                if types > 1:
                    findings.append(
                        QualityFinding(
                            check_name="type_mismatch",
                            category="consistency",
                            severity=Severity.WARNING,
                            column=col,
                            affected_rows=len(non_null),
                            affected_pct=100.0,
                            message=f"Column '{col}' contains mixed data types ({types} different types).",
                            suggested_fix=f"Standardize '{col}' to a single data type.",
                            business_impact="Mixed types cause parsing errors and incorrect aggregations.",
                        )
                    )

                # Check if numeric values are stored as strings
                numeric_count = sum(1 for v in non_null if isinstance(v, (int, float)))
                if numeric_count > 0 and numeric_count < len(non_null):
                    # Partially numeric
                    pass  # Already caught by mixed types above

        return findings

    @staticmethod
    def _check_constant_columns(df: pd.DataFrame) -> list[QualityFinding]:
        """Detect columns with only one unique value (no variance)."""
        findings = []
        for col in df.columns:
            if df[col].nunique() == 1 and not df[col].isnull().all():
                value = df[col].iloc[0]
                findings.append(
                    QualityFinding(
                        check_name="constant_column",
                        category="consistency",
                        severity=Severity.INFO,
                        column=col,
                        affected_rows=0,
                        affected_pct=0.0,
                        message=f"Column '{col}' has only one unique value: '{value}'.",
                        suggested_fix=f"Consider removing '{col}' if it provides no analytical value.",
                        business_impact="Constant columns add no information and waste storage.",
                    )
                )
        return findings

    @staticmethod
    def _check_negative_values(df: pd.DataFrame) -> list[QualityFinding]:
        """Detect negative values in columns that shouldn't be negative."""
        findings = []
        total_rows = max(len(df), 1)
        skip_keywords = {"id", "index", "lat", "lon", "latitude", "longitude", "coordinate"}

        for col in df.columns:
            if not pd.api.types.is_numeric_dtype(df[col]):
                continue
            col_lower = col.lower()
            if any(kw in col_lower for kw in skip_keywords):
                continue
            neg_count = int((df[col] < 0).sum())
            if neg_count > 0:
                pct = neg_count / total_rows * 100
                findings.append(
                    QualityFinding(
                        check_name="negative_values",
                        category="validity",
                        severity=Severity.WARNING,
                        column=col,
                        affected_rows=neg_count,
                        affected_pct=pct,
                        message=f"Column '{col}': {neg_count} negative values found.",
                        suggested_fix=f"Check if negative values in '{col}' are valid. Remove or correct if not.",
                        business_impact="Unexpected negative values may indicate data entry errors.",
                    )
                )
        return findings

    @staticmethod
    def _check_mixed_case(df: pd.DataFrame) -> list[QualityFinding]:
        """Detect categorical columns with mixed-case inconsistencies."""
        findings = []
        total_rows = max(len(df), 1)

        for col in df.columns:
            if df[col].dtype != "object":
                continue
            non_null = df[col].dropna().astype(str)
            if len(non_null) == 0 or non_null.nunique() > 50:
                continue

            # Check if same values appear in different cases
            lower_values = non_null.str.lower()
            unique_lower = lower_values.nunique()
            unique_original = non_null.nunique()

            if unique_original > unique_lower:
                diff = unique_original - unique_lower
                findings.append(
                    QualityFinding(
                        check_name="mixed_case",
                        category="consistency",
                        severity=Severity.INFO,
                        column=col,
                        affected_rows=diff,
                        affected_pct=diff / total_rows * 100,
                        message=f"Column '{col}' has {diff} values that differ only by case (e.g., 'Active' vs 'active').",
                        suggested_fix=f"Standardize '{col}' to consistent casing (e.g., all title-case or all lower-case).",
                        business_impact="Case inconsistencies cause duplicate categories in group-by operations.",
                    )
                )

        return findings

    # ── Date Validity Checks ────────────────────────────

    @staticmethod
    def _check_invalid_dates(df: pd.DataFrame) -> list[QualityFinding]:
        """Detect invalid date values in date-like columns."""
        findings = []
        total_rows = max(len(df), 1)

        date_keywords = ("date", "time", "timestamp", "created", "updated", "expiry", "deadline")
        date_cols = [
            c
            for c in df.columns
            if any(kw in c.lower() for kw in date_keywords)
            or pd.api.types.is_datetime64_any_dtype(df[c])
        ]

        for col in date_cols:
            series = df[col].dropna()
            if len(series) == 0:
                continue

            # If already datetime, skip
            if pd.api.types.is_datetime64_any_dtype(series):
                continue

            # Try parsing as datetime
            try:
                parsed = pd.to_datetime(series, errors="coerce")
                invalid_count = int(parsed.isna().sum())
            except Exception:
                invalid_count = len(series)

            if invalid_count > 0:
                pct = invalid_count / total_rows * 100
                severity = Severity.ERROR if pct > 20 else Severity.WARNING
                sample_vals = []
                with contextlib.suppress(Exception):
                    sample_vals = series[parsed.isna()].head(5).astype(str).tolist()
                findings.append(
                    QualityFinding(
                        check_name="invalid_dates",
                        category="validity",
                        severity=severity,
                        column=col,
                        affected_rows=invalid_count,
                        affected_pct=pct,
                        message=f"Column '{col}': {invalid_count} values cannot be parsed as dates.",
                        suggested_fix=f"Standardize date format in '{col}' (e.g., YYYY-MM-DD).",
                        business_impact="Invalid dates prevent time-based analysis and trend detection.",
                        sample_values=sample_vals,
                    )
                )

        return findings

    # ── Numeric Validity Checks ─────────────────────────

    @staticmethod
    def _check_invalid_numeric(df: pd.DataFrame) -> list[QualityFinding]:
        """Detect non-numeric values in numeric-like columns."""
        findings = []
        total_rows = max(len(df), 1)

        numeric_keywords = (
            "amount",
            "price",
            "cost",
            "revenue",
            "sales",
            "total",
            "quantity",
            "count",
            "sum",
            "avg",
            "average",
            "rate",
            "salary",
            "balance",
            "fee",
            "charge",
            "payment",
        )
        numeric_cols = [
            c
            for c in df.columns
            if any(kw in c.lower() for kw in numeric_keywords) and df[c].dtype == "object"
        ]

        for col in numeric_cols:
            series = df[col].dropna()
            if len(series) == 0:
                continue

            # Try converting to numeric
            converted = pd.to_numeric(series, errors="coerce")
            invalid_count = int(converted.isna().sum())

            if invalid_count > 0:
                pct = invalid_count / total_rows * 100
                severity = Severity.WARNING if pct < 10 else Severity.ERROR
                findings.append(
                    QualityFinding(
                        check_name="invalid_numeric",
                        category="validity",
                        severity=severity,
                        column=col,
                        affected_rows=invalid_count,
                        affected_pct=pct,
                        message=f"Column '{col}': {invalid_count} non-numeric values in a numeric column.",
                        suggested_fix=f"Clean '{col}' by removing currency symbols, commas, and non-numeric characters.",
                        business_impact="Non-numeric values in numeric columns prevent aggregation and statistical analysis.",
                        sample_values=series[converted.isna()].head(5).astype(str).tolist(),
                    )
                )

        return findings
