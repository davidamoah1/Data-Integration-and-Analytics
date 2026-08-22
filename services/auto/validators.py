"""Chart Validation & Fallback Engine.

Validates chart specifications before rendering and provides fallback
selection when a chart fails validation.

Validation checks:
  - columns exist in the DataFrame
  - data is non-empty
  - aggregation is valid for the column types
  - data types are compatible with the chart type
  - no impossible configurations (e.g., pie chart with 50 categories)
  - chart type is appropriate for the data

If validation fails, the engine tries the next-ranked valid chart.
One broken chart must NEVER destroy the entire dashboard.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import pandas as pd

from services.auto.chart_specification import ChartSpecification

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of validating a chart specification."""

    valid: bool
    reason: str = ""
    warnings: list[str] | None = None

    def __post_init__(self) -> None:
        if self.warnings is None:
            self.warnings = []


class ChartValidator:
    """Validates chart specifications against the source DataFrame."""

    # Chart type → required axis count
    REQUIRED_AXES: dict[str, int] = {
        "bar_chart": 2,
        "horizontal_bar": 2,
        "line_chart": 2,
        "area_chart": 2,
        "pie_chart": 1,
        "donut_chart": 1,
        "scatter_plot": 2,
        "histogram": 1,
        "box_plot": 1,
        "heatmap": 3,  # x, y, z
        "geo_map": 2,
        "treemap": 2,
        "leaderboard": 2,
        "kpi_card": 0,
        "table": 0,
    }

    # Pie/donut max categories
    PIE_MAX_CATEGORIES = 8

    # Bar max categories for readability
    BAR_MAX_CATEGORIES = 25

    def validate(
        self,
        chart: ChartSpecification,
        df: pd.DataFrame,
    ) -> ValidationResult:
        """Validate a chart specification against the source DataFrame.

        Args:
            chart: The chart specification to validate.
            df: The source DataFrame.

        Returns:
            ValidationResult with valid=True if the chart can be rendered.
        """
        warnings: list[str] = []

        # 1. Check that data exists
        if not chart.data:
            return ValidationResult(
                valid=False,
                reason="Chart has no data points",
                warnings=warnings,
            )

        # 2. Check that source columns exist in DataFrame
        for col in chart.source_columns:
            if col and col not in df.columns:
                return ValidationResult(
                    valid=False,
                    reason=f"Column '{col}' not found in dataset",
                    warnings=warnings,
                )

        # 3. Check chart-type-specific constraints
        type_check = self._validate_chart_type(chart, df)
        if not type_check.valid:
            return type_check

        # 4. Check for NaN/undefined values in data
        nan_check = self._validate_no_nan(chart)
        if not nan_check.valid:
            return nan_check

        # 5. Check aggregation validity
        agg_check = self._validate_aggregation(chart, df)
        if not agg_check.valid:
            return agg_check

        # 6. Warnings for suboptimal but valid charts
        if chart.chart_type in ("pie_chart", "donut_chart"):
            n_cats = len(chart.data)
            if n_cats > 6:
                warnings.append(
                    f"Pie chart has {n_cats} segments — consider a bar chart for readability"
                )

        if chart.chart_type in ("bar_chart", "horizontal_bar"):
            n_cats = len(chart.data)
            if n_cats > 15:
                warnings.append(
                    f"Bar chart has {n_cats} categories — showing top {n_cats} only"
                )

        return ValidationResult(valid=True, warnings=warnings)

    def validate_and_fallback(
        self,
        charts: list[ChartSpecification],
        df: pd.DataFrame,
    ) -> list[ChartSpecification]:
        """Validate a list of charts and return only valid ones.

        If a chart fails validation, it is skipped and the next-ranked
        chart is considered. The dashboard continues even if some charts fail.

        Args:
            charts: List of chart specifications sorted by importance.
            df: The source DataFrame.

        Returns:
            List of valid chart specifications.
        """
        valid_charts: list[ChartSpecification] = []

        for chart in charts:
            result = self.validate(chart, df)
            if result.valid:
                valid_charts.append(chart)
            else:
                logger.warning(
                    "Chart '%s' (type=%s) failed validation: %s",
                    chart.title,
                    chart.chart_type,
                    result.reason,
                )

        return valid_charts

    def _validate_chart_type(
        self,
        chart: ChartSpecification,
        df: pd.DataFrame,
    ) -> ValidationResult:
        """Validate chart-type-specific constraints."""
        ct = chart.chart_type

        # Pie/donut: must have small number of categories
        if ct in ("pie_chart", "donut_chart"):
            n_cats = len(chart.data)
            if n_cats > self.PIE_MAX_CATEGORIES:
                return ValidationResult(
                    valid=False,
                    reason=f"Pie chart has {n_cats} categories (max {self.PIE_MAX_CATEGORIES})",
                )
            if n_cats < 2:
                return ValidationResult(
                    valid=False,
                    reason="Pie chart needs at least 2 categories",
                )

        # Bar: check category count
        if ct in ("bar_chart", "horizontal_bar"):
            n_cats = len(chart.data)
            if n_cats > self.BAR_MAX_CATEGORIES:
                return ValidationResult(
                    valid=False,
                    reason=f"Bar chart has {n_cats} categories (max {self.BAR_MAX_CATEGORIES})",
                )

        # Scatter: need at least 5 data points
        if ct == "scatter_plot":
            if len(chart.data) < 5:
                return ValidationResult(
                    valid=False,
                    reason="Scatter plot needs at least 5 data points",
                )

        # Histogram: need at least 5 data points
        if ct == "histogram":
            if len(chart.data) < 3:
                return ValidationResult(
                    valid=False,
                    reason="Histogram needs at least 3 bins",
                )

        # Line: need at least 2 data points
        if ct == "line_chart":
            if len(chart.data) < 2:
                return ValidationResult(
                    valid=False,
                    reason="Line chart needs at least 2 data points",
                )

        # Heatmap: need at least 2x2 grid
        if ct == "heatmap":
            if len(chart.data) < 4:
                return ValidationResult(
                    valid=False,
                    reason="Heatmap needs at least a 2×2 grid",
                )

        # Geo map: need at least 2 regions
        if ct == "geo_map":
            if len(chart.data) < 1:
                return ValidationResult(
                    valid=False,
                    reason="Geo map needs at least 1 region",
                )

        return ValidationResult(valid=True)

    def _validate_no_nan(self, chart: ChartSpecification) -> ValidationResult:
        """Check that chart data doesn't contain NaN/None values."""
        for i, point in enumerate(chart.data):
            for key, val in point.items():
                if val is None:
                    return ValidationResult(
                        valid=False,
                        reason=f"Data point {i} has None value for '{key}'",
                    )
                if isinstance(val, float):
                    import math

                    if math.isnan(val):
                        return ValidationResult(
                            valid=False,
                            reason=f"Data point {i} has NaN value for '{key}'",
                        )
        return ValidationResult(valid=True)

    def _validate_aggregation(
        self,
        chart: ChartSpecification,
        df: pd.DataFrame,
    ) -> ValidationResult:
        """Validate that the aggregation is valid for the column types."""
        if not chart.aggregation or chart.aggregation == "none":
            return ValidationResult(valid=True)

        valid_aggs = {"sum", "count", "avg", "mean", "min", "max", "median"}
        if chart.aggregation not in valid_aggs:
            return ValidationResult(
                valid=False,
                reason=f"Unknown aggregation: {chart.aggregation}",
            )

        # Sum/avg/median/min/max require numeric y_axis
        if chart.aggregation in ("sum", "avg", "mean", "median", "min", "max"):
            if chart.y_axis and chart.y_axis in df.columns:
                if not pd.api.types.is_numeric_dtype(df[chart.y_axis]):
                    return ValidationResult(
                        valid=False,
                        reason=f"Aggregation '{chart.aggregation}' requires numeric column '{chart.y_axis}'",
                    )

        return ValidationResult(valid=True)
