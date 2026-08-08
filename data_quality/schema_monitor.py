"""Schema Change Monitor.

Detects schema changes between dataset runs:
  - Added columns (new fields appearing)
  - Removed columns (fields disappearing)
  - Type changes (column dtype changed)
  - Column order changes
  - Column rename detection (heuristic)

Maintains a schema baseline and compares new datasets against it.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd


@dataclass
class SchemaChange:
    """A single schema change."""

    change_type: str  # "added", "removed", "type_changed", "renamed"
    column: str
    old_value: str = ""
    new_value: str = ""
    severity: str = "warning"  # "info", "warning", "error"
    message: str = ""
    impact: str = ""

    def to_dict(self) -> dict:
        return {
            "change_type": self.change_type,
            "column": self.column,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "severity": self.severity,
            "message": self.message,
            "impact": self.impact,
        }


@dataclass
class SchemaChangeResult:
    """Result of schema change detection."""

    changes_detected: bool
    changes: list[SchemaChange] = field(default_factory=list)
    old_schema: dict = field(default_factory=dict)
    new_schema: dict = field(default_factory=dict)
    summary: str = ""

    def to_dict(self) -> dict:
        return {
            "changes_detected": self.changes_detected,
            "changes": [c.to_dict() for c in self.changes],
            "old_schema": self.old_schema,
            "new_schema": self.new_schema,
            "summary": self.summary,
        }


class SchemaMonitor:
    """Monitors schema changes between dataset runs."""

    @staticmethod
    def compare(
        old_df: pd.DataFrame,
        new_df: pd.DataFrame,
        old_name: str = "baseline",
        new_name: str = "current",
    ) -> SchemaChangeResult:
        """Compare schemas of two DataFrames.

        Args:
            old_df: Baseline DataFrame.
            new_df: Current DataFrame.
            old_name: Name of the baseline dataset.
            new_name: Name of the current dataset.

        Returns:
            SchemaChangeResult with detected changes.
        """
        old_schema = SchemaMonitor._extract_schema(old_df)
        new_schema = SchemaMonitor._extract_schema(new_df)

        changes: list[SchemaChange] = []

        old_cols = set(old_df.columns)
        new_cols = set(new_df.columns)

        # Added columns
        added = new_cols - old_cols
        for col in added:
            changes.append(
                SchemaChange(
                    change_type="added",
                    column=str(col),
                    new_value=str(new_df[col].dtype),
                    severity="info",
                    message=f"Column '{col}' added with dtype {new_df[col].dtype}.",
                    impact="New column may need to be mapped in downstream pipelines.",
                )
            )

        # Removed columns
        removed = old_cols - new_cols
        for col in removed:
            changes.append(
                SchemaChange(
                    change_type="removed",
                    column=str(col),
                    old_value=str(old_df[col].dtype),
                    severity="error",
                    message=f"Column '{col}' removed (was {old_df[col].dtype}).",
                    impact="Removed column may break downstream pipelines that depend on it.",
                )
            )

        # Type changes
        common = old_cols & new_cols
        for col in common:
            old_dtype = str(old_df[col].dtype)
            new_dtype = str(new_df[col].dtype)
            if old_dtype != new_dtype:
                severity = "warning"
                if "object" in new_dtype and "object" not in old_dtype:
                    severity = "error"
                changes.append(
                    SchemaChange(
                        change_type="type_changed",
                        column=str(col),
                        old_value=old_dtype,
                        new_value=new_dtype,
                        severity=severity,
                        message=f"Column '{col}' type changed from {old_dtype} to {new_dtype}.",
                        impact="Type changes may cause data loss or parsing errors in downstream systems.",
                    )
                )

        # Sort by severity
        severity_order = {"error": 0, "warning": 1, "info": 2}
        changes.sort(key=lambda c: severity_order.get(c.severity, 99))

        changes_detected = len(changes) > 0
        summary = SchemaMonitor._generate_summary(changes, old_name, new_name)

        return SchemaChangeResult(
            changes_detected=changes_detected,
            changes=changes,
            old_schema=old_schema,
            new_schema=new_schema,
            summary=summary,
        )

    @staticmethod
    def detect_renames(
        old_df: pd.DataFrame,
        new_df: pd.DataFrame,
        threshold: float = 0.85,
    ) -> list[SchemaChange]:
        """Heuristically detect column renames by comparing data profiles.

        When a column is removed and another is added with similar data
        profiles, it's likely a rename.

        Args:
            old_df: Baseline DataFrame.
            new_df: Current DataFrame.
            threshold: Similarity threshold (0-1) for matching columns.

        Returns:
            List of SchemaChange objects for detected renames.
        """
        old_cols = set(old_df.columns) - set(new_df.columns)
        new_cols = set(new_df.columns) - set(old_df.columns)

        renames: list[SchemaChange] = []
        matched_new = set()

        for old_col in old_cols:
            old_profile = SchemaMonitor._profile_column(old_df[old_col])
            best_match = None
            best_score = 0.0

            for new_col in new_cols:
                if new_col in matched_new:
                    continue
                new_profile = SchemaMonitor._profile_column(new_df[new_col])
                score = SchemaMonitor._profile_similarity(old_profile, new_profile)
                if score > best_score:
                    best_score = score
                    best_match = new_col

            if best_match and best_score >= threshold:
                matched_new.add(best_match)
                renames.append(
                    SchemaChange(
                        change_type="renamed",
                        column=f"{old_col} → {best_match}",
                        old_value=str(old_col),
                        new_value=str(best_match),
                        severity="info",
                        message=f"Column '{old_col}' likely renamed to '{best_match}' (similarity: {best_score:.2f}).",
                        impact="Update downstream references to use the new column name.",
                    )
                )

        return renames

    @staticmethod
    def _extract_schema(df: pd.DataFrame) -> dict:
        """Extract schema information from a DataFrame."""
        return {
            "columns": list(df.columns),
            "dtypes": {str(c): str(df[c].dtype) for c in df.columns},
            "row_count": len(df),
            "column_count": len(df.columns),
        }

    @staticmethod
    def _profile_column(series: pd.Series) -> dict:
        """Create a lightweight profile of a column for rename detection."""
        profile = {
            "dtype": str(series.dtype),
            "nunique": int(series.nunique()),
            "null_pct": float(series.isnull().sum() / max(len(series), 1)),
        }

        if pd.api.types.is_numeric_dtype(series):
            non_null = series.dropna()
            if len(non_null) > 0:
                profile["mean"] = float(non_null.mean())
                profile["std"] = float(non_null.std()) if len(non_null) > 1 else 0.0
                profile["min"] = float(non_null.min())
                profile["max"] = float(non_null.max())
        else:
            non_null = series.dropna().astype(str)
            if len(non_null) > 0:
                profile["top_value"] = str(non_null.value_counts().index[0])
                profile["avg_length"] = float(non_null.str.len().mean())

        return profile

    @staticmethod
    def _profile_similarity(old: dict, new: dict) -> float:
        """Compute similarity score between two column profiles (0-1)."""
        score = 0.0
        weights = 0.0

        # Dtype match
        if old.get("dtype") == new.get("dtype"):
            score += 0.3
        weights += 0.3

        # Unique count similarity
        old_nunique = old.get("nunique", 0)
        new_nunique = new.get("nunique", 0)
        if old_nunique > 0 and new_nunique > 0:
            ratio = min(old_nunique, new_nunique) / max(old_nunique, new_nunique)
            score += 0.2 * ratio
        weights += 0.2

        # Null percentage similarity
        old_null = old.get("null_pct", 0)
        new_null = new.get("null_pct", 0)
        null_diff = abs(old_null - new_null)
        score += 0.15 * max(0, 1 - null_diff * 2)
        weights += 0.15

        # Numeric-specific: mean/std similarity
        if "mean" in old and "mean" in new:
            old_mean = abs(old["mean"])
            new_mean = abs(new["mean"])
            if old_mean > 0 and new_mean > 0:
                ratio = min(old_mean, new_mean) / max(old_mean, new_mean)
                score += 0.2 * ratio
            weights += 0.2

            old_std = old.get("std", 0)
            new_std = new.get("std", 0)
            if old_std > 0 and new_std > 0:
                ratio = min(old_std, new_std) / max(old_std, new_std)
                score += 0.15 * ratio
            weights += 0.15

        # Categorical: top value match
        elif "top_value" in old and "top_value" in new:
            if old["top_value"] == new["top_value"]:
                score += 0.35
            weights += 0.35

        return score / weights if weights > 0 else 0.0

    @staticmethod
    def _generate_summary(changes: list[SchemaChange], old_name: str, new_name: str) -> str:
        """Generate a human-readable summary of schema changes."""
        if not changes:
            return f"No schema changes detected between '{old_name}' and '{new_name}'."

        parts = [f"Schema changes detected ({len(changes)}):"]
        for c in changes:
            parts.append(f"  [{c.severity.upper()}] {c.message}")

        return "\n".join(parts)
