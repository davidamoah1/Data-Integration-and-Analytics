"""Chart Recommendation Engine [DEPRECATED].

.. deprecated::
    Use ``services.auto.engine.VisualizationIntelligenceEngine`` instead.
    This module is preserved for backward compatibility with
    ``services.dashboard_engine_routes`` but will be removed in a future
    release. All new code must use the canonical engine.

Recommends visualizations based on data characteristics, semantic mappings,
and industry knowledge. The engine analyzes:

  - Data types (numeric, categorical, datetime, geographic)
  - Cardinality (unique value counts)
  - Relationships between columns
  - Semantic entity roles (metric, dimension, entity)
  - Industry-specific chart preferences

Chart type selection logic:
  - Time series â†’ Line chart
  - Category comparison â†’ Bar chart
  - Composition â†’ Pie/Donut
  - Distribution â†’ Histogram
  - Correlation â†’ Scatter plot
  - Geographic data â†’ Map
  - Ranking â†’ Horizontal bar chart
"""

from __future__ import annotations

import logging
import uuid

import pandas as pd

from services.dashboard_engine import ChartDefinition, LayoutSection

logger = logging.getLogger(__name__)


class ChartRecommendationEngine:
    """Recommends chart types based on data characteristics."""

    # Industry-specific chart preferences
    INDUSTRY_CHART_PREFERENCES: dict[str, list[str]] = {
        "healthcare": ["treemap", "funnel", "bar", "line"],
        "education": ["waterfall", "bar", "line"],
        "church": ["rose", "bar", "line"],
        "government": ["icicle", "bar", "gauge"],
        "ngo": ["sunburst", "bar", "line"],
        "retail": ["bar", "line", "pie", "heatmap"],
        "banking": ["bar", "line", "pie"],
        "manufacturing": ["bar", "line", "gauge"],
        "agriculture": ["bar", "pie", "line"],
        "insurance": ["bar", "line", "pie"],
        "hospitality": ["bar", "line", "pie"],
        "telecommunications": ["bar", "line", "pie"],
    }

    def recommend_charts(
        self,
        df: pd.DataFrame,
        industry: str,
        semantic_mappings: dict | None = None,
        max_charts: int = 12,
    ) -> list[ChartDefinition]:
        """Recommend charts for a dataset.

        Args:
            df: The dataset DataFrame.
            industry: Detected industry.
            semantic_mappings: Column-to-entity mapping.
            max_charts: Maximum number of charts to recommend.

        Returns:
            List of ChartDefinition objects.
        """
        col_mapping = semantic_mappings or {}
        charts: list[ChartDefinition] = []
        order = 0

        # Identify column categories
        numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
        categorical_cols = [c for c in df.columns if df[c].dtype == "object"]
        datetime_cols = [c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])]
        geo_cols = self._find_geo_columns(col_mapping, categorical_cols)

        # Identify semantic roles
        metric_cols = self._find_metric_columns(df, col_mapping, numeric_cols)
        dimension_cols = self._find_dimension_columns(col_mapping, categorical_cols)
        entity_cols = self._find_entity_columns(col_mapping)

        # 1. Time series charts
        for date_col in datetime_cols[:2]:
            for metric_col in metric_cols[:3]:
                charts.append(
                    self._make_chart(
                        chart_type="line_chart",
                        title=f"{self._label(metric_col)} Over Time",
                        section=LayoutSection.PRIMARY_CHARTS.value,
                        x_axis=date_col,
                        y_axis=metric_col,
                        aggregation="sum",
                        source_columns=[date_col, metric_col],
                        confidence=0.9,
                        reasoning=f"Time series: {self._label(metric_col)} plotted over {self._label(date_col)}",
                        order=order,
                    )
                )
                order += 1

        # 2. Category comparison (bar charts)
        for dim_col in dimension_cols[:3]:
            for metric_col in metric_cols[:2]:
                if dim_col == metric_col:
                    continue
                cardinality = df[dim_col].nunique()
                chart_type = "horizontal_bar" if cardinality > 20 else "bar_chart"

                charts.append(
                    self._make_chart(
                        chart_type=chart_type,
                        title=f"{self._label(metric_col)} by {self._label(dim_col)}",
                        section=LayoutSection.PRIMARY_CHARTS.value,
                        x_axis=dim_col,
                        y_axis=metric_col,
                        aggregation="sum",
                        source_columns=[dim_col, metric_col],
                        confidence=0.85,
                        reasoning=f"Category comparison: {self._label(metric_col)} grouped by {self._label(dim_col)} ({cardinality} categories)",
                        order=order,
                    )
                )
                order += 1

        # 3. Composition (pie/donut)
        for dim_col in dimension_cols[:2]:
            cardinality = df[dim_col].nunique()
            if 2 <= cardinality <= 10:
                charts.append(
                    self._make_chart(
                        chart_type="donut_chart",
                        title=f"{self._label(dim_col)} Distribution",
                        section=LayoutSection.SUPPORTING_CHARTS.value,
                        x_axis=dim_col,
                        aggregation="count",
                        source_columns=[dim_col],
                        confidence=0.75,
                        reasoning=f"Composition: distribution of {self._label(dim_col)} ({cardinality} segments)",
                        width=4,
                        order=order,
                    )
                )
                order += 1

        # 4. Distribution (histogram)
        for metric_col in metric_cols[:2]:
            if df[metric_col].nunique() > 10:
                charts.append(
                    self._make_chart(
                        chart_type="histogram",
                        title=f"{self._label(metric_col)} Distribution",
                        section=LayoutSection.SUPPORTING_CHARTS.value,
                        x_axis=metric_col,
                        aggregation="count",
                        source_columns=[metric_col],
                        confidence=0.7,
                        reasoning=f"Distribution: histogram of {self._label(metric_col)}",
                        width=6,
                        order=order,
                    )
                )
                order += 1

        # 5. Correlation (scatter)
        if len(metric_cols) >= 2:
            charts.append(
                self._make_chart(
                    chart_type="scatter_plot",
                    title=f"{self._label(metric_cols[0])} vs {self._label(metric_cols[1])}",
                    section=LayoutSection.SUPPORTING_CHARTS.value,
                    x_axis=metric_cols[0],
                    y_axis=metric_cols[1],
                    source_columns=[metric_cols[0], metric_cols[1]],
                    confidence=0.65,
                    reasoning=f"Correlation: scatter plot of {self._label(metric_cols[0])} vs {self._label(metric_cols[1])}",
                    width=6,
                    order=order,
                )
            )
            order += 1

        # 6. Geographic (map)
        if geo_cols:
            for geo_col in geo_cols[:1]:
                for metric_col in metric_cols[:1]:
                    charts.append(
                        self._make_chart(
                            chart_type="geo_map",
                            title=f"{self._label(metric_col)} by {self._label(geo_col)}",
                            section=LayoutSection.PRIMARY_CHARTS.value,
                            x_axis=geo_col,
                            y_axis=metric_col,
                            aggregation="sum",
                            source_columns=[geo_col, metric_col],
                            confidence=0.8,
                            reasoning=f"Geographic: {self._label(metric_col)} visualized by {self._label(geo_col)}",
                            width=12,
                            order=order,
                        )
                    )
                    order += 1

        # 7. Heatmap (if we have 2 categorical + 1 numeric)
        if len(dimension_cols) >= 2 and metric_cols:
            charts.append(
                self._make_chart(
                    chart_type="heatmap",
                    title=f"{self._label(metric_cols[0])} Heatmap: {self._label(dimension_cols[0])} Ã— {self._label(dimension_cols[1])}",
                    section=LayoutSection.SUPPORTING_CHARTS.value,
                    x_axis=dimension_cols[0],
                    y_axis=dimension_cols[1],
                    z_axis=metric_cols[0],
                    aggregation="sum",
                    source_columns=[dimension_cols[0], dimension_cols[1], metric_cols[0]],
                    confidence=0.6,
                    reasoning=f"Heatmap: {self._label(metric_cols[0])} across {self._label(dimension_cols[0])} and {self._label(dimension_cols[1])}",
                    width=6,
                    order=order,
                )
            )
            order += 1

        # 8. Leaderboard (top N entities)
        if entity_cols and metric_cols:
            charts.append(
                self._make_chart(
                    chart_type="leaderboard",
                    title=f"Top {self._label(entity_cols[0])}s by {self._label(metric_cols[0])}",
                    section=LayoutSection.SUPPORTING_CHARTS.value,
                    x_axis=entity_cols[0],
                    y_axis=metric_cols[0],
                    aggregation="sum",
                    source_columns=[entity_cols[0], metric_cols[0]],
                    confidence=0.7,
                    reasoning=f"Ranking: top entities by {self._label(metric_cols[0])}",
                    width=6,
                    order=order,
                )
            )
            order += 1

        # Sort by confidence and limit
        charts.sort(key=lambda c: c.confidence, reverse=True)
        charts = charts[:max_charts]

        # Re-order after filtering
        for i, chart in enumerate(charts):
            chart.order = i

        return charts

    def recommend_replacement(
        self,
        current_type: str,
        available_types: list[str],
        context: dict | None = None,
    ) -> str | None:
        """Recommend a replacement chart type.

        Args:
            current_type: Current chart type.
            available_types: List of available chart types.
            context: Optional context (data types, cardinality, etc.).

        Returns:
            Recommended replacement type or None.
        """
        # Similar chart types for replacement
        similar: dict[str, list[str]] = {
            "bar_chart": ["horizontal_bar", "leaderboard", "pie_chart"],
            "horizontal_bar": ["bar_chart", "leaderboard"],
            "pie_chart": ["donut_chart", "bar_chart"],
            "donut_chart": ["pie_chart", "bar_chart"],
            "line_chart": ["forecast", "bar_chart"],
            "scatter_plot": ["heatmap", "line_chart"],
            "histogram": ["bar_chart", "donut_chart"],
            "heatmap": ["scatter_plot", "bar_chart"],
            "leaderboard": ["horizontal_bar", "bar_chart"],
            "gauge": ["bar_chart"],
        }

        candidates = similar.get(current_type, [])
        for candidate in candidates:
            if candidate in available_types:
                return candidate
        return None

    # â”€â”€ Helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    @staticmethod
    def _make_chart(
        chart_type: str,
        title: str,
        section: str,
        x_axis: str | None = None,
        y_axis: str | None = None,
        z_axis: str | None = None,
        group_by: str | None = None,
        aggregation: str = "sum",
        source_columns: list[str] | None = None,
        confidence: float = 1.0,
        reasoning: str = "",
        width: int = 6,
        height: int = 300,
        order: int = 0,
    ) -> ChartDefinition:
        return ChartDefinition(
            id=str(uuid.uuid4()),
            chart_type=chart_type,
            title=title,
            section=section,
            x_axis=x_axis,
            y_axis=y_axis,
            z_axis=z_axis,
            group_by=group_by,
            aggregation=aggregation,
            source_columns=source_columns or [],
            confidence=confidence,
            reasoning=reasoning,
            width=width,
            height=height,
            order=order,
        )

    @staticmethod
    def _label(col: str) -> str:
        return col.replace("_", " ").title()

    @staticmethod
    def _find_geo_columns(col_mapping: dict, categorical_cols: list[str]) -> list[str]:
        geo_entities = {"region", "country", "city", "state", "district", "location", "branch"}
        return [
            col
            for col, ent in col_mapping.items()
            if ent in geo_entities and col in categorical_cols
        ]

    @staticmethod
    def _find_metric_columns(
        df: pd.DataFrame, col_mapping: dict, numeric_cols: list[str]
    ) -> list[str]:
        """Find columns that serve as metrics (measures)."""
        metric_entities = {
            "revenue",
            "expense",
            "offering",
            "tithe",
            "donation",
            "billing",
            "production",
            "downtime",
            "crop",
            "livestock",
            "weather",
            "transaction",
            "loan",
            "card",
            "claim",
            "policy",
            "reservation",
            "room",
            "service",
            "call",
            "data_usage",
        }
        semantic_metrics = [col for col, ent in col_mapping.items() if ent in metric_entities]
        # Add all numeric columns that aren't IDs
        numeric_metrics = [
            col
            for col in numeric_cols
            if not col.lower().endswith("_id") and not col.lower().endswith("_no")
        ]
        # Combine, prioritizing semantic metrics
        seen = set()
        result = []
        for col in semantic_metrics + numeric_metrics:
            if col not in seen:
                seen.add(col)
                result.append(col)
        return result[:6]  # Limit

    @staticmethod
    def _find_dimension_columns(col_mapping: dict, categorical_cols: list[str]) -> list[str]:
        """Find columns that serve as dimensions."""
        dimension_entities = {
            "region",
            "department",
            "department_edu",
            "ward",
            "course",
            "diagnosis",
            "event",
            "product",
            "program",
            "project",
            "category",
            "branch_church",
            "ministry",
            "plan",
        }
        semantic_dims = [col for col, ent in col_mapping.items() if ent in dimension_entities]
        # Add categorical columns with reasonable cardinality
        for col in categorical_cols:
            if col not in semantic_dims and not col.lower().endswith("_id"):
                semantic_dims.append(col)
        return semantic_dims[:6]

    @staticmethod
    def _find_entity_columns(col_mapping: dict) -> list[str]:
        """Find columns that represent business entities."""
        entity_entities = {
            "patient",
            "student",
            "member",
            "customer",
            "donor",
            "beneficiary",
            "citizen",
            "account",
            "subscriber",
            "guest",
            "doctor",
            "teacher",
            "agent",
            "supplier",
        }
        return [col for col, ent in col_mapping.items() if ent in entity_entities]
