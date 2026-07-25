"""Data Drift Detector.

Detects statistical distribution changes between two datasets or
between two time periods within the same dataset. Uses:
  - Population Stability Index (PSI) for numeric columns
  - Chi-square-like frequency comparison for categorical columns
  - Mean/median shift detection
  - New category appearance / category disappearance

A PSI > 0.25 indicates significant drift. PSI > 0.10 is moderate drift.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd


@dataclass
class ColumnDrift:
    """Drift result for a single column."""

    column: str
    drift_type: str  # "numeric" or "categorical"
    psi: float | None  # Population Stability Index (numeric only)
    drift_detected: bool
    drift_severity: str  # "none", "low", "moderate", "significant"
    old_stats: dict
    new_stats: dict
    new_categories: list = field(default_factory=list)
    disappeared_categories: list = field(default_factory=list)
    message: str = ""

    def to_dict(self) -> dict:
        return {
            "column": self.column,
            "drift_type": self.drift_type,
            "psi": round(self.psi, 4) if self.psi is not None else None,
            "drift_detected": self.drift_detected,
            "drift_severity": self.drift_severity,
            "old_stats": self.old_stats,
            "new_stats": self.new_stats,
            "new_categories": self.new_categories,
            "disappeared_categories": self.disappeared_categories,
            "message": self.message,
        }


@dataclass
class DriftResult:
    """Overall drift detection result."""

    drift_detected: bool
    drift_score: float  # Average PSI across numeric columns
    drifted_columns: list[ColumnDrift] = field(default_factory=list)
    summary: str = ""

    def to_dict(self) -> dict:
        return {
            "drift_detected": self.drift_detected,
            "drift_score": round(self.drift_score, 4),
            "drifted_columns": [c.to_dict() for c in self.drifted_columns],
            "summary": self.summary,
        }


class DriftDetector:
    """Detects data drift between two datasets or time periods."""

    # PSI thresholds
    PSI_NO_DRIFT = 0.10
    PSI_MODERATE_DRIFT = 0.25

    @staticmethod
    def detect(
        old_df: pd.DataFrame,
        new_df: pd.DataFrame,
        common_columns: list[str] | None = None,
    ) -> DriftResult:
        """Detect drift between two datasets.

        Args:
            old_df: Reference (baseline) DataFrame.
            new_df: Current DataFrame to compare.
            common_columns: Columns to compare. If None, uses intersection.

        Returns:
            DriftResult with per-column drift details.
        """
        if common_columns is None:
            common_columns = list(set(old_df.columns) & set(new_df.columns))

        drifted_columns: list[ColumnDrift] = []
        psi_values: list[float] = []

        for col in common_columns:
            if col not in old_df.columns or col not in new_df.columns:
                continue

            old_series = old_df[col].dropna()
            new_series = new_df[col].dropna()

            if len(old_series) == 0 or len(new_series) == 0:
                continue

            if pd.api.types.is_numeric_dtype(old_df[col]) and pd.api.types.is_numeric_dtype(new_df[col]):
                drift = DriftDetector._detect_numeric_drift(col, old_series, new_series)
                if drift.psi is not None:
                    psi_values.append(drift.psi)
            else:
                drift = DriftDetector._detect_categorical_drift(col, old_series, new_series)

            drifted_columns.append(drift)

        # Sort by drift severity
        severity_order = {"significant": 0, "moderate": 1, "low": 2, "none": 3}
        drifted_columns.sort(key=lambda c: severity_order.get(c.drift_severity, 99))

        drift_detected = any(c.drift_detected for c in drifted_columns)
        avg_psi = float(np.mean(psi_values)) if psi_values else 0.0

        summary = DriftDetector._generate_summary(drifted_columns, avg_psi)

        return DriftResult(
            drift_detected=drift_detected,
            drift_score=avg_psi,
            drifted_columns=drifted_columns,
            summary=summary,
        )

    @staticmethod
    def detect_time_drift(
        df: pd.DataFrame,
        date_col: str,
        numeric_cols: list[str] | None = None,
    ) -> DriftResult:
        """Detect drift between the first and second half of a dataset.

        Args:
            df: DataFrame with a date column.
            date_col: Name of the date column.
            numeric_cols: Columns to check. If None, uses all numeric columns.

        Returns:
            DriftResult comparing first half vs second half.
        """
        if date_col not in df.columns:
            return DriftResult(
                drift_detected=False,
                drift_score=0.0,
                summary="No date column found — cannot detect time drift.",
            )

        df_temp = df.copy()
        if not pd.api.types.is_datetime64_any_dtype(df_temp[date_col]):
            df_temp[date_col] = pd.to_datetime(df_temp[date_col], errors="coerce")
        df_temp = df_temp.dropna(subset=[date_col]).sort_values(date_col)

        if len(df_temp) < 4:
            return DriftResult(
                drift_detected=False,
                drift_score=0.0,
                summary="Insufficient data for time drift detection.",
            )

        midpoint = df_temp[date_col].median()
        old_df = df_temp[df_temp[date_col] <= midpoint]
        new_df = df_temp[df_temp[date_col] > midpoint]

        if old_df.empty or new_df.empty:
            return DriftResult(
                drift_detected=False,
                drift_score=0.0,
                summary="Cannot split data into two periods for drift comparison.",
            )

        return DriftDetector.detect(old_df, new_df, numeric_cols)

    @staticmethod
    def _detect_numeric_drift(col: str, old_series: pd.Series, new_series: pd.Series) -> ColumnDrift:
        """Detect drift in a numeric column using PSI."""
        psi = DriftDetector._compute_psi(old_series, new_series)

        if psi > DriftDetector.PSI_MODERATE_DRIFT:
            severity = "significant"
            drift_detected = True
        elif psi > DriftDetector.PSI_NO_DRIFT:
            severity = "moderate"
            drift_detected = True
        elif psi > 0.05:
            severity = "low"
            drift_detected = False
        else:
            severity = "none"
            drift_detected = False

        old_stats = {
            "mean": round(float(old_series.mean()), 4),
            "median": round(float(old_series.median()), 4),
            "std": round(float(old_series.std()), 4) if len(old_series) > 1 else 0.0,
            "min": round(float(old_series.min()), 4),
            "max": round(float(old_series.max()), 4),
        }
        new_stats = {
            "mean": round(float(new_series.mean()), 4),
            "median": round(float(new_series.median()), 4),
            "std": round(float(new_series.std()), 4) if len(new_series) > 1 else 0.0,
            "min": round(float(new_series.min()), 4),
            "max": round(float(new_series.max()), 4),
        }

        mean_shift = ((new_stats["mean"] - old_stats["mean"]) / old_stats["mean"] * 100) if old_stats["mean"] != 0 else 0.0

        message = (
            f"'{col}' {'significant' if severity == 'significant' else 'moderate'} drift detected "
            f"(PSI={psi:.4f}). Mean shifted from {old_stats['mean']} to {new_stats['mean']} ({mean_shift:+.1f}%)."
            if drift_detected
            else f"'{col}' no significant drift (PSI={psi:.4f})."
        )

        return ColumnDrift(
            column=col,
            drift_type="numeric",
            psi=psi,
            drift_detected=drift_detected,
            drift_severity=severity,
            old_stats=old_stats,
            new_stats=new_stats,
            message=message,
        )

    @staticmethod
    def _detect_categorical_drift(col: str, old_series: pd.Series, new_series: pd.Series) -> ColumnDrift:
        """Detect drift in a categorical column using frequency comparison."""
        old_counts = old_series.value_counts(normalize=True)
        new_counts = new_series.value_counts(normalize=True)

        old_categories = set(old_counts.index)
        new_categories = set(new_counts.index)

        appeared = list(new_categories - old_categories)
        disappeared = list(old_categories - new_categories)

        # Compute a simple drift score based on frequency changes
        all_cats = old_categories | new_categories
        total_change = 0.0
        for cat in all_cats:
            old_freq = float(old_counts.get(cat, 0))
            new_freq = float(new_counts.get(cat, 0))
            total_change += abs(new_freq - old_freq)

        # Normalize to 0-1 range (total_change / 2 because max change is 2.0)
        drift_score = total_change / 2.0

        if drift_score > 0.30:
            severity = "significant"
            drift_detected = True
        elif drift_score > 0.15:
            severity = "moderate"
            drift_detected = True
        elif drift_score > 0.05:
            severity = "low"
            drift_detected = False
        else:
            severity = "none"
            drift_detected = False

        old_stats = {
            "unique_count": int(old_series.nunique()),
            "top_value": str(old_counts.index[0]) if len(old_counts) > 0 else "",
            "top_freq": round(float(old_counts.iloc[0]), 4) if len(old_counts) > 0 else 0.0,
        }
        new_stats = {
            "unique_count": int(new_series.nunique()),
            "top_value": str(new_counts.index[0]) if len(new_counts) > 0 else "",
            "top_freq": round(float(new_counts.iloc[0]), 4) if len(new_counts) > 0 else 0.0,
        }

        message_parts = []
        if appeared:
            message_parts.append(f"{len(appeared)} new categories appeared: {appeared[:3]}")
        if disappeared:
            message_parts.append(f"{len(disappeared)} categories disappeared: {disappeared[:3]}")
        if drift_detected:
            message_parts.append(f"drift score={drift_score:.4f}")

        message = f"'{col}' {severity} drift. " + "; ".join(message_parts) if message_parts else f"'{col}' no significant drift."

        return ColumnDrift(
            column=col,
            drift_type="categorical",
            psi=None,
            drift_detected=drift_detected,
            drift_severity=severity,
            old_stats=old_stats,
            new_stats=new_stats,
            new_categories=appeared,
            disappeared_categories=disappeared,
            message=message,
        )

    @staticmethod
    def _compute_psi(old: pd.Series, new: pd.Series, bins: int = 10) -> float:
        """Compute Population Stability Index (PSI) for numeric data.

        PSI = sum((p_new - p_old) * ln(p_new / p_old))

        PSI < 0.10: No significant change
        PSI 0.10-0.25: Moderate change
        PSI > 0.25: Significant change
        """
        # Create bins based on old data distribution
        old_array = old.values
        new_array = new.values

        # Use quantile-based bins
        _, bin_edges = np.histogram(old_array, bins=bins)

        # Ensure bin edges cover both distributions
        bin_edges[0] = min(bin_edges[0], new_array.min())
        bin_edges[-1] = max(bin_edges[-1], new_array.max())

        # Compute proportions
        old_counts, _ = np.histogram(old_array, bins=bin_edges)
        new_counts, _ = np.histogram(new_array, bins=bin_edges)

        old_props = old_counts / max(len(old_array), 1)
        new_props = new_counts / max(len(new_array), 1)

        # Avoid log(0) by adding small epsilon
        eps = 1e-6
        old_props = np.where(old_props == 0, eps, old_props)
        new_props = np.where(new_props == 0, eps, new_props)

        psi = float(np.sum((new_props - old_props) * np.log(new_props / old_props)))

        return max(psi, 0.0)  # PSI is non-negative

    @staticmethod
    def _generate_summary(drifted_columns: list[ColumnDrift], avg_psi: float) -> str:
        """Generate a human-readable drift summary."""
        drifted = [c for c in drifted_columns if c.drift_detected]
        if not drifted:
            return "No significant data drift detected across all columns."

        parts = [f"Data drift detected in {len(drifted)} column(s):"]
        for c in drifted[:5]:
            parts.append(f"  - {c.message}")

        if avg_psi > 0:
            parts.append(f"Average PSI: {avg_psi:.4f}")

        return "\n".join(parts)
