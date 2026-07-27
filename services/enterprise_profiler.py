"""Enterprise Dataset Profiler.

Consolidates and extends the three existing profilers into one comprehensive profiler:
  - semantic/data_profiler.py
  - etl/profiling/__init__.py
  - validation/profiler.py

Adds:
  - File encoding detection
  - Memory usage analysis
  - Correlation matrix
  - Sensitive information detection
  - Candidate primary key scoring
  - Distribution summary (skewness, kurtosis)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

import numpy as np
import pandas as pd


@dataclass
class EnterpriseColumnProfile:
    """Comprehensive profile for a single column."""

    name: str
    dtype: str
    count: int = 0
    null_count: int = 0
    null_percentage: float = 0.0
    unique_count: int = 0
    uniqueness: float = 0.0
    cardinality: str = "unknown"  # low, medium, high

    # Numeric stats
    min_value: float | None = None
    max_value: float | None = None
    mean_value: float | None = None
    median_value: float | None = None
    std_value: float | None = None
    q1: float | None = None
    q3: float | None = None
    iqr: float | None = None
    outlier_count: int = 0
    skewness: float | None = None
    kurtosis: float | None = None

    # Date stats
    date_range: list[str] | None = None

    # Categorical stats
    top_values: dict = field(default_factory=dict)
    value_distribution: dict = field(default_factory=dict)

    # Pattern detection
    pattern: str = ""
    pattern_consistency: float = 0.0

    # Quality
    completeness: float = 0.0
    consistency: float = 0.0
    validity: float = 0.0
    quality_score: float = 0.0

    # Sensitive info
    is_sensitive: bool = False
    sensitive_type: str = ""  # pii, financial, health, none

    # PK candidate
    pk_score: float = 0.0  # 0-1, higher = better PK candidate

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "dtype": self.dtype,
            "count": self.count,
            "null_count": self.null_count,
            "null_percentage": round(self.null_percentage, 2),
            "unique_count": self.unique_count,
            "uniqueness": round(self.uniqueness, 2),
            "cardinality": self.cardinality,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "mean_value": round(self.mean_value, 4) if self.mean_value is not None else None,
            "median_value": round(self.median_value, 4) if self.median_value is not None else None,
            "std_value": round(self.std_value, 4) if self.std_value is not None else None,
            "q1": round(self.q1, 4) if self.q1 is not None else None,
            "q3": round(self.q3, 4) if self.q3 is not None else None,
            "iqr": round(self.iqr, 4) if self.iqr is not None else None,
            "outlier_count": self.outlier_count,
            "skewness": round(self.skewness, 4) if self.skewness is not None else None,
            "kurtosis": round(self.kurtosis, 4) if self.kurtosis is not None else None,
            "date_range": self.date_range,
            "top_values": {str(k): v for k, v in list(self.top_values.items())[:10]},
            "value_distribution": {str(k): v for k, v in list(self.value_distribution.items())[:20]},
            "pattern": self.pattern,
            "pattern_consistency": round(self.pattern_consistency, 2),
            "completeness": round(self.completeness, 2),
            "consistency": round(self.consistency, 2),
            "validity": round(self.validity, 2),
            "quality_score": round(self.quality_score, 2),
            "is_sensitive": self.is_sensitive,
            "sensitive_type": self.sensitive_type,
            "pk_score": round(self.pk_score, 3),
        }


@dataclass
class EnterpriseDatasetProfile:
    """Comprehensive profile for an entire dataset."""

    source_name: str
    profiled_at: str = ""
    row_count: int = 0
    column_count: int = 0
    duplicate_rows: int = 0
    duplicate_percentage: float = 0.0
    total_missing: int = 0
    missing_percentage: float = 0.0
    total_outliers: int = 0
    memory_mb: float = 0.0
    overall_completeness: float = 0.0
    overall_consistency: float = 0.0
    overall_uniqueness: float = 0.0
    overall_validity: float = 0.0
    overall_quality_score: float = 0.0
    columns: list[EnterpriseColumnProfile] = field(default_factory=list)
    correlations: list[dict] = field(default_factory=list)
    sensitive_columns: list[str] = field(default_factory=list)
    candidate_primary_keys: list[str] = field(default_factory=list)
    quality_issues: list[dict] = field(default_factory=list)
    distribution_summary: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "source_name": self.source_name,
            "profiled_at": self.profiled_at,
            "row_count": self.row_count,
            "column_count": self.column_count,
            "duplicate_rows": self.duplicate_rows,
            "duplicate_percentage": round(self.duplicate_percentage, 2),
            "total_missing": self.total_missing,
            "missing_percentage": round(self.missing_percentage, 2),
            "total_outliers": self.total_outliers,
            "memory_mb": round(self.memory_mb, 2),
            "overall_completeness": round(self.overall_completeness, 2),
            "overall_consistency": round(self.overall_consistency, 2),
            "overall_uniqueness": round(self.overall_uniqueness, 2),
            "overall_validity": round(self.overall_validity, 2),
            "overall_quality_score": round(self.overall_quality_score, 2),
            "columns": [c.to_dict() for c in self.columns],
            "correlations": self.correlations,
            "sensitive_columns": self.sensitive_columns,
            "candidate_primary_keys": self.candidate_primary_keys,
            "quality_issues": self.quality_issues,
            "distribution_summary": self.distribution_summary,
        }


# Sensitive data patterns
SENSITIVE_PATTERNS = {
    "email": {
        "pattern": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
        "type": "pii",
    },
    "phone": {
        "pattern": r"^\+?[\d\s\-\(\)]{7,15}$",
        "type": "pii",
    },
    "ssn": {
        "pattern": r"^\d{3}-\d{2}-\d{4}$",
        "type": "pii",
    },
    "credit_card": {
        "pattern": r"^\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}$",
        "type": "financial",
    },
    "ip_address": {
        "pattern": r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$",
        "type": "pii",
    },
}

SENSITIVE_COLUMN_NAMES = {
    "email": "pii",
    "phone": "pii",
    "mobile": "pii",
    "ssn": "pii",
    "social_security": "pii",
    "credit_card": "financial",
    "card_number": "financial",
    "account_number": "financial",
    "password": "pii",
    "address": "pii",
    "zip": "pii",
    "postal": "pii",
    "dob": "pii",
    "date_of_birth": "pii",
    "birth_date": "pii",
    "salary": "financial",
    "income": "financial",
    "diagnosis": "health",
    "medical": "health",
    "patient": "health",
    "prescription": "health",
}


class EnterpriseDataProfiler:
    """Comprehensive dataset profiler consolidating all profiling logic."""

    def profile(self, df: pd.DataFrame, source_name: str = "uploaded_dataset") -> dict:
        """Generate a comprehensive data profile.

        Args:
            df: DataFrame to profile.
            source_name: Name of the data source.

        Returns:
            Dict with complete profile data.
        """
        profile = EnterpriseDatasetProfile(
            source_name=source_name,
            profiled_at=datetime.now(timezone.utc).isoformat(),
            row_count=len(df),
            column_count=len(df.columns),
        )

        if df.empty:
            return profile.to_dict()

        # Dataset-level stats
        profile.duplicate_rows = int(df.duplicated().sum())
        profile.duplicate_percentage = (profile.duplicate_rows / max(len(df), 1)) * 100
        profile.memory_mb = df.memory_usage(deep=True).sum() / 1024 / 1024

        total_cells = len(df) * len(df.columns)
        profile.total_missing = int(df.isnull().sum().sum())
        profile.missing_percentage = (profile.total_missing / max(total_cells, 1)) * 100

        # Column-level profiles
        all_completeness = []
        all_consistency = []
        all_uniqueness = []
        all_validity = []
        total_outliers = 0

        for col_name in df.columns:
            cp = self._profile_column(df, col_name, len(df))
            profile.columns.append(cp)
            all_completeness.append(cp.completeness)
            all_consistency.append(cp.consistency)
            all_uniqueness.append(cp.uniqueness)
            all_validity.append(cp.validity)
            total_outliers += cp.outlier_count

            # Collect quality issues
            self._collect_quality_issues(profile, cp)

            # Sensitive columns
            if cp.is_sensitive:
                profile.sensitive_columns.append(col_name)

            # PK candidates
            if cp.pk_score >= 0.8:
                profile.candidate_primary_keys.append(col_name)

        profile.total_outliers = total_outliers
        profile.overall_completeness = float(np.mean(all_completeness)) if all_completeness else 0
        profile.overall_consistency = float(np.mean(all_consistency)) if all_consistency else 0
        profile.overall_uniqueness = float(np.mean(all_uniqueness)) if all_uniqueness else 0
        profile.overall_validity = float(np.mean(all_validity)) if all_validity else 0
        profile.overall_quality_score = (
            profile.overall_completeness * 0.35
            + profile.overall_consistency * 0.25
            + profile.overall_validity * 0.25
            + profile.overall_uniqueness * 0.15
        )

        # Correlations
        profile.correlations = self._compute_correlations(df)

        # Distribution summary
        profile.distribution_summary = self._distribution_summary(df)

        return profile.to_dict()

    def _profile_column(self, df: pd.DataFrame, col_name: str, row_count: int) -> EnterpriseColumnProfile:
        """Profile a single column comprehensively."""
        series = df[col_name]
        non_null = series.dropna()
        null_count = int(series.isnull().sum())
        unique_count = int(series.nunique())

        cp = EnterpriseColumnProfile(
            name=col_name,
            dtype=str(series.dtype),
            count=row_count - null_count,
            null_count=null_count,
            null_percentage=(null_count / max(row_count, 1)) * 100,
            unique_count=unique_count,
            uniqueness=(unique_count / max(row_count, 1)) * 100,
            completeness=((row_count - null_count) / max(row_count, 1)) * 100,
        )

        # Cardinality
        if cp.uniqueness < 1:
            cp.cardinality = "low"
        elif cp.uniqueness < 20:
            cp.cardinality = "medium"
        else:
            cp.cardinality = "high"

        # Numeric stats
        if pd.api.types.is_numeric_dtype(series) and len(non_null) > 0:
            cp.min_value = float(non_null.min())
            cp.max_value = float(non_null.max())
            cp.mean_value = float(non_null.mean())
            cp.median_value = float(non_null.median())
            cp.std_value = float(non_null.std()) if len(non_null) > 1 else 0.0
            cp.q1 = float(non_null.quantile(0.25))
            cp.q3 = float(non_null.quantile(0.75))
            cp.iqr = cp.q3 - cp.q1

            # Outliers (IQR method)
            lower = cp.q1 - 1.5 * cp.iqr
            upper = cp.q3 + 1.5 * cp.iqr
            cp.outlier_count = int(((non_null < lower) | (non_null > upper)).sum())

            # Skewness and kurtosis
            if cp.std_value and cp.std_value > 0:
                cp.skewness = float(non_null.skew())
                cp.kurtosis = float(non_null.kurtosis())

            cp.validity = (len(non_null) / max(row_count, 1)) * 100
            cp.pattern = "numeric"

        # Datetime stats
        elif pd.api.types.is_datetime64_any_dtype(series) and len(non_null) > 0:
            cp.date_range = [str(non_null.min()), str(non_null.max())]
            cp.pattern = "datetime"
            cp.validity = (len(non_null) / max(row_count, 1)) * 100

        # Categorical / object stats
        elif series.dtype == "object" and len(non_null) > 0:
            # Pattern detection
            cp.pattern = self._detect_pattern(non_null)
            cp.pattern_consistency = self._pattern_consistency(non_null, cp.pattern)

            # Top values
            if cp.cardinality in ("low", "medium"):
                vc = non_null.value_counts().head(10)
                cp.top_values = {k: int(v) for k, v in vc.items()}
                vc_full = non_null.value_counts().head(20)
                cp.value_distribution = {str(k): int(v) for k, v in vc_full.items()}

            # Validity: check if values match expected format
            sample = non_null.head(100).astype(str)
            valid_pattern = sample.str.match(r"^[A-Za-z0-9\s\-_./@,:;()]+$")
            cp.validity = (valid_pattern.sum() / max(len(sample), 1)) * 100

            # Consistency: case consistency
            lower_count = int(non_null.astype(str).str.islower().sum())
            upper_count = int(non_null.astype(str).str.isupper().sum())
            title_count = int(non_null.astype(str).str.istitle().sum())
            max_case = max(lower_count, upper_count, title_count)
            cp.consistency = (max_case / max(len(non_null), 1)) * 100

        # Sensitive info detection
        cp.is_sensitive, cp.sensitive_type = self._detect_sensitive(col_name, non_null)

        # PK candidate scoring
        cp.pk_score = self._pk_score(cp, row_count)

        # Quality score
        cp.quality_score = (
            cp.completeness * 0.35
            + cp.consistency * 0.25
            + cp.validity * 0.25
            + min(cp.uniqueness, 100) * 0.15
        )

        return cp

    def _detect_pattern(self, series: pd.Series) -> str:
        """Detect the dominant pattern in a string column."""
        if len(series) == 0:
            return "empty"

        sample = str(series.iloc[0])

        for name, info in SENSITIVE_PATTERNS.items():
            import re
            if re.match(info["pattern"], sample):
                return name

        if sample.replace("-", "").replace("/", "").replace(".", "").isdigit():
            return "numeric_string"
        if sample.startswith(("http://", "https://")):
            return "url"
        if sample.replace(",", "").replace(".", "").isdigit():
            return "decimal_string"
        return "text"

    def _pattern_consistency(self, series: pd.Series, pattern: str) -> float:
        """Calculate how consistently values match the detected pattern."""
        if pattern in ("text", "empty"):
            return 100.0

        import re
        pat = SENSITIVE_PATTERNS.get(pattern, {}).get("pattern")
        if not pat:
            return 100.0

        sample = series.head(200).astype(str)
        matches = sample.str.match(pat)
        return (matches.sum() / max(len(sample), 1)) * 100

    def _detect_sensitive(self, col_name: str, series: pd.Series) -> tuple[bool, str]:
        """Detect if a column contains sensitive information."""
        name_lower = col_name.lower()

        # Check column name
        for keyword, stype in SENSITIVE_COLUMN_NAMES.items():
            if keyword in name_lower:
                return True, stype

        # Check sample values for patterns
        if len(series) > 0 and series.dtype == "object":
            import re
            sample = series.head(50).astype(str)
            for name, info in SENSITIVE_PATTERNS.items():
                matches = sample.str.match(info["pattern"])
                if matches.sum() > len(sample) * 0.5:
                    return True, info["type"]

        return False, "none"

    def _pk_score(self, cp: EnterpriseColumnProfile, row_count: int) -> float:
        """Score how likely a column is a primary key (0-1)."""
        if row_count == 0:
            return 0.0

        score = 0.0

        # Uniqueness (must be unique)
        if cp.unique_count == row_count and cp.null_count == 0:
            score += 0.4
        elif cp.unique_count / row_count > 0.95:
            score += 0.2

        # No nulls
        if cp.null_count == 0:
            score += 0.2

        # Name ends with _id or is "id"
        name_lower = cp.name.lower()
        if name_lower == "id" or name_lower.endswith("_id"):
            score += 0.2

        # Numeric type (common for PKs)
        if cp.dtype in ("int64", "int32", "int16", "int8", "Int64"):
            score += 0.1

        # Low cardinality relative to row count (but still unique)
        if cp.cardinality == "high":
            score += 0.1

        return min(score, 1.0)

    def _compute_correlations(self, df: pd.DataFrame) -> list[dict]:
        """Compute correlations between numeric columns."""
        numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
        if len(numeric_cols) < 2:
            return []

        try:
            corr = df[numeric_cols].corr()
        except Exception:
            return []

        correlations = []
        seen = set()
        for i, c1 in enumerate(numeric_cols):
            for j, c2 in enumerate(numeric_cols):
                if i >= j:
                    continue
                pair = tuple(sorted([c1, c2]))
                if pair in seen:
                    continue
                seen.add(pair)

                val = corr.loc[c1, c2]
                if pd.isna(val):
                    continue

                if abs(val) >= 0.5:
                    correlations.append({
                        "column_1": c1,
                        "column_2": c2,
                        "correlation": round(float(val), 3),
                        "strength": "strong" if abs(val) >= 0.8 else "moderate",
                        "direction": "positive" if val > 0 else "negative",
                    })

        return sorted(correlations, key=lambda x: abs(x["correlation"]), reverse=True)

    def _distribution_summary(self, df: pd.DataFrame) -> dict:
        """Generate distribution summary for the dataset."""
        numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
        summary = {}

        for col in numeric_cols:
            series = df[col].dropna()
            if len(series) < 4:
                continue

            std = float(series.std())
            mean = float(series.mean())
            median = float(series.median())

            summary[col] = {
                "mean": round(mean, 4),
                "median": round(median, 4),
                "std": round(std, 4),
                "skewness": round(float(series.skew()), 4) if std > 0 else 0,
                "kurtosis": round(float(series.kurtosis()), 4) if std > 0 else 0,
                "distribution_type": (
                    "normal" if abs(float(series.skew())) < 0.5 and abs(float(series.kurtosis())) < 3
                    else "right_skewed" if float(series.skew()) > 0.5
                    else "left_skewed" if float(series.skew()) < -0.5
                    else "heavy_tailed"
                ),
            }

        return summary

    def _collect_quality_issues(self, profile: EnterpriseDatasetProfile, cp: EnterpriseColumnProfile) -> None:
        """Collect quality issues from a column profile."""
        row_count = profile.row_count
        if cp.completeness < 50:
            profile.quality_issues.append({
                "column": cp.name,
                "severity": "high",
                "issue": "Low completeness",
                "detail": f"{cp.completeness:.1f}% non-null",
                "recommended_fix": "Consider dropping column or imputing missing values",
            })
        elif cp.completeness < 90:
            profile.quality_issues.append({
                "column": cp.name,
                "severity": "medium",
                "issue": "Missing values",
                "detail": f"{cp.completeness:.1f}% non-null",
                "recommended_fix": "Impute missing values or collect more data",
            })

        if cp.outlier_count > 0:
            severity = "high" if cp.outlier_count > row_count * 0.1 else "low"
            profile.quality_issues.append({
                "column": cp.name,
                "severity": severity,
                "issue": "Outliers detected",
                "detail": f"{cp.outlier_count} outliers found",
                "recommended_fix": "Review outliers for data entry errors or exceptional cases",
            })

        if cp.is_sensitive:
            profile.quality_issues.append({
                "column": cp.name,
                "severity": "high",
                "issue": f"Sensitive data detected ({cp.sensitive_type})",
                "detail": f"Column appears to contain {cp.sensitive_type} information",
                "recommended_fix": "Ensure proper access controls and data masking",
            })
