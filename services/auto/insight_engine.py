"""Automatic Insight Engine.

Generates insights from computed results â€” not fabricated by AI.
Every insight references real computed data.

Priorities:
  1. Major trends (significant increases/decreases over time)
  2. Outliers (statistical anomalies)
  3. Significant correlations (strong relationships)
  4. Dominant categories (concentration risk)
  5. Data quality issues
  6. Distribution patterns (skewness, bimodality)
"""

from __future__ import annotations

import logging

import pandas as pd

from services.auto.analysis_engine import DatasetUnderstanding, SemanticRole
from services.auto.chart_specification import InsightSpecification

logger = logging.getLogger(__name__)


class AutomaticInsightEngine:
    """Generates data-driven insights from computed results."""

    MAX_INSIGHTS = 10

    def generate_insights(
        self,
        df: pd.DataFrame,
        understanding: DatasetUnderstanding,
    ) -> list[InsightSpecification]:
        """Generate insights from the dataset.

        Args:
            df: The dataset DataFrame.
            understanding: DatasetUnderstanding from AutomaticAnalysisEngine.

        Returns:
            List of InsightSpecification objects sorted by priority.
        """
        insights: list[InsightSpecification] = []

        # Run all detectors
        insights.extend(self._detect_trends(df, understanding))
        insights.extend(self._detect_outliers(df, understanding))
        insights.extend(self._detect_correlations(df, understanding))
        insights.extend(self._detect_dominance(df, understanding))
        insights.extend(self._detect_quality_issues(df, understanding))
        insights.extend(self._detect_distribution_patterns(df, understanding))

        # Sort by priority (higher first), then by severity
        severity_priority = {"critical": 3, "warning": 2, "positive": 1, "info": 0}
        insights.sort(
            key=lambda i: (i.priority, severity_priority.get(i.severity, 0)),
            reverse=True,
        )

        # Assign order
        for i, insight in enumerate(insights):
            insight.order = i

        return insights[: self.MAX_INSIGHTS]

    # â”€â”€ Detectors â”€â”€

    def _detect_trends(
        self,
        df: pd.DataFrame,
        understanding: DatasetUnderstanding,
    ) -> list[InsightSpecification]:
        """Detect significant trends over time."""
        insights = []
        if not understanding.time_columns or not understanding.measures:
            return insights

        time_col = understanding.time_columns[0]
        if time_col not in df.columns:
            return insights

        try:
            if pd.api.types.is_datetime64_any_dtype(df[time_col]):
                dates = df[time_col]
            else:
                dates = pd.to_datetime(df[time_col], errors="coerce")

            df_temp = df.copy()
            df_temp["_period"] = dates.dt.to_period("M")
            monthly = (
                df_temp.groupby("_period")[
                    [
                        m
                        for m in understanding.measures
                        if m in df_temp.columns and pd.api.types.is_numeric_dtype(df_temp[m])
                    ][:3]
                ]
                .sum()
                .sort_index()
            )

            if len(monthly) < 3:
                return insights

            for metric in monthly.columns:
                series = monthly[metric]
                first_val = float(series.iloc[0])
                last_val = float(series.iloc[-1])

                if first_val == 0:
                    continue

                change_pct = ((last_val - first_val) / abs(first_val)) * 100

                if abs(change_pct) < 5:
                    continue

                direction = "increased" if change_pct > 0 else "decreased"
                severity = "positive" if change_pct > 0 else "warning"
                priority = 8 if abs(change_pct) > 50 else 5 if abs(change_pct) > 20 else 3

                insights.append(
                    InsightSpecification(
                        title=f"{self._label(metric)} {direction} by {abs(change_pct):.1f}%",
                        description=f"From {series.index[0]} to {series.index[-1]}, {self._label(metric)} {direction} from {first_val:,.0f} to {last_val:,.0f} ({change_pct:+.1f}%).",
                        severity=severity,
                        insight_type="trend",
                        metric=metric,
                        value=change_pct,
                        recommendation=(
                            f"Investigate the factors driving this {'growth' if change_pct > 0 else 'decline'} and {'sustain positive drivers' if change_pct > 0 else 'address root causes'}."
                        ),
                        source_data=f"monthly_trend:{metric}",
                        priority=priority,
                    )
                )
        except Exception:
            logger.debug("Trend detection failed", exc_info=True)

        return insights

    def _detect_outliers(
        self,
        df: pd.DataFrame,
        understanding: DatasetUnderstanding,
    ) -> list[InsightSpecification]:
        """Detect statistical outliers in numeric columns."""
        insights = []

        for col_u in understanding.columns:
            if not col_u.is_numeric or col_u.semantic_role == SemanticRole.IDENTIFIER:
                continue
            if col_u.name not in df.columns:
                continue

            stats = col_u.stats
            outlier_count = stats.get("outlier_count", 0)
            if outlier_count == 0:
                continue

            outlier_pct = outlier_count / max(understanding.row_count, 1) * 100
            if outlier_pct < 1:
                continue

            severity = "warning" if outlier_pct > 10 else "info"
            priority = 6 if outlier_pct > 15 else 3

            insights.append(
                InsightSpecification(
                    title=f"{outlier_count} outliers detected in {self._label(col_u.name)}",
                    description=f"{outlier_pct:.1f}% of {self._label(col_u.name)} values are statistical outliers (beyond 1.5Ã—IQR). Values range from {stats.get('min', 0):,.2f} to {stats.get('max', 0):,.2f}.",
                    severity=severity,
                    insight_type="anomaly",
                    metric=col_u.name,
                    value=float(outlier_count),
                    recommendation="Review outlier values to determine if they are data errors or genuine extreme values. Consider winsorizing or investigating root causes.",
                    source_data=f"outlier_detection:{col_u.name}",
                    priority=priority,
                )
            )

        return insights

    def _detect_correlations(
        self,
        df: pd.DataFrame,
        understanding: DatasetUnderstanding,
    ) -> list[InsightSpecification]:
        """Detect significant correlations between numeric variables."""
        insights = []

        for corr in understanding.correlations:
            if corr["strength"] != "strong":
                continue

            insights.append(
                InsightSpecification(
                    title=f"Strong {corr['direction']} correlation between {self._label(corr['column_1'])} and {self._label(corr['column_2'])}",
                    description=f"{self._label(corr['column_1'])} and {self._label(corr['column_2'])} have a {corr['direction']} correlation of r={corr['correlation']:.2f}. This means they tend to {'increase' if corr['direction'] == 'positive' else 'move in opposite directions'} together.",
                    severity="info",
                    insight_type="correlation",
                    metric=f"{corr['column_1']} vs {corr['column_2']}",
                    value=corr["correlation"],
                    recommendation=f"Consider using {self._label(corr['column_1'])} to {'predict' if corr['direction'] == 'positive' else 'understand'} {self._label(corr['column_2'])} and vice versa.",
                    source_data=f"correlation:{corr['column_1']}:{corr['column_2']}",
                    priority=5,
                )
            )

        return insights

    def _detect_dominance(
        self,
        df: pd.DataFrame,
        understanding: DatasetUnderstanding,
    ) -> list[InsightSpecification]:
        """Detect dominant categories (concentration risk)."""
        insights = []

        for col_u in understanding.columns:
            if col_u.semantic_role not in (SemanticRole.CATEGORY, SemanticRole.GEOGRAPHY):
                continue
            if col_u.name not in df.columns:
                continue

            stats = col_u.stats
            top_pct = stats.get("top_value_pct", 0)

            if top_pct > 50:
                severity = "warning"
                priority = 5
                insights.append(
                    InsightSpecification(
                        title=f"{self._label(col_u.name)} is dominated by '{stats.get('top_value', '')}' ({top_pct:.1f}%)",
                        description=f"A single value ('{stats.get('top_value', '')}') accounts for {top_pct:.1f}% of all {self._label(col_u.name)} records. This indicates high concentration.",
                        severity=severity,
                        insight_type="dominance",
                        metric=col_u.name,
                        value=top_pct,
                        recommendation="Consider whether this concentration is expected or represents a risk. Diversification may be needed if this is a business metric.",
                        source_data=f"dominance:{col_u.name}",
                        priority=priority,
                    )
                )

        return insights

    def _detect_quality_issues(
        self,
        df: pd.DataFrame,
        understanding: DatasetUnderstanding,
    ) -> list[InsightSpecification]:
        """Detect data quality issues that affect analysis."""
        insights = []

        for warning in understanding.quality_warnings:
            insights.append(
                InsightSpecification(
                    title=warning,
                    description=warning,
                    severity="warning",
                    insight_type="quality",
                    recommendation="Address data quality issues before drawing conclusions from affected columns.",
                    source_data="quality_check",
                    priority=2,
                )
            )

        return insights

    def _detect_distribution_patterns(
        self,
        df: pd.DataFrame,
        understanding: DatasetUnderstanding,
    ) -> list[InsightSpecification]:
        """Detect notable distribution patterns (skewness, bimodality)."""
        insights = []

        for col_u in understanding.columns:
            if not col_u.is_numeric or col_u.semantic_role == SemanticRole.IDENTIFIER:
                continue
            if col_u.name not in df.columns:
                continue

            stats = col_u.stats
            mean = stats.get("mean", 0)
            median = stats.get("median", 0)
            std = stats.get("std", 0)

            if std == 0 or mean == 0:
                continue

            # Check for skewness (mean != median)
            skew_ratio = (mean - median) / std if std > 0 else 0
            if abs(skew_ratio) > 0.5:
                direction = (
                    "right-skewed (mean > median)"
                    if skew_ratio > 0
                    else "left-skewed (mean < median)"
                )
                insights.append(
                    InsightSpecification(
                        title=f"{self._label(col_u.name)} distribution is {direction}",
                        description=f"The distribution of {self._label(col_u.name)} is {direction} (mean={mean:,.2f}, median={median:,.2f}, std={std:,.2f}). This means the data is not symmetrically distributed.",
                        severity="info",
                        insight_type="distribution",
                        metric=col_u.name,
                        value=skew_ratio,
                        recommendation=f"Use median rather than mean for {self._label(col_u.name)} as it better represents the typical value in skewed distributions.",
                        source_data=f"distribution:{col_u.name}",
                        priority=2,
                    )
                )

        return insights

    # â”€â”€ Helpers â”€â”€

    @staticmethod
    def _label(col: str) -> str:
        return col.replace("_", " ").title()
