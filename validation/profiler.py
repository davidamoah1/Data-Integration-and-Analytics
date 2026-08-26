"""Validation Profiler â€” generates column statistics and data profiling metrics."""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd


@dataclass
class ColumnProfile:
    name: str
    dtype: str
    total_count: int
    null_count: int
    null_percentage: float
    unique_count: int
    uniqueness: float
    top_values: dict
    min_value: float | None = None
    max_value: float | None = None
    mean_value: float | None = None
    median_value: float | None = None
    std_value: float | None = None
    pattern: str | None = None


@dataclass
class DataProfileResult:
    row_count: int
    column_count: int
    column_profiles: list[ColumnProfile] = field(default_factory=list)
    overall_completeness: float = 0.0
    overall_uniqueness: float = 0.0
    duplicate_percentage: float = 0.0
    cardinality: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "row_count": self.row_count,
            "column_count": self.column_count,
            "overall_completeness": self.overall_completeness,
            "overall_uniqueness": self.overall_uniqueness,
            "duplicate_percentage": self.duplicate_percentage,
            "columns": [
                {
                    "name": c.name,
                    "dtype": c.dtype,
                    "total_count": c.total_count,
                    "null_count": c.null_count,
                    "null_percentage": c.null_percentage,
                    "unique_count": c.unique_count,
                    "uniqueness": c.uniqueness,
                    "top_values": c.top_values,
                    "min_value": c.min_value,
                    "max_value": c.max_value,
                    "mean_value": c.mean_value,
                    "median_value": c.median_value,
                    "std_value": c.std_value,
                }
                for c in self.column_profiles
            ],
        }


class ValidationProfiler:
    """Generates data profiling statistics for a DataFrame."""

    @staticmethod
    def profile(df: pd.DataFrame) -> DataProfileResult:
        result = DataProfileResult(
            row_count=len(df),
            column_count=len(df.columns),
        )

        total_cells = len(df) * len(df.columns) if len(df.columns) > 0 else 0
        total_nulls = int(df.isnull().sum().sum())
        result.overall_completeness = ((total_cells - total_nulls) / max(total_cells, 1)) * 100

        dup_count = int(df.duplicated().sum())
        result.duplicate_percentage = (dup_count / max(len(df), 1)) * 100

        for col in df.columns:
            profile = ValidationProfiler._profile_column(df, col)
            result.column_profiles.append(profile)
            result.cardinality[col] = profile.unique_count

        avg_uniqueness = sum(c.uniqueness for c in result.column_profiles) / max(
            len(result.column_profiles), 1
        )
        result.overall_uniqueness = avg_uniqueness

        return result

    @staticmethod
    def _profile_column(df: pd.DataFrame, col: str) -> ColumnProfile:
        series = df[col]
        total = len(series)
        null_count = int(series.isnull().sum())
        unique_count = int(series.nunique())

        top_values = {}
        if series.dtype == "object":
            vc = series.dropna().astype(str).value_counts().head(5)
        else:
            vc = series.dropna().value_counts().head(5)
        top_values = {str(k): int(v) for k, v in vc.items()}

        profile = ColumnProfile(
            name=str(col),
            dtype=str(series.dtype),
            total_count=total,
            null_count=null_count,
            null_percentage=(null_count / max(total, 1)) * 100,
            unique_count=unique_count,
            uniqueness=(unique_count / max(total, 1)) * 100,
            top_values=top_values,
        )

        if pd.api.types.is_numeric_dtype(series):
            non_null = series.dropna()
            if len(non_null) > 0:
                profile.min_value = float(non_null.min())
                profile.max_value = float(non_null.max())
                profile.mean_value = float(non_null.mean())
                profile.median_value = float(non_null.median())
                profile.std_value = float(non_null.std()) if len(non_null) > 1 else 0.0

        return profile
