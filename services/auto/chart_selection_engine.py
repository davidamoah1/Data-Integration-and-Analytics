"""Intelligent Chart Selection Engine.

Determines which visualizations are appropriate for a dataset using
deterministic rules first, then AI/semantic reasoning where appropriate.

Rules:
  TIME + NUMERIC       â†’ line chart
  CATEGORY + NUMERIC   â†’ bar chart
  CATEGORY + PROPORTIONâ†’ pie/donut (small category count only)
  TWO NUMERIC          â†’ scatter plot
  DISTRIBUTION         â†’ histogram, box plot
  CORRELATION          â†’ heatmap
  RANKING              â†’ sorted bar chart
  GEOGRAPHIC           â†’ map (only when confidently detected)

Every chart receives an importance score.  Poor chart choices are
actively rejected.  Duplicate charts are detected and removed.
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from services.auto.analysis_engine import (
    DatasetUnderstanding,
)
from services.auto.chart_specification import ChartSpecification

logger = logging.getLogger(__name__)


class IntelligentChartSelectionEngine:
    """Selects, scores, deduplicates, and validates chart recommendations.

    This engine produces canonical ChartSpecification objects that are
    the single source of truth for dashboard, report, and PPTX.
    """

    # Configurable limits
    MAX_CANDIDATE_CHARTS = 30
    MAX_DASHBOARD_CHARTS = 12
    MAX_PRESENTATION_CHARTS = 10

    # Pie chart limits
    PIE_MAX_CATEGORIES = 8

    # Bar chart limits
    BAR_MAX_CATEGORIES_READABLE = 25

    def select_charts(
        self,
        df: pd.DataFrame,
        understanding: DatasetUnderstanding,
        max_charts: int | None = None,
    ) -> list[ChartSpecification]:
        """Select appropriate charts for a dataset.

        Args:
            df: The dataset DataFrame.
            understanding: DatasetUnderstanding from AutomaticAnalysisEngine.
            max_charts: Maximum charts to return (default: MAX_DASHBOARD_CHARTS).

        Returns:
            List of ChartSpecification objects, sorted by importance score.
        """
        max_charts = max_charts or self.MAX_DASHBOARD_CHARTS
        candidates: list[ChartSpecification] = []
        order = 0

        measures = [m for m in understanding.measures if m in df.columns]
        dimensions = [d for d in understanding.dimensions if d in df.columns]
        time_cols = [t for t in understanding.time_columns if t in df.columns]
        geo_cols = [g for g in understanding.geographic_columns if g in df.columns]

        # Filter out high-missing-percentage columns from important charts
        good_measures = self._filter_by_quality(df, measures, understanding)
        good_dimensions = self._filter_by_quality(df, dimensions, understanding)

        # â”€â”€ 1. TIME + NUMERIC â†’ Line chart â”€â”€
        for time_col in time_cols[:2]:
            for metric_col in good_measures[:3]:
                chart = self._make_line_chart(df, time_col, metric_col, understanding, order)
                if chart:
                    candidates.append(chart)
                    order += 1

        # â”€â”€ 2. CATEGORY + NUMERIC â†’ Bar chart â”€â”€
        for dim_col in good_dimensions[:4]:
            for metric_col in good_measures[:3]:
                if dim_col == metric_col:
                    continue
                chart = self._make_bar_chart(df, dim_col, metric_col, understanding, order)
                if chart:
                    candidates.append(chart)
                    order += 1

        # â”€â”€ 3. CATEGORY + PROPORTION â†’ Pie/donut (small categories only) â”€â”€
        for dim_col in good_dimensions[:3]:
            chart = self._make_pie_chart(df, dim_col, understanding, order)
            if chart:
                candidates.append(chart)
                order += 1

        # â”€â”€ 4. TWO NUMERIC â†’ Scatter plot â”€â”€
        if len(good_measures) >= 2:
            for i in range(min(len(good_measures) - 1, 3)):
                chart = self._make_scatter_plot(
                    df, good_measures[i], good_measures[i + 1], understanding, order
                )
                if chart:
                    candidates.append(chart)
                    order += 1

        # â”€â”€ 5. DISTRIBUTION â†’ Histogram â”€â”€
        for metric_col in good_measures[:3]:
            chart = self._make_histogram(df, metric_col, understanding, order)
            if chart:
                candidates.append(chart)
                order += 1

        # â”€â”€ 6. CORRELATION â†’ Heatmap (3+ numeric variables) â”€â”€
        if len(good_measures) >= 3:
            chart = self._make_correlation_heatmap(df, good_measures, understanding, order)
            if chart:
                candidates.append(chart)
                order += 1

        # â”€â”€ 7. RANKING â†’ Sorted bar chart â”€â”€
        for dim_col in good_dimensions[:2]:
            for metric_col in good_measures[:2]:
                chart = self._make_ranking_chart(df, dim_col, metric_col, understanding, order)
                if chart:
                    candidates.append(chart)
                    order += 1

        # â”€â”€ 8. GEOGRAPHIC â†’ Map (only when confidently detected) â”€â”€
        if geo_cols:
            for geo_col in geo_cols[:1]:
                for metric_col in good_measures[:1]:
                    chart = self._make_geo_map(df, geo_col, metric_col, understanding, order)
                    if chart:
                        candidates.append(chart)
                        order += 1

        # â”€â”€ 9. AREA CHART (time + numeric, emphasizing volume) â”€â”€
        for time_col in time_cols[:1]:
            for metric_col in good_measures[:2]:
                chart = self._make_area_chart(df, time_col, metric_col, understanding, order)
                if chart:
                    candidates.append(chart)
                    order += 1

        # â”€â”€ 10. BOX PLOT (distribution + group comparison) â”€â”€
        for metric_col in good_measures[:2]:
            # Grouped box plot if a dimension exists
            if good_dimensions:
                chart = self._make_box_plot(
                    df, metric_col, good_dimensions[0], understanding, order
                )
            else:
                chart = self._make_box_plot(df, metric_col, None, understanding, order)
            if chart:
                candidates.append(chart)
                order += 1

        # â”€â”€ 11. TREEMAP (many categories + measure) â”€â”€
        for dim_col in good_dimensions[:2]:
            for metric_col in good_measures[:1]:
                chart = self._make_treemap(df, dim_col, metric_col, understanding, order)
                if chart:
                    candidates.append(chart)
                    order += 1

        # Limit candidates
        candidates = candidates[: self.MAX_CANDIDATE_CHARTS]

        # Score all candidates
        for chart in candidates:
            chart.importance_score = self._score_chart(chart, df, understanding)

        # Deduplicate
        candidates = self._deduplicate(candidates)

        # Sort by importance score (descending)
        candidates.sort(key=lambda c: c.importance_score, reverse=True)

        # Ensure chart type diversity â€” reserve slots for underrepresented types
        candidates = self._ensure_diversity(candidates, max_charts)

        # Re-order after filtering
        for i, chart in enumerate(candidates):
            chart.order = i

        return candidates

    # â”€â”€ Chart factories â”€â”€

    def _make_line_chart(
        self,
        df: pd.DataFrame,
        time_col: str,
        metric_col: str,
        understanding: DatasetUnderstanding,
        order: int,
    ) -> ChartSpecification | None:
        """Line chart for time series: TIME + NUMERIC."""
        # Validate
        if not pd.api.types.is_numeric_dtype(df[metric_col]):
            return None

        # Compute aggregated data
        try:
            if pd.api.types.is_datetime64_any_dtype(df[time_col]):
                grouped = df.groupby(df[time_col].dt.to_period("M"))[metric_col].sum()
                x_labels = [str(p) for p in grouped.index]
            else:
                parsed = pd.to_datetime(df[time_col], errors="coerce")
                if parsed.notna().mean() < 0.8:
                    return None
                grouped = df.groupby(parsed.dt.to_period("M"))[metric_col].sum()
                x_labels = [str(p) for p in grouped.index]
        except Exception:
            return None

        if len(grouped) < 2:
            return None

        data = [{"x": x, "y": float(y)} for x, y in zip(x_labels, grouped.values, strict=False)]

        # Generate meaningful title
        date_range = f"{x_labels[0]} to {x_labels[-1]}" if len(x_labels) >= 2 else ""
        title = f"{self._label(metric_col)} Over Time"
        if date_range:
            title += f" â€” {date_range}"

        return ChartSpecification(
            chart_type="line_chart",
            title=title,
            description=f"Monthly trend of {self._label(metric_col)} over {self._label(time_col)}",
            x_axis=time_col,
            y_axis=metric_col,
            aggregation="sum",
            source_columns=[time_col, metric_col],
            data=data,
            section="primary_charts",
            width=12,
            height=350,
            order=order,
            confidence=0.9,
            reason=f"We selected a line chart because your dataset contains a time-based column ({self._label(time_col)}) and a numerical measure ({self._label(metric_col)}). Line charts are the best way to show how a value changes over time.",
            source_analysis="time_series",
            dataset_hash=understanding.dataset_hash,
        )

    def _make_bar_chart(
        self,
        df: pd.DataFrame,
        dim_col: str,
        metric_col: str,
        understanding: DatasetUnderstanding,
        order: int,
    ) -> ChartSpecification | None:
        """Bar chart for category comparison: CATEGORY + NUMERIC."""
        if not pd.api.types.is_numeric_dtype(df[metric_col]):
            return None

        cardinality = df[dim_col].nunique()
        if cardinality < 2:
            return None
        if cardinality > self.BAR_MAX_CATEGORIES_READABLE:
            # Use horizontal bar for many categories
            chart_type = "horizontal_bar"
        else:
            chart_type = "bar_chart"

        # Compute aggregated data
        grouped = df.groupby(dim_col, dropna=False)[metric_col].sum().sort_values(ascending=False)
        if len(grouped) > 15:
            grouped = grouped.head(15)

        data = [{"x": str(k), "y": float(v)} for k, v in grouped.items()]

        title = f"{self._label(metric_col)} by {self._label(dim_col)}"

        return ChartSpecification(
            chart_type=chart_type,
            title=title,
            description=f"Comparison of {self._label(metric_col)} across {self._label(dim_col)} categories",
            x_axis=dim_col,
            y_axis=metric_col,
            aggregation="sum",
            source_columns=[dim_col, metric_col],
            data=data,
            section="primary_charts",
            width=6,
            height=300,
            order=order,
            confidence=0.85,
            reason=f"We selected a bar chart because your dataset contains categorical data ({self._label(dim_col)}) and a numerical measure ({self._label(metric_col)}). Bar charts clearly compare values across categories.",
            source_analysis="category_comparison",
            dataset_hash=understanding.dataset_hash,
        )

    def _make_pie_chart(
        self,
        df: pd.DataFrame,
        dim_col: str,
        understanding: DatasetUnderstanding,
        order: int,
    ) -> ChartSpecification | None:
        """Pie/donut chart for composition: CATEGORY + PROPORTION."""
        cardinality = df[dim_col].nunique()

        # Reject if too many categories
        if cardinality < 2:
            return None
        if cardinality > self.PIE_MAX_CATEGORIES:
            return None

        # Compute proportions
        counts = df[dim_col].value_counts()
        total = counts.sum()
        data = [
            {"x": str(k), "y": int(v), "pct": round(float(v / total * 100), 1)}
            for k, v in counts.items()
        ]

        title = f"{self._label(dim_col)} Distribution"

        return ChartSpecification(
            chart_type="donut_chart",
            title=title,
            description=f"Distribution of {self._label(dim_col)} ({cardinality} segments)",
            x_axis=dim_col,
            aggregation="count",
            source_columns=[dim_col],
            data=data,
            section="supporting_charts",
            width=4,
            height=300,
            order=order,
            confidence=0.75,
            reason=f"We selected a donut chart because {self._label(dim_col)} has only {cardinality} categories, making a part-to-whole visualization easy to read.",
            source_analysis="composition",
            dataset_hash=understanding.dataset_hash,
        )

    def _make_scatter_plot(
        self,
        df: pd.DataFrame,
        x_col: str,
        y_col: str,
        understanding: DatasetUnderstanding,
        order: int,
    ) -> ChartSpecification | None:
        """Scatter plot for two numeric variables."""
        if not pd.api.types.is_numeric_dtype(df[x_col]) or not pd.api.types.is_numeric_dtype(
            df[y_col]
        ):
            return None

        # Compute correlation
        corr = df[[x_col, y_col]].corr().iloc[0, 1]
        if pd.isna(corr):
            return None

        # Sample data for visualization (limit to 200 points)
        sample = df[[x_col, y_col]].dropna().head(200)
        data = [{"x": float(r[x_col]), "y": float(r[y_col])} for _, r in sample.iterrows()]

        strength = "weak" if abs(corr) < 0.3 else "moderate" if abs(corr) < 0.7 else "strong"
        direction = "positive" if corr > 0 else "negative"

        title = f"{self._label(x_col)} vs {self._label(y_col)}"

        return ChartSpecification(
            chart_type="scatter_plot",
            title=title,
            description=f"Relationship between {self._label(x_col)} and {self._label(y_col)} ({strength} {direction} correlation: r={corr:.2f})",
            x_axis=x_col,
            y_axis=y_col,
            source_columns=[x_col, y_col],
            data=data,
            section="supporting_charts",
            width=6,
            height=300,
            order=order,
            confidence=0.7,
            reason=f"We selected a scatter plot because both {self._label(x_col)} and {self._label(y_col)} are numerical variables. Scatter plots reveal relationships and correlations between two measures. The correlation is {strength} {direction} (r={corr:.2f}).",
            source_analysis="correlation",
            dataset_hash=understanding.dataset_hash,
        )

    def _make_histogram(
        self,
        df: pd.DataFrame,
        metric_col: str,
        understanding: DatasetUnderstanding,
        order: int,
    ) -> ChartSpecification | None:
        """Histogram for distribution analysis."""
        if not pd.api.types.is_numeric_dtype(df[metric_col]):
            return None

        vals = df[metric_col].dropna()
        if len(vals) < 5 or vals.nunique() < 5:
            return None

        # Compute histogram bins
        n_bins = min(20, max(5, int(np.sqrt(len(vals)))))
        counts, bin_edges = np.histogram(vals, bins=n_bins)

        data = [
            {"x": f"{bin_edges[i]:.1f}-{bin_edges[i+1]:.1f}", "y": int(counts[i])}
            for i in range(len(counts))
        ]

        title = f"{self._label(metric_col)} Distribution"

        return ChartSpecification(
            chart_type="histogram",
            title=title,
            description=f"Distribution of {self._label(metric_col)} values across {n_bins} bins",
            x_axis=metric_col,
            aggregation="count",
            source_columns=[metric_col],
            data=data,
            section="supporting_charts",
            width=6,
            height=300,
            order=order,
            confidence=0.7,
            reason=f"We selected a histogram to show how {self._label(metric_col)} values are distributed. This helps identify skewness, outliers, and the overall shape of the data.",
            source_analysis="distribution",
            dataset_hash=understanding.dataset_hash,
        )

    def _make_correlation_heatmap(
        self,
        df: pd.DataFrame,
        measures: list[str],
        understanding: DatasetUnderstanding,
        order: int,
    ) -> ChartSpecification | None:
        """Correlation heatmap for 3+ numeric variables."""
        numeric_measures = [m for m in measures if pd.api.types.is_numeric_dtype(df[m])]
        if len(numeric_measures) < 3:
            return None

        corr_matrix = df[numeric_measures].corr()
        data = []
        for _i, col1 in enumerate(numeric_measures):
            for _j, col2 in enumerate(numeric_measures):
                val = corr_matrix.loc[col1, col2]
                if not pd.isna(val):
                    data.append({"x": col1, "y": col2, "value": round(float(val), 2)})

        title = "Correlation Heatmap"

        return ChartSpecification(
            chart_type="heatmap",
            title=title,
            description=f"Correlation matrix of {len(numeric_measures)} numerical variables",
            x_axis=numeric_measures[0],
            y_axis=numeric_measures[1] if len(numeric_measures) > 1 else None,
            z_axis=numeric_measures[0],
            source_columns=numeric_measures,
            data=data,
            section="supporting_charts",
            width=6,
            height=350,
            order=order,
            confidence=0.65,
            reason=f"We selected a correlation heatmap because your dataset has {len(numeric_measures)} numerical variables. Heatmaps reveal which variables are related, helping identify redundant metrics and important relationships.",
            source_analysis="correlation_matrix",
            dataset_hash=understanding.dataset_hash,
        )

    def _make_ranking_chart(
        self,
        df: pd.DataFrame,
        dim_col: str,
        metric_col: str,
        understanding: DatasetUnderstanding,
        order: int,
    ) -> ChartSpecification | None:
        """Sorted bar chart for ranking: top N entities."""
        if not pd.api.types.is_numeric_dtype(df[metric_col]):
            return None

        grouped = df.groupby(dim_col, dropna=False)[metric_col].sum().sort_values(ascending=False)
        if len(grouped) < 3:
            return None

        top_n = min(10, len(grouped))
        grouped = grouped.head(top_n)

        data = [{"x": str(k), "y": float(v)} for k, v in grouped.items()]

        title = f"Top {top_n} {self._label(dim_col)} by {self._label(metric_col)}"

        return ChartSpecification(
            chart_type="horizontal_bar",
            title=title,
            description=f"Ranked {self._label(dim_col)} by {self._label(metric_col)} â€” top {top_n}",
            x_axis=dim_col,
            y_axis=metric_col,
            aggregation="sum",
            source_columns=[dim_col, metric_col],
            data=data,
            section="supporting_charts",
            width=6,
            height=300,
            order=order,
            confidence=0.7,
            reason=f"We selected a sorted horizontal bar chart to rank {self._label(dim_col)} by {self._label(metric_col)}. This makes it easy to see which categories perform best and worst.",
            source_analysis="ranking",
            dataset_hash=understanding.dataset_hash,
        )

    def _make_geo_map(
        self,
        df: pd.DataFrame,
        geo_col: str,
        metric_col: str,
        understanding: DatasetUnderstanding,
        order: int,
    ) -> ChartSpecification | None:
        """Geographic map (only when confidently detected)."""
        if not pd.api.types.is_numeric_dtype(df[metric_col]):
            return None

        grouped = df.groupby(geo_col, dropna=False)[metric_col].sum().sort_values(ascending=False)
        data = [{"x": str(k), "y": float(v)} for k, v in grouped.items()]

        title = f"{self._label(metric_col)} by {self._label(geo_col)}"

        return ChartSpecification(
            chart_type="geo_map",
            title=title,
            description=f"Geographic distribution of {self._label(metric_col)} by {self._label(geo_col)}",
            x_axis=geo_col,
            y_axis=metric_col,
            aggregation="sum",
            source_columns=[geo_col, metric_col],
            data=data,
            section="primary_charts",
            width=12,
            height=400,
            order=order,
            confidence=0.8,
            reason=f"We selected a map visualization because {self._label(geo_col)} contains geographic information. Maps show spatial patterns that bar charts cannot reveal.",
            source_analysis="geographic",
            dataset_hash=understanding.dataset_hash,
        )

    def _make_area_chart(
        self,
        df: pd.DataFrame,
        time_col: str,
        metric_col: str,
        understanding: DatasetUnderstanding,
        order: int,
    ) -> ChartSpecification | None:
        """Area chart for emphasizing volume/trend over time."""
        if not pd.api.types.is_numeric_dtype(df[metric_col]):
            return None

        try:
            if pd.api.types.is_datetime64_any_dtype(df[time_col]):
                grouped = df.groupby(df[time_col].dt.to_period("M"))[metric_col].sum()
                x_labels = [str(p) for p in grouped.index]
            else:
                parsed = pd.to_datetime(df[time_col], errors="coerce")
                if parsed.notna().mean() < 0.8:
                    return None
                grouped = df.groupby(parsed.dt.to_period("M"))[metric_col].sum()
                x_labels = [str(p) for p in grouped.index]
        except Exception:
            return None

        if len(grouped) < 2:
            return None

        data = [{"x": x, "y": float(y)} for x, y in zip(x_labels, grouped.values, strict=False)]

        return ChartSpecification(
            chart_type="area_chart",
            title=f"{self._label(metric_col)} Volume Over Time",
            description=f"Cumulative trend of {self._label(metric_col)} over {self._label(time_col)}",
            x_axis=time_col,
            y_axis=metric_col,
            aggregation="sum",
            source_columns=[time_col, metric_col],
            data=data,
            section="supporting_charts",
            width=6,
            height=300,
            order=order,
            confidence=0.78,
            reason=f"We selected an area chart to emphasize the volume of {self._label(metric_col)} over time. Area charts highlight magnitude and trend direction.",
            source_analysis="time_series_volume",
            dataset_hash=understanding.dataset_hash,
        )

    def _make_box_plot(
        self,
        df: pd.DataFrame,
        metric_col: str,
        group_col: str | None,
        understanding: DatasetUnderstanding,
        order: int,
    ) -> ChartSpecification | None:
        """Box plot for distribution/outlier/group comparison."""
        if not pd.api.types.is_numeric_dtype(df[metric_col]):
            return None

        if group_col:
            if df[group_col].nunique() > 15:
                return None
            data = []
            for cat in df[group_col].dropna().unique():
                vals = df[df[group_col] == cat][metric_col].dropna()
                if len(vals) < 5:
                    continue
                q1 = float(vals.quantile(0.25))
                q2 = float(vals.median())
                q3 = float(vals.quantile(0.75))
                iqr = q3 - q1
                lower = q1 - 1.5 * iqr
                upper = q3 + 1.5 * iqr
                outliers = vals[(vals < lower) | (vals > upper)]
                data.append(
                    {
                        "x": str(cat),
                        "min": float(vals.min()),
                        "q1": q1,
                        "median": q2,
                        "q3": q3,
                        "max": float(vals.max()),
                        "outliers": [float(v) for v in outliers.head(10)],
                    }
                )
            title = f"{self._label(metric_col)} Distribution by {self._label(group_col)}"
            reason = f"We selected a box plot to compare {self._label(metric_col)} distributions across {self._label(group_col)} groups. Box plots reveal medians, quartiles, and outliers."
        else:
            vals = df[metric_col].dropna()
            if len(vals) < 5:
                return None
            q1 = float(vals.quantile(0.25))
            q2 = float(vals.median())
            q3 = float(vals.quantile(0.75))
            iqr = q3 - q1
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr
            outliers = vals[(vals < lower) | (vals > upper)]
            data = [
                {
                    "x": self._label(metric_col),
                    "min": float(vals.min()),
                    "q1": q1,
                    "median": q2,
                    "q3": q3,
                    "max": float(vals.max()),
                    "outliers": [float(v) for v in outliers.head(10)],
                }
            ]
            title = f"{self._label(metric_col)} Distribution (Box Plot)"
            reason = f"We selected a box plot to show the distribution of {self._label(metric_col)}. Box plots reveal the median, quartiles, and outliers at a glance."

        if not data:
            return None

        source_cols = [metric_col] + ([group_col] if group_col else [])

        return ChartSpecification(
            chart_type="box_plot",
            title=title,
            description=f"Statistical distribution of {self._label(metric_col)}",
            x_axis=group_col or metric_col,
            y_axis=metric_col,
            source_columns=source_cols,
            data=data,
            section="supporting_charts",
            width=6,
            height=300,
            order=order,
            confidence=0.68,
            reason=reason,
            source_analysis="distribution_box",
            dataset_hash=understanding.dataset_hash,
        )

    def _make_treemap(
        self,
        df: pd.DataFrame,
        dim_col: str,
        metric_col: str,
        understanding: DatasetUnderstanding,
        order: int,
    ) -> ChartSpecification | None:
        """Treemap for hierarchical part-to-whole with many categories."""
        if not pd.api.types.is_numeric_dtype(df[metric_col]):
            return None

        cardinality = df[dim_col].nunique()
        if cardinality < 8:
            return None  # Use pie/donut for small category counts
        if cardinality > 100:
            return None  # Too many for treemap

        grouped = df.groupby(dim_col, dropna=False)[metric_col].sum().sort_values(ascending=False)
        grouped = grouped.head(30)  # Cap at 30 for readability

        total = float(grouped.sum())
        if total <= 0:
            return None

        data = [
            {"x": str(k), "y": float(v), "pct": round(float(v / total * 100), 1)}
            for k, v in grouped.items()
        ]

        return ChartSpecification(
            chart_type="treemap",
            title=f"{self._label(metric_col)} Distribution by {self._label(dim_col)}",
            description=f"Hierarchical view of {self._label(metric_col)} across {self._label(dim_col)} ({cardinality} categories)",
            x_axis=dim_col,
            y_axis=metric_col,
            aggregation="sum",
            source_columns=[dim_col, metric_col],
            data=data,
            section="supporting_charts",
            width=6,
            height=350,
            order=order,
            confidence=0.72,
            reason=f"We selected a treemap because {self._label(dim_col)} has {cardinality} categories â€” too many for a pie chart but ideal for a treemap, which shows part-to-whole relationships at scale.",
            source_analysis="composition_hierarchical",
            dataset_hash=understanding.dataset_hash,
        )

    # â”€â”€ Scoring â”€â”€

    def _ensure_diversity(
        self,
        charts: list[ChartSpecification],
        max_charts: int,
    ) -> list[ChartSpecification]:
        """Ensure chart type diversity by reserving slots for underrepresented types.

        Without this, bar charts and line charts (which score higher) would
        crowd out scatter plots, histograms, and heatmaps â€” even when those
        chart types provide unique analytical value.
        """
        if len(charts) <= max_charts:
            return charts[:max_charts]

        # Take the top charts by score
        top = charts[:max_charts]
        remaining = charts[max_charts:]

        # Chart types already in the top selection
        types_in_top = {c.chart_type for c in top}

        # Priority types to ensure inclusion (if they exist)
        priority_types = [
            "scatter_plot",
            "histogram",
            "heatmap",
            "box_plot",
            "area_chart",
            "treemap",
        ]

        for ptype in priority_types:
            if ptype in types_in_top:
                continue

            # Find the highest-scoring chart of this type from remaining
            for chart in remaining:
                if chart.chart_type == ptype:
                    # Replace the lowest-scoring non-priority chart in top
                    # Only replace bar/horizontal_bar/donut/pie (common types)
                    replaceable_types = {"bar_chart", "horizontal_bar", "donut_chart", "pie_chart"}
                    for i in range(len(top) - 1, -1, -1):
                        if top[i].chart_type in replaceable_types:
                            # Only replace if there's more than one of this type
                            type_count = sum(1 for c in top if c.chart_type == top[i].chart_type)
                            if type_count > 1:
                                top[i] = chart
                                types_in_top.add(ptype)
                                break
                    break

        # Re-sort by score
        top.sort(key=lambda c: c.importance_score, reverse=True)
        return top

    def _score_chart(
        self,
        chart: ChartSpecification,
        df: pd.DataFrame,
        understanding: DatasetUnderstanding,
    ) -> float:
        """Score a chart's importance (0-100).

        Score components:
          analytical_relevance (25) + data_quality (20) + interpretability (15)
          + business_value (15) + statistical_significance (10) + uniqueness (10) + readability (5)
        """
        score = 0.0

        # 1. Analytical relevance (max 25)
        score += chart.confidence * 25

        # 2. Data quality (max 20) â€” penalize charts using low-quality columns
        quality_penalty = 0.0
        for col_name in chart.source_columns:
            for col_u in understanding.columns:
                if col_u.name == col_name:
                    if col_u.missing_percentage > 50:
                        quality_penalty += 10
                    if col_u.missing_percentage > 80:
                        quality_penalty += 10
        score += max(0, 20 - quality_penalty)

        # 3. Interpretability (max 15)
        easy_types = {"bar_chart", "line_chart", "horizontal_bar", "pie_chart", "donut_chart"}
        if chart.chart_type in easy_types:
            score += 15
        elif chart.chart_type == "histogram":
            score += 12
        elif chart.chart_type == "scatter_plot":
            score += 10
        elif chart.chart_type == "heatmap":
            score += 8
        elif chart.chart_type == "geo_map":
            score += 12
        elif chart.chart_type == "area_chart":
            score += 13
        elif chart.chart_type == "box_plot":
            score += 9
        elif chart.chart_type == "treemap":
            score += 10

        # 4. Business value (max 15) â€” charts with measures in name
        y_axis_lower = (chart.y_axis or "").lower()
        if any(
            kw in y_axis_lower
            for kw in (
                "revenue",
                "sales",
                "amount",
                "total",
                "income",
                "profit",
                "billing",
                "payment",
            )
        ):
            score += 15
        elif chart.y_axis:
            score += 8
        else:
            score += 3

        # 5. Statistical significance (max 10)
        if chart.source_analysis == "correlation" and chart.data:
            # Boost scatter plots with strong correlations
            score += 8
        elif chart.source_analysis == "time_series":
            score += 10
        elif chart.source_analysis == "category_comparison":
            score += 7
        elif chart.source_analysis == "ranking":
            score += 6
        elif chart.source_analysis == "distribution":
            score += 5
        elif chart.source_analysis == "correlation_matrix":
            score += 7
        else:
            score += 4

        # 6. Uniqueness (max 10) â€” will be adjusted during dedup
        score += 10

        # 7. Readability (max 5)
        if chart.chart_type in ("pie_chart", "donut_chart"):
            # Pie charts are less readable with more categories
            n_cats = len(chart.data)
            if n_cats <= 5:
                score += 5
            elif n_cats <= 8:
                score += 3
            else:
                score += 1
        else:
            score += 5

        return min(100, max(0, score))

    # â”€â”€ Deduplication â”€â”€

    def _deduplicate(self, charts: list[ChartSpecification]) -> list[ChartSpecification]:
        """Detect and remove charts that communicate nearly identical information."""
        if len(charts) <= 1:
            return charts

        result: list[ChartSpecification] = []
        seen_signatures: set[str] = set()

        for chart in charts:
            # Create a signature based on source columns + chart type category
            cols = sorted(chart.source_columns)
            # Group similar chart types
            type_group = self._chart_type_group(chart.chart_type)

            # Signature 1: same columns + same type group
            sig1 = f"{type_group}:{','.join(cols)}"

            # Signature 2: same x/y axes + same type group
            # (different chart types with same axes are NOT duplicates)
            sig2 = f"axes:{type_group}:{chart.x_axis}:{chart.y_axis}"

            if sig1 in seen_signatures or sig2 in seen_signatures:
                # Duplicate â€” skip if the existing one has higher score
                continue

            seen_signatures.add(sig1)
            seen_signatures.add(sig2)
            result.append(chart)

        return result

    @staticmethod
    def _chart_type_group(chart_type: str) -> str:
        """Group similar chart types for deduplication."""
        bar_types = {"bar_chart", "horizontal_bar"}
        pie_types = {"pie_chart", "donut_chart"}
        if chart_type in bar_types:
            return "bar"
        if chart_type in pie_types:
            return "pie"
        return chart_type

    # â”€â”€ Quality filtering â”€â”€

    @staticmethod
    def _filter_by_quality(
        df: pd.DataFrame,
        columns: list[str],
        understanding: DatasetUnderstanding,
    ) -> list[str]:
        """Filter out columns with >80% missing values."""
        good = []
        for col in columns:
            if col not in df.columns:
                continue
            missing_pct = float(df[col].isna().sum() / max(len(df), 1) * 100)
            if missing_pct <= 80:
                good.append(col)
        return good

    # â”€â”€ Helpers â”€â”€

    @staticmethod
    def _label(col: str) -> str:
        """Convert column name to human-readable label."""
        return col.replace("_", " ").title()

    def explain_chart(self, chart: ChartSpecification) -> str:
        """Return the 'Why this chart?' explanation."""
        return chart.reason
