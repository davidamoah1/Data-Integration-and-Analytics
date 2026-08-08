"""Automated Insight Generator.

Surfaces interesting patterns in the data without being asked:
  - Anomalies (outliers, sudden spikes/dips)
  - Trends (increasing/decreasing metrics over time)
  - Correlations (strong relationships between numeric columns)
  - Dominant categories (concentration risk)
  - Data quality issues (missing values, duplicates)
  - Notable distributions (skewed, bimodal)
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import pandas as pd


class InsightType(Enum):
    ANOMALY = "anomaly"
    TREND = "trend"
    CORRELATION = "correlation"
    DOMINANCE = "dominance"
    QUALITY = "quality"
    DISTRIBUTION = "distribution"
    COMPARISON = "comparison"


class Severity(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    POSITIVE = "positive"


@dataclass
class AutoInsight:
    """A single automated insight."""

    type: InsightType
    severity: Severity
    title: str
    description: str
    metric: str | None = None
    value: float | None = None
    recommendation: str = ""

    def to_dict(self) -> dict:
        return {
            "type": self.type.value,
            "severity": self.severity.value,
            "title": self.title,
            "description": self.description,
            "metric": self.metric,
            "value": self.value,
            "recommendation": self.recommendation,
        }


class InsightGenerator:
    """Automatically surfaces insights from a DataFrame."""

    @staticmethod
    def generate(
        df: pd.DataFrame,
        col_mapping: dict[str, str] | None = None,
        max_insights: int = 15,
    ) -> list[AutoInsight]:
        """Generate automated insights from the data.

        Args:
            df: The DataFrame to analyze.
            col_mapping: Mapping of column names to entity keys.
            max_insights: Maximum number of insights to return.

        Returns:
            List of AutoInsight objects sorted by severity.
        """
        col_mapping = col_mapping or {}
        insights: list[AutoInsight] = []

        # Run all detectors
        insights.extend(InsightGenerator._detect_anomalies(df, col_mapping))
        insights.extend(InsightGenerator._detect_trends(df, col_mapping))
        insights.extend(InsightGenerator._detect_correlations(df, col_mapping))
        insights.extend(InsightGenerator._detect_dominance(df, col_mapping))
        insights.extend(InsightGenerator._detect_quality_issues(df, col_mapping))
        insights.extend(InsightGenerator._detect_distribution_patterns(df, col_mapping))

        # Sort by severity (critical > warning > positive > info)
        severity_order = {
            Severity.CRITICAL: 0,
            Severity.WARNING: 1,
            Severity.POSITIVE: 2,
            Severity.INFO: 3,
        }
        insights.sort(key=lambda i: severity_order.get(i.severity, 99))

        return insights[:max_insights]

    @staticmethod
    def _detect_anomalies(df: pd.DataFrame, col_mapping: dict) -> list[AutoInsight]:
        """Detect outliers in numeric columns using IQR method."""
        insights = []
        numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]

        for col in numeric_cols:
            series = df[col].dropna()
            if len(series) < 10:
                continue

            q1 = series.quantile(0.25)
            q3 = series.quantile(0.75)
            iqr = q3 - q1
            if iqr == 0:
                continue

            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            outliers = series[(series < lower_bound) | (series > upper_bound)]
            outlier_pct = (len(outliers) / len(series) * 100) if len(series) > 0 else 0

            if len(outliers) > 0:
                entity = col_mapping.get(col, col)
                severity = Severity.WARNING if outlier_pct > 10 else Severity.INFO
                max_outlier = float(outliers.max()) if not outliers.empty else 0
                insights.append(
                    AutoInsight(
                        type=InsightType.ANOMALY,
                        severity=severity,
                        title=f"Outliers detected in {col.replace('_', ' ').title()}",
                        description=f"{len(outliers)} outliers ({outlier_pct:.1f}%) found in '{col}'. "
                        f"Values range from {float(outliers.min()):.2f} to {max_outlier:.2f}, "
                        f"outside the normal range [{lower_bound:.2f}, {upper_bound:.2f}].",
                        metric=col,
                        value=outlier_pct,
                        recommendation=f"Review {entity} outliers for data entry errors or exceptional cases.",
                    )
                )

        return insights

    @staticmethod
    def _detect_trends(df: pd.DataFrame, col_mapping: dict) -> list[AutoInsight]:
        """Detect trends in numeric columns over time."""
        insights = []
        date_col = None
        for c in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[c]):
                date_col = c
                break
        if date_col is None:
            for col, entity in col_mapping.items():
                if entity == "date" and col in df.columns:
                    date_col = col
                    break

        if date_col is None:
            return insights

        numeric_cols = [
            c for c in df.columns if pd.api.types.is_numeric_dtype(df[c]) and c != date_col
        ]

        df_sorted = df.copy()
        if not pd.api.types.is_datetime64_any_dtype(df_sorted[date_col]):
            df_sorted[date_col] = pd.to_datetime(df_sorted[date_col], errors="coerce")
        df_sorted = df_sorted.dropna(subset=[date_col]).sort_values(date_col)

        if len(df_sorted) < 4:
            return insights

        for col in numeric_cols:
            series = df_sorted[col].dropna()
            if len(series) < 4:
                continue

            # Split into halves and compare
            mid = len(series) // 2
            first_half = series.iloc[:mid]
            second_half = series.iloc[mid:]

            first_mean = float(first_half.mean())
            second_mean = float(second_half.mean())

            if first_mean == 0:
                continue

            change_pct = ((second_mean - first_mean) / abs(first_mean)) * 100

            if abs(change_pct) < 10:
                continue

            direction = "increasing" if change_pct > 0 else "decreasing"
            severity = Severity.POSITIVE if change_pct > 0 else Severity.WARNING
            entity = col_mapping.get(col, col)

            insights.append(
                AutoInsight(
                    type=InsightType.TREND,
                    severity=severity,
                    title=f"{col.replace('_', ' ').title()} is {direction}",
                    description=f"{col.replace('_', ' ').title()} shows a {abs(change_pct):.1f}% "
                    f"{direction} trend (from avg {first_mean:.2f} to {second_mean:.2f}).",
                    metric=col,
                    value=change_pct,
                    recommendation=f"Monitor {entity} trend and adjust strategy accordingly.",
                )
            )

        return insights

    @staticmethod
    def _detect_correlations(df: pd.DataFrame, col_mapping: dict) -> list[AutoInsight]:
        """Detect strong correlations between numeric columns."""
        insights = []
        numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]

        if len(numeric_cols) < 2:
            return insights

        try:
            corr = df[numeric_cols].corr()
        except Exception:
            return insights

        seen = set()
        for i, col1 in enumerate(numeric_cols):
            for j, col2 in enumerate(numeric_cols):
                if i >= j:
                    continue
                pair = tuple(sorted([col1, col2]))
                if pair in seen:
                    continue
                seen.add(pair)

                val = corr.loc[col1, col2]
                if pd.isna(val):
                    continue

                if abs(val) >= 0.7:
                    direction = "positive" if val > 0 else "negative"
                    strength = "strong" if abs(val) >= 0.8 else "moderate"
                    severity = Severity.INFO
                    insights.append(
                        AutoInsight(
                            type=InsightType.CORRELATION,
                            severity=severity,
                            title=f"{strength.title()} {direction} correlation: {col1} ↔ {col2}",
                            description=f"{col1.replace('_', ' ').title()} and {col2.replace('_', ' ').title()} "
                            f"have a {strength} {direction} correlation (r={val:.2f}). "
                            f"{'They tend to move together.' if val > 0 else 'They tend to move in opposite directions.'}",
                            metric=f"{col1} vs {col2}",
                            value=float(val),
                            recommendation=f"Use this correlation for predictive insights — "
                            f"{'when one increases, expect the other to increase too.' if val > 0 else 'when one increases, expect the other to decrease.'}",
                        )
                    )

        return insights

    @staticmethod
    def _detect_dominance(df: pd.DataFrame, col_mapping: dict) -> list[AutoInsight]:
        """Detect category dominance / concentration risk."""
        insights = []
        categorical_cols = [
            c for c in df.columns if df[c].dtype == "object" and df[c].nunique() < 50
        ]

        for col in categorical_cols:
            value_counts = df[col].value_counts()
            if value_counts.empty:
                continue

            top_pct = value_counts.iloc[0] / len(df) * 100
            top_value = value_counts.index[0]

            if top_pct > 60:
                entity = col_mapping.get(col, col)
                severity = Severity.WARNING if top_pct > 80 else Severity.INFO
                insights.append(
                    AutoInsight(
                        type=InsightType.DOMINANCE,
                        severity=severity,
                        title=f"High concentration in {col.replace('_', ' ').title()}",
                        description=f"'{top_value}' accounts for {top_pct:.1f}% of all records in '{col}'. "
                        f"This represents concentration risk.",
                        metric=col,
                        value=top_pct,
                        recommendation=f"Diversify {entity} to reduce dependency on '{top_value}'.",
                    )
                )

        return insights

    @staticmethod
    def _detect_quality_issues(df: pd.DataFrame, col_mapping: dict) -> list[AutoInsight]:
        """Detect data quality issues."""
        insights = []

        # Missing values
        for col in df.columns:
            missing = df[col].isna().sum()
            if missing > 0:
                missing_pct = missing / len(df) * 100
                if missing_pct > 20:
                    entity = col_mapping.get(col, col)
                    severity = Severity.CRITICAL if missing_pct > 50 else Severity.WARNING
                    insights.append(
                        AutoInsight(
                            type=InsightType.QUALITY,
                            severity=severity,
                            title=f"High missing rate in {col.replace('_', ' ').title()}",
                            description=f"'{col}' has {missing} missing values ({missing_pct:.1f}%). "
                            f"This may affect analysis reliability.",
                            metric=col,
                            value=missing_pct,
                            recommendation=f"Address missing {entity} values through imputation or data collection.",
                        )
                    )

        # Duplicates
        dup_count = df.duplicated().sum()
        if dup_count > 0:
            dup_pct = dup_count / len(df) * 100
            if dup_pct > 5:
                insights.append(
                    AutoInsight(
                        type=InsightType.QUALITY,
                        severity=Severity.WARNING,
                        title=f"{dup_count} duplicate rows detected",
                        description=f"{dup_pct:.1f}% of rows are exact duplicates, which may skew analysis.",
                        value=dup_pct,
                        recommendation="Remove duplicate rows before analysis.",
                    )
                )

        return insights

    @staticmethod
    def _detect_distribution_patterns(df: pd.DataFrame, col_mapping: dict) -> list[AutoInsight]:
        """Detect notable distribution patterns in numeric columns."""
        insights = []
        numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]

        for col in numeric_cols:
            series = df[col].dropna()
            if len(series) < 10:
                continue

            mean = float(series.mean())
            median = float(series.median())
            std = float(series.std())

            if std == 0 or mean == 0:
                continue

            # Skewness check
            skew = (mean - median) / std if std != 0 else 0
            if abs(skew) > 0.5:
                direction = "right" if skew > 0 else "left"
                severity = Severity.INFO
                insights.append(
                    AutoInsight(
                        type=InsightType.DISTRIBUTION,
                        severity=severity,
                        title=f"{col.replace('_', ' ').title()} is {direction}-skewed",
                        description=f"'{col}' has a {direction} skew (mean={mean:.2f}, median={median:.2f}). "
                        f"{'Most values are low with a few high outliers.' if skew > 0 else 'Most values are high with a few low outliers.'}",
                        metric=col,
                        value=skew,
                        recommendation=f"Consider log transformation for {col} if using linear models.",
                    )
                )

        return insights
