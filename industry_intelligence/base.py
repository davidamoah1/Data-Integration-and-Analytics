"""Base classes for industry-specific analytics.

Every sector analytics module inherits from IndustryAnalytics and implements
analyze() to produce an AnalyticsResult with sector-specific insights.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd


@dataclass
class Insight:
    """A single analytics insight."""

    title: str
    value: Any
    formatted: str
    category: str  # operational, financial, clinical, academic, risk, etc.
    description: str = ""
    alert: str | None = None  # "ok", "warning", "critical"

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "value": self.value,
            "formatted": self.formatted,
            "category": self.category,
            "description": self.description,
            "alert": self.alert,
        }


@dataclass
class Breakdown:
    """A dimension breakdown for a metric."""

    dimension: str
    values: dict[str, float]  # {category_value: metric_value}
    metric: str = ""
    aggregation: str = "sum"

    def to_dict(self) -> dict:
        return {
            "dimension": self.dimension,
            "metric": self.metric,
            "aggregation": self.aggregation,
            "values": {str(k): v for k, v in self.values.items()},
        }


@dataclass
class Trend:
    """A time series trend."""

    periods: list[str]
    values: list[float]
    metric: str = ""
    direction: str = "stable"  # "up", "down", "stable"

    def to_dict(self) -> dict:
        return {
            "metric": self.metric,
            "periods": self.periods,
            "values": self.values,
            "direction": self.direction,
        }


@dataclass
class AnalyticsResult:
    """Result of industry-specific analytics computation."""

    industry: str
    insights: list[Insight] = field(default_factory=list)
    breakdowns: list[Breakdown] = field(default_factory=list)
    trends: list[Trend] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    alerts: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "industry": self.industry,
            "insights": [i.to_dict() for i in self.insights],
            "breakdowns": [b.to_dict() for b in self.breakdowns],
            "trends": [t.to_dict() for t in self.trends],
            "recommendations": self.recommendations,
            "alerts": self.alerts,
        }

    def get_insight(self, title: str) -> Insight | None:
        for i in self.insights:
            if i.title == title:
                return i
        return None


class IndustryAnalytics:
    """Base class for industry-specific analytics.

    Each subclass implements analyze() to produce sector-specific insights.
    The base class provides helpers for finding columns, computing
    aggregations, and formatting values.
    """

    industry: str = "unknown"

    @classmethod
    def analyze(cls, df: pd.DataFrame, col_mapping: dict[str, str] | None = None) -> AnalyticsResult:
        """Run industry-specific analytics on a DataFrame.

        Args:
            df: The DataFrame to analyze.
            col_mapping: Mapping of column names to entity keys
                         (from SemanticResult.get_column_mapping()).

        Returns:
            AnalyticsResult with insights, breakdowns, trends, and alerts.
        """
        raise NotImplementedError

    # ── Helpers ──────────────────────────────────────────

    @staticmethod
    def _find_col(
        df: pd.DataFrame, col_mapping: dict | None, entity_keys: list[str]
    ) -> str | None:
        """Find a column by entity key mapping or by name heuristic."""
        if col_mapping:
            for col, entity in col_mapping.items():
                if entity in entity_keys and col in df.columns:
                    return col
        # Fallback: search by column name
        lower_map = {c.lower(): c for c in df.columns}
        for key in entity_keys:
            if key in lower_map:
                return lower_map[key]
            for col_lower, col in lower_map.items():
                if key in col_lower:
                    return col
        return None

    @staticmethod
    def _find_numeric_col(
        df: pd.DataFrame, col_mapping: dict | None, entity_keys: list[str]
    ) -> str | None:
        """Find a numeric column by entity key or name."""
        if col_mapping:
            for col, entity in col_mapping.items():
                if entity in entity_keys and col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
                    return col
        # Fallback: search by column name for numeric columns
        lower_map = {c.lower(): c for c in df.columns}
        for key in entity_keys:
            if key in lower_map and pd.api.types.is_numeric_dtype(df[lower_map[key]]):
                return lower_map[key]
            for col_lower, col in lower_map.items():
                if key in col_lower and pd.api.types.is_numeric_dtype(df[col]):
                    return col
        return None

    @staticmethod
    def _find_date_col(df: pd.DataFrame, col_mapping: dict | None) -> str | None:
        """Find a date/datetime column."""
        if col_mapping:
            for col, entity in col_mapping.items():
                if entity == "date" and col in df.columns:
                    return col
        # Fallback: search by dtype
        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                return col
        # Fallback: search by name
        lower_map = {c.lower(): c for c in df.columns}
        for name in ("date", "visit_date", "order_date", "transaction_date", "created_at"):
            if name in lower_map:
                return lower_map[name]
        return None

    @staticmethod
    def _fmt_currency(v: float) -> str:
        if abs(v) >= 1_000_000:
            return f"${v / 1_000_000:.1f}M"
        elif abs(v) >= 1_000:
            return f"${v / 1_000:.1f}K"
        return f"${v:,.0f}"

    @staticmethod
    def _fmt_number(v: float) -> str:
        if abs(v) >= 1_000_000:
            return f"{v / 1_000_000:.1f}M"
        elif abs(v) >= 1_000:
            return f"{v / 1_000:.1f}K"
        return f"{v:,.0f}"

    @staticmethod
    def _fmt_pct(v: float) -> str:
        return f"{v:.1f}%"

    @staticmethod
    def _compute_trend(
        df: pd.DataFrame, date_col: str, metric_col: str, aggregation: str = "sum"
    ) -> Trend | None:
        """Compute a monthly trend for a metric."""
        try:
            if not pd.api.types.is_datetime64_any_dtype(df[date_col]):
                df_temp = df.copy()
                df_temp[date_col] = pd.to_datetime(df_temp[date_col], errors="coerce")
                df_temp = df_temp.dropna(subset=[date_col])
            else:
                df_temp = df

            if df_temp.empty:
                return None

            df_temp = df_temp.copy()
            df_temp["_period"] = df_temp[date_col].dt.to_period("M").astype(str)

            if aggregation == "sum" and pd.api.types.is_numeric_dtype(df_temp[metric_col]):
                grouped = df_temp.groupby("_period")[metric_col].sum()
            elif aggregation == "count":
                grouped = df_temp.groupby("_period")[metric_col].nunique()
            elif aggregation == "mean" and pd.api.types.is_numeric_dtype(df_temp[metric_col]):
                grouped = df_temp.groupby("_period")[metric_col].mean()
            else:
                grouped = df_temp.groupby("_period").size()

            if len(grouped) < 2:
                return None

            periods = list(grouped.index.astype(str))
            values = [float(v) for v in grouped.values]

            # Determine direction
            if len(values) >= 2:
                first_half = sum(values[: len(values) // 2]) / max(len(values) // 2, 1)
                second_half = sum(values[len(values) // 2 :]) / max(
                    len(values) - len(values) // 2, 1
                )
                if second_half > first_half * 1.05:
                    direction = "up"
                elif second_half < first_half * 0.95:
                    direction = "down"
                else:
                    direction = "stable"
            else:
                direction = "stable"

            return Trend(periods=periods, values=values, metric=metric_col, direction=direction)
        except Exception:
            return None

    @staticmethod
    def _compute_breakdown(
        df: pd.DataFrame, group_col: str, metric_col: str, aggregation: str = "sum", top_n: int = 10
    ) -> Breakdown | None:
        """Compute a breakdown of a metric by a dimension."""
        try:
            if group_col not in df.columns or metric_col not in df.columns:
                return None

            if aggregation == "sum" and pd.api.types.is_numeric_dtype(df[metric_col]):
                grouped = df.groupby(group_col)[metric_col].sum()
            elif aggregation == "count":
                grouped = df.groupby(group_col)[metric_col].nunique()
            elif aggregation == "mean" and pd.api.types.is_numeric_dtype(df[metric_col]):
                grouped = df.groupby(group_col)[metric_col].mean()
            else:
                grouped = df.groupby(group_col)[metric_col].nunique()

            grouped = grouped.sort_values(ascending=False).head(top_n)
            values = {str(k): float(v) for k, v in grouped.items()}

            if not values:
                return None

            return Breakdown(
                dimension=group_col,
                values=values,
                metric=metric_col,
                aggregation=aggregation,
            )
        except Exception:
            return None


class IndustryAnalyticsRegistry:
    """Registry for industry-specific analytics engines."""

    _engines: dict[str, type[IndustryAnalytics]] = {}

    @classmethod
    def register(cls, industry: str, engine: type[IndustryAnalytics]) -> None:
        cls._engines[industry] = engine

    @classmethod
    def get(cls, industry: str) -> type[IndustryAnalytics] | None:
        return cls._engines.get(industry)

    @classmethod
    def industries(cls) -> list[str]:
        return sorted(cls._engines.keys())

    @classmethod
    def analyze(cls, industry: str, df: pd.DataFrame, col_mapping: dict | None = None) -> AnalyticsResult | None:
        engine = cls.get(industry)
        if engine is None:
            return None
        return engine.analyze(df, col_mapping)
