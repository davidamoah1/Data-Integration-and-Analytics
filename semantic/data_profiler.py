"""MODULE 2 — Data Profiling.

Calculates data quality metrics: completeness, consistency, uniqueness,
validity, accuracy, duplicates, missing values, outliers, patterns.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd


@dataclass
class ColumnProfile:
    """Profile for a single column."""

    name: str
    completeness: float = 0.0  # % non-null
    uniqueness: float = 0.0  # % unique
    consistency: float = 0.0  # % matching dominant pattern
    validity: float = 0.0  # % valid per type rules
    duplicate_count: int = 0
    missing_count: int = 0
    outlier_count: int = 0
    pattern: str = ""
    date_range: tuple | None = None
    numeric_range: tuple | None = None
    top_values: dict = field(default_factory=dict)
    quality_score: float = 0.0

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "completeness": round(self.completeness, 2),
            "uniqueness": round(self.uniqueness, 2),
            "consistency": round(self.consistency, 2),
            "validity": round(self.validity, 2),
            "duplicate_count": self.duplicate_count,
            "missing_count": self.missing_count,
            "outlier_count": self.outlier_count,
            "pattern": self.pattern,
            "date_range": [str(d) for d in self.date_range] if self.date_range else None,
            "numeric_range": [float(v) for v in self.numeric_range] if self.numeric_range else None,
            "top_values": {str(k): v for k, v in list(self.top_values.items())[:10]},
            "quality_score": round(self.quality_score, 2),
        }


@dataclass
class DatasetProfile:
    """Profile for an entire dataset."""

    row_count: int
    column_count: int
    duplicate_rows: int = 0
    total_missing: int = 0
    total_outliers: int = 0
    overall_completeness: float = 0.0
    overall_consistency: float = 0.0
    overall_uniqueness: float = 0.0
    overall_validity: float = 0.0
    overall_quality_score: float = 0.0
    columns: list[ColumnProfile] = field(default_factory=list)
    quality_issues: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "row_count": self.row_count,
            "column_count": self.column_count,
            "duplicate_rows": self.duplicate_rows,
            "total_missing": self.total_missing,
            "total_outliers": self.total_outliers,
            "overall_completeness": round(self.overall_completeness, 2),
            "overall_consistency": round(self.overall_consistency, 2),
            "overall_uniqueness": round(self.overall_uniqueness, 2),
            "overall_validity": round(self.overall_validity, 2),
            "overall_quality_score": round(self.overall_quality_score, 2),
            "columns": [c.to_dict() for c in self.columns],
            "quality_issues": self.quality_issues,
        }


class DataProfiler:
    """Profiles data quality metrics from a DataFrame."""

    @staticmethod
    def profile(df: pd.DataFrame) -> DatasetProfile:
        """Profile an entire dataset.

        Args:
            df: DataFrame to profile.

        Returns:
            DatasetProfile with quality metrics.
        """
        row_count = len(df)
        col_count = len(df.columns)
        duplicate_rows = int(df.duplicated().sum())

        col_profiles = []
        all_completeness = []
        all_consistency = []
        all_uniqueness = []
        all_validity = []
        quality_issues = []
        total_missing = 0
        total_outliers = 0

        for col_name in df.columns:
            cp = DataProfiler._profile_column(df, col_name, row_count)
            col_profiles.append(cp)
            all_completeness.append(cp.completeness)
            all_consistency.append(cp.consistency)
            all_uniqueness.append(cp.uniqueness)
            all_validity.append(cp.validity)
            total_missing += cp.missing_count
            total_outliers += cp.outlier_count

            # Collect quality issues
            if cp.completeness < 50:
                quality_issues.append(
                    {
                        "column": col_name,
                        "severity": "high",
                        "issue": "Low completeness",
                        "detail": f"{cp.completeness:.1f}% non-null",
                    }
                )
            elif cp.completeness < 90:
                quality_issues.append(
                    {
                        "column": col_name,
                        "severity": "medium",
                        "issue": "Missing values",
                        "detail": f"{cp.completeness:.1f}% non-null",
                    }
                )
            if cp.outlier_count > 0:
                quality_issues.append(
                    {
                        "column": col_name,
                        "severity": "low",
                        "issue": "Outliers detected",
                        "detail": f"{cp.outlier_count} outliers found",
                    }
                )
            if cp.duplicate_count > row_count * 0.1:
                quality_issues.append(
                    {
                        "column": col_name,
                        "severity": "medium",
                        "issue": "High duplication",
                        "detail": f"{cp.duplicate_count} duplicate values",
                    }
                )

        overall_completeness = np.mean(all_completeness) if all_completeness else 0
        overall_consistency = np.mean(all_consistency) if all_consistency else 0
        overall_uniqueness = np.mean(all_uniqueness) if all_uniqueness else 0
        overall_validity = np.mean(all_validity) if all_validity else 0
        overall_quality = (
            overall_completeness * 0.35
            + overall_consistency * 0.25
            + overall_validity * 0.25
            + overall_uniqueness * 0.15
        )

        return DatasetProfile(
            row_count=row_count,
            column_count=col_count,
            duplicate_rows=duplicate_rows,
            total_missing=total_missing,
            total_outliers=total_outliers,
            overall_completeness=overall_completeness,
            overall_consistency=overall_consistency,
            overall_uniqueness=overall_uniqueness,
            overall_validity=overall_validity,
            overall_quality_score=overall_quality,
            columns=col_profiles,
            quality_issues=quality_issues,
        )

    @staticmethod
    def _profile_column(df: pd.DataFrame, col_name: str, row_count: int) -> ColumnProfile:
        """Profile a single column."""
        series = df[col_name]
        non_null = series.dropna()
        missing = int(series.isnull().sum())
        completeness = ((row_count - missing) / row_count * 100) if row_count > 0 else 0
        unique_count = int(series.nunique())
        uniqueness = (unique_count / row_count * 100) if row_count > 0 else 0
        duplicate_count = row_count - unique_count - missing

        # Validity: check if values match expected type
        validity = 100.0
        if np.issubdtype(series.dtype, np.number):
            # Check for non-numeric strings that were coerced
            validity = ((non_null.shape[0]) / row_count * 100) if row_count > 0 else 0
        elif series.dtype == "object" and len(non_null) > 0:
            # Check for consistent formatting
            # Pattern detection
            sample = non_null.head(100)
            patterns = sample.astype(str).str.match(r"^[A-Za-z0-9\s\-_./@]+$")
            validity = (patterns.sum() / len(sample) * 100) if len(sample) > 0 else 0

        # Consistency: how well values match the dominant pattern
        consistency = 100.0
        if series.dtype == "object" and len(non_null) > 0:
            # Check case consistency
            lower_count = int(non_null.astype(str).str.islower().sum())
            upper_count = int(non_null.astype(str).str.isupper().sum())
            title_count = int(non_null.astype(str).str.istitle().sum())
            max_case = max(lower_count, upper_count, title_count)
            consistency = (max_case / len(non_null) * 100) if len(non_null) > 0 else 0

        # Outlier detection for numeric columns
        outlier_count = 0
        numeric_range = None
        if np.issubdtype(series.dtype, np.number) and len(non_null) > 4:
            q1 = non_null.quantile(0.25)
            q3 = non_null.quantile(0.75)
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            outliers = non_null[(non_null < lower_bound) | (non_null > upper_bound)]
            outlier_count = int(len(outliers))
            numeric_range = (float(non_null.min()), float(non_null.max()))

        # Date range for datetime columns
        date_range = None
        pattern = ""
        if np.issubdtype(series.dtype, np.datetime64):
            date_range = (non_null.min(), non_null.max())
            pattern = "datetime"
        elif series.dtype == "object" and len(non_null) > 0:
            # Detect common patterns
            sample_str = str(non_null.iloc[0]) if len(non_null) > 0 else ""
            if sample_str.replace("-", "").replace("/", "").replace(".", "").isdigit():
                pattern = "numeric_string"
            elif "@" in sample_str:
                pattern = "email"
            elif sample_str.startswith(("http://", "https://")):
                pattern = "url"
            else:
                pattern = "text"

        # Top values for categorical
        top_values = {}
        if uniqueness < 50:
            vc = non_null.value_counts().head(10)
            top_values = {k: int(v) for k, v in vc.items()}

        # Quality score
        quality_score = (
            completeness * 0.35 + consistency * 0.25 + validity * 0.25 + min(uniqueness, 100) * 0.15
        )

        return ColumnProfile(
            name=col_name,
            completeness=completeness,
            uniqueness=uniqueness,
            consistency=consistency,
            validity=validity,
            duplicate_count=duplicate_count,
            missing_count=missing,
            outlier_count=outlier_count,
            pattern=pattern,
            date_range=date_range,
            numeric_range=numeric_range,
            top_values=top_values,
            quality_score=quality_score,
        )
