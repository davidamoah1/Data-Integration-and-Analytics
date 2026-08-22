"""Chart Selection Engine [DEPRECATED].

.. deprecated::
    Use ``services.auto.engine.VisualizationIntelligenceEngine`` instead.
    This module is preserved for backward compatibility but will be removed
    in a future release. All new code must use the canonical engine.

Selects appropriate visualizations based on the dataset understanding.
Each candidate chart is scored, deduplicated, and given a reason.

Selection rules (deterministic first, then scored):
  TIME + NUMERIC        → line chart
  CATEGORY + NUMERIC    → bar chart
  CATEGORY + PROPORTION → pie/donut (small category count only)
  TWO NUMERIC           → scatter plot
  DISTRIBUTION          → histogram / box plot
  CORRELATION           → heatmap
  RANKING               → sorted bar chart
  GEOGRAPHIC            → map (only if geo confirmed)

Scoring factors:
  analytical_relevance  (0-30)
  data_quality          (0-20)
  interpretability      (0-15)
  business_value        (0-15)
  statistical_significance (0-10)
  uniqueness            (0-10)
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from enum import Enum

import numpy as np
import pandas as pd

from .column_analyzer import (
    ColumnSemanticRole,
    DatasetUnderstanding,
)

logger = logging.getLogger(__name__)

# Limits (configurable via env in production)
MAX_CANDIDATE_CHARTS = 30
MAX_DASHBOARD_CHARTS = 12
MAX_PRESENTATION_CHARTS = 10


class ChartType(str, Enum):
    LINE = "line"
    BAR = "bar"
    HORIZONTAL_BAR = "horizontal_bar"
    PIE = "pie"
    DONUT = "donut"
    SCATTER = "scatter"
    HISTOGRAM = "histogram"
    BOX_PLOT = "box_plot"
    HEATMAP = "heatmap"
    AREA = "area"
    GEO_MAP = "geo_map"
    KPI_CARD = "kpi_card"
    TABLE = "table"


@dataclass
class ChartSpecification:
    """Canonical chart specification — single source of truth.

    This specification is used by:
      - Dashboard renderer
      - Report generator
      - PPTX presentation generator
    """

    id: str
    type: ChartType
    title: str
    description: str
    x_axis: str | None = None
    y_axis: str | None = None
    series: list[dict] = field(default_factory=list)
    aggregation: str = "sum"  # sum, mean, count, median, min, max
    filters: list[dict] = field(default_factory=list)
    importance_score: float = 0.0
    reason: str = ""
    why_this_chart: str = ""
    source_analysis: str = ""
    data: list[dict] = field(default_factory=list)  # actual data points
    data_hash: str = ""  # for versioning / dedup detection
    version: int = 1
    excluded_from_presentation: bool = False
    exclusion_reason: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type.value,
            "title": self.title,
            "description": self.description,
            "x_axis": self.x_axis,
            "y_axis": self.y_axis,
            "series": self.series,
            "aggregation": self.aggregation,
            "filters": self.filters,
            "importance_score": round(self.importance_score, 2),
            "reason": self.reason,
            "why_this_chart": self.why_this_chart,
            "source_analysis": self.source_analysis,
            "data": self.data[:100],  # cap for API response
            "data_hash": self.data_hash,
            "version": self.version,
            "excluded_from_presentation": self.excluded_from_presentation,
            "exclusion_reason": self.exclusion_reason,
        }


@dataclass
class ChartSelectionResult:
    """Result of chart selection."""

    charts: list[ChartSpecification] = field(default_factory=list)
    total_candidates: int = 0
    rejected: list[dict] = field(default_factory=list)  # rejected candidates with reasons
    dataset_hash: str = ""

    def to_dict(self) -> dict:
        return {
            "charts": [c.to_dict() for c in self.charts],
            "total_candidates": self.total_candidates,
            "rejected": self.rejected,
            "dataset_hash": self.dataset_hash,
            "chart_count": len(self.charts),
        }


class ChartSelector:
    """Selects and scores charts based on dataset understanding."""

    def select(
        self,
        df: pd.DataFrame,
        understanding: DatasetUnderstanding,
    ) -> ChartSelectionResult:
        """Select appropriate charts for the dataset."""
        result = ChartSelectionResult()
        result.dataset_hash = self._hash_dataset(df)

        # Generate candidate charts
        candidates = self._generate_candidates(df, understanding)
        result.total_candidates = len(candidates)

        # Score each candidate
        for chart in candidates:
            self._score_chart(chart, df, understanding)

        # Reject poor candidates
        scored = []
        for chart in candidates:
            if chart.importance_score < 20:
                result.rejected.append(
                    {
                        "type": chart.type.value,
                        "title": chart.title,
                        "reason": f"Score too low ({chart.importance_score:.1f})",
                    }
                )
            else:
                scored.append(chart)

        # Deduplicate
        deduped = self._deduplicate(scored)

        # Sort by score (descending)
        deduped.sort(key=lambda c: c.importance_score, reverse=True)

        # Cap at max dashboard charts
        result.charts = deduped[:MAX_DASHBOARD_CHARTS]

        return result

    def _generate_candidates(
        self,
        df: pd.DataFrame,
        understanding: DatasetUnderstanding,
    ) -> list[ChartSpecification]:
        """Generate all candidate charts based on data structure."""
        candidates: list[ChartSpecification] = []

        measures = understanding.measures
        dimensions = understanding.dimensions
        categories = understanding.categories
        date_cols = understanding.date_columns
        geo_cols = understanding.geo_columns

        # ─── Time series: DATE + MEASURE → line chart ───────────────────
        for date_col in date_cols:
            for measure in measures:
                if self._column_quality_ok(df, measure) and self._column_quality_ok(df, date_col):
                    chart = self._make_line_chart(df, date_col, measure, understanding)
                    if chart:
                        candidates.append(chart)

        # ─── Category + Measure → bar chart ──────────────────────────────
        for cat_col in categories + dimensions:
            for measure in measures:
                if self._column_quality_ok(df, measure) and self._column_quality_ok(df, cat_col):
                    chart = self._make_bar_chart(df, cat_col, measure, understanding)
                    if chart:
                        candidates.append(chart)

        # ─── Category proportion → pie/donut (small cardinality only) ────
        for cat_col in categories:
            cardinality = self._cardinality(df, cat_col)
            if 2 <= cardinality <= 8:
                chart = self._make_pie_chart(df, cat_col, understanding)
                if chart:
                    candidates.append(chart)

        # ─── Two numeric → scatter plot ──────────────────────────────────
        if len(measures) >= 2:
            for i, m1 in enumerate(measures):
                for m2 in measures[i + 1 :]:
                    if self._column_quality_ok(df, m1) and self._column_quality_ok(df, m2):
                        chart = self._make_scatter_chart(df, m1, m2, understanding)
                        if chart:
                            candidates.append(chart)

        # ─── Distribution → histogram ────────────────────────────────────
        for measure in measures:
            if self._column_quality_ok(df, measure):
                chart = self._make_histogram(df, measure, understanding)
                if chart:
                    candidates.append(chart)

        # ─── Correlation heatmap (3+ numeric columns) ────────────────────
        if len(measures) >= 3:
            chart = self._make_heatmap(df, measures, understanding)
            if chart:
                candidates.append(chart)

        # ─── Geographic → map (only if geo detected) ─────────────────────
        for geo_col in geo_cols:
            for measure in measures:
                if self._column_quality_ok(df, measure) and self._column_quality_ok(df, geo_col):
                    chart = self._make_geo_chart(df, geo_col, measure, understanding)
                    if chart:
                        candidates.append(chart)

        # ─── Ranking → sorted bar (top N) ────────────────────────────────
        for cat_col in categories + dimensions:
            for measure in measures:
                if self._cardinality(df, cat_col) > 5:
                    chart = self._make_ranking_chart(df, cat_col, measure, understanding)
                    if chart:
                        candidates.append(chart)

        return candidates[:MAX_CANDIDATE_CHARTS]

    # ─── Chart builders ──────────────────────────────────────────────────

    def _make_line_chart(
        self, df: pd.DataFrame, date_col: str, measure: str, u: DatasetUnderstanding
    ) -> ChartSpecification | None:
        """Create a line chart for time + measure."""
        try:
            # Parse dates
            dates = pd.to_datetime(df[date_col], errors="coerce")
            temp = df.copy()
            temp["_date_parsed"] = dates
            temp = temp.dropna(subset=["_date_parsed", measure])

            if len(temp) == 0:
                return None

            # Group by date (daily/monthly depending on range)
            date_range = (temp["_date_parsed"].max() - temp["_date_parsed"].min()).days
            if date_range > 365:
                temp["_period"] = temp["_date_parsed"].dt.to_period("M").astype(str)
            else:
                temp["_period"] = temp["_date_parsed"].dt.strftime("%Y-%m-%d")

            grouped = temp.groupby("_period")[measure].agg(["sum", "mean", "count"]).reset_index()
            grouped = grouped.sort_values("_period")

            data = [{"x": row["_period"], "y": float(row["sum"])} for _, row in grouped.iterrows()]

            # Generate meaningful title
            measure_label = measure.replace("_", " ").title()
            title = f"{measure_label} Over Time"

            return ChartSpecification(
                id=f"line_{date_col}_{measure}",
                type=ChartType.LINE,
                title=title,
                description=f"Trend of {measure_label} over time, grouped by {date_col}",
                x_axis=date_col,
                y_axis=measure,
                aggregation="sum",
                importance_score=0,  # scored later
                reason=f"Line chart shows how {measure_label} changes over time",
                why_this_chart=(
                    f"We selected a line chart because your dataset contains a "
                    f"date/time column ('{date_col}') and a numerical measure "
                    f"('{measure}'). Line charts are the standard way to show "
                    f"how a value changes over time."
                ),
                source_analysis="time_series",
                data=data,
                data_hash=self._hash_data(data),
            )
        except Exception as e:
            logger.debug("Line chart failed for %s + %s: %s", date_col, measure, e)
            return None

    def _make_bar_chart(
        self, df: pd.DataFrame, cat_col: str, measure: str, u: DatasetUnderstanding
    ) -> ChartSpecification | None:
        """Create a bar chart for category + measure."""
        try:
            temp = df.dropna(subset=[cat_col, measure])
            if len(temp) == 0:
                return None

            cardinality = temp[cat_col].nunique()
            if cardinality > 50:
                # Too many categories — use top N
                grouped = temp.groupby(cat_col)[measure].sum().nlargest(15).reset_index()
            else:
                grouped = temp.groupby(cat_col)[measure].sum().reset_index()
                grouped = grouped.sort_values(measure, ascending=False)

            data = [
                {"x": str(row[cat_col]), "y": float(row[measure])} for _, row in grouped.iterrows()
            ]

            measure_label = measure.replace("_", " ").title()
            cat_label = cat_col.replace("_", " ").title()
            title = f"{measure_label} by {cat_label}"

            return ChartSpecification(
                id=f"bar_{cat_col}_{measure}",
                type=ChartType.BAR,
                title=title,
                description=f"Comparison of {measure_label} across {cat_label} categories",
                x_axis=cat_col,
                y_axis=measure,
                aggregation="sum",
                importance_score=0,
                reason=f"Bar chart compares {measure_label} across {cat_label} groups",
                why_this_chart=(
                    f"We selected a bar chart because your dataset contains a "
                    f"categorical column ('{cat_col}') and a numerical measure "
                    f"('{measure}'). Bar charts are ideal for comparing values "
                    f"across different categories."
                ),
                source_analysis="category_comparison",
                data=data,
                data_hash=self._hash_data(data),
            )
        except Exception as e:
            logger.debug("Bar chart failed for %s + %s: %s", cat_col, measure, e)
            return None

    def _make_pie_chart(
        self, df: pd.DataFrame, cat_col: str, u: DatasetUnderstanding
    ) -> ChartSpecification | None:
        """Create a pie chart for category proportion."""
        try:
            temp = df.dropna(subset=[cat_col])
            if len(temp) == 0:
                return None

            cardinality = temp[cat_col].nunique()
            if cardinality > 8:
                return None  # Too many categories for pie

            counts = temp[cat_col].value_counts()
            data = [{"x": str(k), "y": int(v)} for k, v in counts.items()]

            cat_label = cat_col.replace("_", " ").title()
            title = f"Distribution by {cat_label}"

            return ChartSpecification(
                id=f"pie_{cat_col}",
                type=ChartType.PIE,
                title=title,
                description=f"Proportion of records by {cat_label}",
                x_axis=cat_col,
                y_axis="count",
                aggregation="count",
                importance_score=0,
                reason=f"Pie chart shows the share of each {cat_label} category",
                why_this_chart=(
                    f"We selected a pie chart because your dataset contains a "
                    f"categorical column ('{cat_col}') with only {cardinality} "
                    f"distinct values. Pie charts are effective for showing "
                    f"part-to-whole relationships when there are few categories."
                ),
                source_analysis="proportion",
                data=data,
                data_hash=self._hash_data(data),
            )
        except Exception as e:
            logger.debug("Pie chart failed for %s: %s", cat_col, e)
            return None

    def _make_scatter_chart(
        self, df: pd.DataFrame, m1: str, m2: str, u: DatasetUnderstanding
    ) -> ChartSpecification | None:
        """Create a scatter plot for two numeric variables."""
        try:
            temp = df.dropna(subset=[m1, m2])
            if len(temp) < 5:
                return None

            # Sample if too many points
            if len(temp) > 200:
                temp = temp.sample(200, random_state=42)

            data = [{"x": float(row[m1]), "y": float(row[m2])} for _, row in temp.iterrows()]

            m1_label = m1.replace("_", " ").title()
            m2_label = m2.replace("_", " ").title()

            # Compute correlation
            corr = temp[m1].corr(temp[m2])
            corr_text = f" (r={corr:.2f})" if not pd.isna(corr) else ""

            title = f"{m1_label} vs {m2_label}{corr_text}"

            return ChartSpecification(
                id=f"scatter_{m1}_{m2}",
                type=ChartType.SCATTER,
                title=title,
                description=f"Relationship between {m1_label} and {m2_label}",
                x_axis=m1,
                y_axis=m2,
                aggregation="none",
                importance_score=0,
                reason=f"Scatter plot reveals the relationship between {m1_label} and {m2_label}",
                why_this_chart=(
                    (
                        f"We selected a scatter plot because your dataset contains two "
                        f"numerical columns ('{m1}' and '{m2}'). Scatter plots are the "
                        f"standard way to examine relationships between two continuous "
                        f"variables. The correlation coefficient is {corr:.3f}."
                    )
                    if not pd.isna(corr)
                    else (
                        f"We selected a scatter plot because your dataset contains two "
                        f"numerical columns ('{m1}' and '{m2}')."
                    )
                ),
                source_analysis="correlation",
                data=data,
                data_hash=self._hash_data(data),
            )
        except Exception as e:
            logger.debug("Scatter chart failed for %s + %s: %s", m1, m2, e)
            return None

    def _make_histogram(
        self, df: pd.DataFrame, measure: str, u: DatasetUnderstanding
    ) -> ChartSpecification | None:
        """Create a histogram for a numeric column."""
        try:
            temp = df[measure].dropna()
            if len(temp) < 5:
                return None

            # Create bins
            counts, bin_edges = np.histogram(temp, bins="auto")
            data = [
                {"x": f"{bin_edges[i]:.1f}-{bin_edges[i+1]:.1f}", "y": int(counts[i])}
                for i in range(len(counts))
            ]

            measure_label = measure.replace("_", " ").title()
            title = f"Distribution of {measure_label}"

            return ChartSpecification(
                id=f"hist_{measure}",
                type=ChartType.HISTOGRAM,
                title=title,
                description=f"Frequency distribution of {measure_label}",
                x_axis=measure,
                y_axis="frequency",
                aggregation="count",
                importance_score=0,
                reason=f"Histogram shows the distribution shape of {measure_label}",
                why_this_chart=(
                    f"We selected a histogram because '{measure}' is a numerical "
                    f"column. Histograms reveal the distribution shape — whether "
                    f"values are normally distributed, skewed, or have outliers."
                ),
                source_analysis="distribution",
                data=data,
                data_hash=self._hash_data(data),
            )
        except Exception as e:
            logger.debug("Histogram failed for %s: %s", measure, e)
            return None

    def _make_heatmap(
        self, df: pd.DataFrame, measures: list[str], u: DatasetUnderstanding
    ) -> ChartSpecification | None:
        """Create a correlation heatmap for multiple numeric columns."""
        try:
            temp = df[measures].dropna()
            if len(temp) < 10:
                return None

            corr_matrix = temp.corr()
            data = []
            for i, m1 in enumerate(measures):
                for j, m2 in enumerate(measures):
                    val = corr_matrix.iloc[i, j]
                    if not pd.isna(val):
                        data.append({"x": m1, "y": m2, "value": float(val)})

            title = "Correlation Matrix"

            return ChartSpecification(
                id="heatmap_correlation",
                type=ChartType.HEATMAP,
                title=title,
                description=f"Correlation between {len(measures)} numerical variables",
                x_axis="variables",
                y_axis="variables",
                aggregation="correlation",
                importance_score=0,
                reason="Heatmap reveals which numerical variables are correlated",
                why_this_chart=(
                    f"We selected a correlation heatmap because your dataset has "
                    f"{len(measures)} numerical columns. The heatmap shows how "
                    f"strongly each pair of variables is correlated, helping you "
                    f"identify relationships worth investigating further."
                ),
                source_analysis="correlation_matrix",
                data=data,
                data_hash=self._hash_data(data),
            )
        except Exception as e:
            logger.debug("Heatmap failed: %s", e)
            return None

    def _make_geo_chart(
        self, df: pd.DataFrame, geo_col: str, measure: str, u: DatasetUnderstanding
    ) -> ChartSpecification | None:
        """Create a geographic chart."""
        try:
            temp = df.dropna(subset=[geo_col, measure])
            if len(temp) == 0:
                return None

            grouped = temp.groupby(geo_col)[measure].sum().reset_index()
            grouped = grouped.sort_values(measure, ascending=False)

            data = [
                {"x": str(row[geo_col]), "y": float(row[measure])} for _, row in grouped.iterrows()
            ]

            measure_label = measure.replace("_", " ").title()
            geo_label = geo_col.replace("_", " ").title()
            title = f"{measure_label} by {geo_label}"

            return ChartSpecification(
                id=f"geo_{geo_col}_{measure}",
                type=ChartType.GEO_MAP,
                title=title,
                description=f"Geographic distribution of {measure_label}",
                x_axis=geo_col,
                y_axis=measure,
                aggregation="sum",
                importance_score=0,
                reason=f"Map chart shows {measure_label} across geographic regions",
                why_this_chart=(
                    f"We selected a map visualization because '{geo_col}' was "
                    f"detected as a geographic column and '{measure}' is a "
                    f"numerical measure. Maps are the most intuitive way to "
                    f"show how values vary across locations."
                ),
                source_analysis="geographic",
                data=data,
                data_hash=self._hash_data(data),
            )
        except Exception as e:
            logger.debug("Geo chart failed for %s + %s: %s", geo_col, measure, e)
            return None

    def _make_ranking_chart(
        self, df: pd.DataFrame, cat_col: str, measure: str, u: DatasetUnderstanding
    ) -> ChartSpecification | None:
        """Create a sorted bar chart showing top N items."""
        try:
            temp = df.dropna(subset=[cat_col, measure])
            if len(temp) == 0:
                return None

            top_n = 10
            grouped = temp.groupby(cat_col)[measure].sum().nlargest(top_n).reset_index()

            data = [
                {"x": str(row[cat_col]), "y": float(row[measure])} for _, row in grouped.iterrows()
            ]

            measure_label = measure.replace("_", " ").title()
            cat_label = cat_col.replace("_", " ").title()
            title = f"Top {top_n} {cat_label} by {measure_label}"

            return ChartSpecification(
                id=f"ranking_{cat_col}_{measure}",
                type=ChartType.HORIZONTAL_BAR,
                title=title,
                description=f"Top {top_n} {cat_label} ranked by {measure_label}",
                x_axis=cat_col,
                y_axis=measure,
                aggregation="sum",
                importance_score=0,
                reason=f"Ranking chart highlights the top-performing {cat_label}",
                why_this_chart=(
                    f"We selected a ranking chart because '{cat_col}' has many "
                    f"categories. Showing only the top {top_n} makes the chart "
                    f"readable and highlights the most important contributors."
                ),
                source_analysis="ranking",
                data=data,
                data_hash=self._hash_data(data),
            )
        except Exception as e:
            logger.debug("Ranking chart failed for %s + %s: %s", cat_col, measure, e)
            return None

    # ─── Scoring ─────────────────────────────────────────────────────────

    def _score_chart(
        self,
        chart: ChartSpecification,
        df: pd.DataFrame,
        u: DatasetUnderstanding,
    ) -> None:
        """Score a chart on multiple factors."""
        # Analytical relevance (0-30)
        relevance = self._score_relevance(chart, u)

        # Data quality (0-20)
        quality = self._score_quality(chart, df)

        # Interpretability (0-15)
        interpretability = self._score_interpretability(chart)

        # Business value (0-15)
        business_value = self._score_business_value(chart, u)

        # Statistical significance (0-10)
        significance = self._score_significance(chart, df)

        # Uniqueness (0-10) — will be adjusted during dedup
        uniqueness = 10.0

        chart.importance_score = (
            relevance + quality + interpretability + business_value + significance + uniqueness
        )

    def _score_relevance(self, chart: ChartSpecification, u: DatasetUnderstanding) -> float:
        """Score analytical relevance (0-30)."""
        score = 0.0

        # Time series with measures → high relevance
        if chart.type == ChartType.LINE and chart.source_analysis == "time_series":
            score = 28.0
        # Category comparison → high
        elif chart.type == ChartType.BAR and chart.source_analysis == "category_comparison":
            score = 25.0
        # Correlation → high if multiple measures
        elif chart.type == ChartType.SCATTER:
            score = 22.0
        elif chart.type == ChartType.HEATMAP:
            score = 20.0
        # Distribution → moderate
        elif chart.type == ChartType.HISTOGRAM:
            score = 18.0
        # Proportion → moderate
        elif chart.type in (ChartType.PIE, ChartType.DONUT):
            score = 16.0
        # Ranking → moderate-high
        elif chart.type == ChartType.HORIZONTAL_BAR:
            score = 22.0
        # Geographic → high if geo detected
        elif chart.type == ChartType.GEO_MAP:
            score = 24.0
        else:
            score = 12.0

        # Boost if uses a detected measure
        if chart.y_axis and chart.y_axis in u.measures:
            score += 2

        return min(30, score)

    def _score_quality(self, chart: ChartSpecification, df: pd.DataFrame) -> float:
        """Score data quality (0-20)."""
        if not chart.data:
            return 0

        # Check completeness of source columns
        score = 20.0

        if chart.x_axis and chart.x_axis in df.columns:
            missing = df[chart.x_axis].isna().sum() / len(df) if len(df) > 0 else 1
            score -= missing * 10

        if chart.y_axis and chart.y_axis in df.columns:
            missing = df[chart.y_axis].isna().sum() / len(df) if len(df) > 0 else 1
            score -= missing * 10

        # Penalize very few data points
        if len(chart.data) < 3:
            score -= 5

        return max(0, score)

    def _score_interpretability(self, chart: ChartSpecification) -> float:
        """Score interpretability (0-15)."""
        score = 15.0

        # Pie charts with many slices are hard to read
        if chart.type in (ChartType.PIE, ChartType.DONUT) and len(chart.data) > 6:
            score -= 5

        # Bar charts with too many categories
        if chart.type == ChartType.BAR and len(chart.data) > 15:
            score -= 3

        # Scatter with too many points
        if chart.type == ChartType.SCATTER and len(chart.data) > 150:
            score -= 2

        return max(0, score)

    def _score_business_value(self, chart: ChartSpecification, u: DatasetUnderstanding) -> float:
        """Score business value (0-15)."""
        score = 10.0

        # Boost charts using currency/measure columns
        if chart.y_axis:
            col_u = next((c for c in u.columns if c.name == chart.y_axis), None)
            if col_u:
                if col_u.role == ColumnSemanticRole.CURRENCY:
                    score += 5
                elif col_u.role == ColumnSemanticRole.MEASURE:
                    score += 3
                elif col_u.role == ColumnSemanticRole.PERCENTAGE:
                    score += 2

        # Boost time series (always business-relevant)
        if chart.type == ChartType.LINE:
            score += 2

        return min(15, score)

    def _score_significance(self, chart: ChartSpecification, df: pd.DataFrame) -> float:
        """Score statistical significance (0-10)."""
        if not chart.data:
            return 0

        score = 5.0

        # Scatter with strong correlation
        if chart.type == ChartType.SCATTER and chart.x_axis and chart.y_axis:
            try:
                corr = df[chart.x_axis].corr(df[chart.y_axis])
                if not pd.isna(corr) and abs(corr) > 0.5:
                    score += 5
                elif not pd.isna(corr) and abs(corr) > 0.3:
                    score += 3
            except Exception:
                pass

        # Bar chart with clear dominant category
        if chart.type == ChartType.BAR and len(chart.data) > 0:
            values = [d["y"] for d in chart.data]
            if values:
                max_val = max(values)
                total = sum(values)
                if total > 0 and max_val / total > 0.4:
                    score += 3  # One category dominates → interesting

        return min(10, score)

    # ─── Deduplication ───────────────────────────────────────────────────

    def _deduplicate(self, charts: list[ChartSpecification]) -> list[ChartSpecification]:
        """Remove charts that communicate nearly identical information."""
        result: list[ChartSpecification] = []
        seen_hashes: set[str] = set()
        seen_combos: set[str] = set()

        for chart in charts:
            # Skip if exact data hash seen
            if chart.data_hash in seen_hashes:
                continue
            seen_hashes.add(chart.data_hash)

            # Skip if same axis combination seen (e.g., bar + pie for same category)
            combo = f"{chart.type.value}:{chart.x_axis}:{chart.y_axis}"
            if combo in seen_combos:
                continue
            seen_combos.add(combo)

            result.append(chart)

        return result

    # ─── Utilities ───────────────────────────────────────────────────────

    def _column_quality_ok(self, df: pd.DataFrame, col: str) -> bool:
        """Check if a column has sufficient quality for visualization."""
        if col not in df.columns:
            return False
        missing_ratio = df[col].isna().sum() / len(df) if len(df) > 0 else 1
        return missing_ratio < 0.8  # Reject columns with 80%+ missing

    def _cardinality(self, df: pd.DataFrame, col: str) -> int:
        """Get cardinality of a column."""
        if col not in df.columns:
            return 0
        return int(df[col].nunique())

    def _hash_data(self, data: list[dict]) -> str:
        """Create a hash of chart data for dedup/versioning."""
        import json

        data_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(data_str.encode()).hexdigest()[:12]

    def _hash_dataset(self, df: pd.DataFrame) -> str:
        """Create a hash of the dataset for versioning."""
        try:
            # Use shape + first/last rows for a quick hash
            info = f"{df.shape}_{list(df.columns)}"
            return hashlib.sha256(info.encode()).hexdigest()[:12]
        except Exception:
            return "unknown"
