"""Metric Engine — computes business metrics from a SemanticModel + DataFrame.

Goes beyond simple KPIs to compute:
  - Aggregations (sum, count, avg, min, max, distinct_count)
  - Time-based trends (period-over-period change)
  - Group-by breakdowns (by dimension)
  - Ratios and derived metrics
  - Statistical summaries

The MetricEngine is the computational layer that turns semantic
understanding into actual numbers on the dashboard.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from semantic.semantic_model import (
    MetricDefinition,
    SemanticModel,
)


@dataclass
class MetricResult:
    """Result of a single metric computation."""

    key: str
    label: str
    value: float
    formatted: str
    category: str
    entity: str
    aggregation: str
    breakdown: dict | None = None  # dimension → {value: metric_value}
    trend: list[dict] | None = None  # [{period: "2024-01", value: 1234}, ...]
    definition: str = ""
    threshold: dict | None = None
    alert: str | None = None  # "ok", "warning", "critical"

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "label": self.label,
            "value": self.value,
            "formatted": self.formatted,
            "category": self.category,
            "entity": self.entity,
            "aggregation": self.aggregation,
            "breakdown": self.breakdown,
            "trend": self.trend,
            "definition": self.definition,
            "threshold": self.threshold,
            "alert": self.alert,
        }


@dataclass
class MetricResultSet:
    """A complete set of computed metrics for a dataset."""

    metrics: list[MetricResult] = field(default_factory=list)
    dataset: str = ""
    domain: str = ""

    def to_dict(self) -> dict:
        return {
            "dataset": self.dataset,
            "domain": self.domain,
            "metrics": [m.to_dict() for m in self.metrics],
        }

    def get(self, key: str) -> MetricResult | None:
        for m in self.metrics:
            if m.key == key:
                return m
        return None

    def by_category(self, category: str) -> list[MetricResult]:
        return [m for m in self.metrics if m.category == category]

    def categories(self) -> list[str]:
        return sorted({m.category for m in self.metrics})


def _fmt_currency(v: float) -> str:
    if abs(v) >= 1_000_000:
        return f"${v / 1_000_000:.1f}M"
    elif abs(v) >= 1_000:
        return f"${v / 1_000:.1f}K"
    return f"${v:,.0f}"


def _fmt_number(v: float) -> str:
    if abs(v) >= 1_000_000:
        return f"{v / 1_000_000:.1f}M"
    elif abs(v) >= 1_000:
        return f"{v / 1_000:.1f}K"
    return f"{v:,.0f}"


def _fmt_pct(v: float) -> str:
    return f"{v:.1f}%"


class MetricEngine:
    """Computes business metrics from a SemanticModel and DataFrame.

    This is the engine that turns "patient_id column → Patient entity"
    into "patient_count = 1,247 unique patients" and then breaks it
    down by region, trends it over time, and checks it against thresholds.
    """

    @classmethod
    def compute(
        cls,
        df: pd.DataFrame,
        model: SemanticModel,
        include_breakdowns: bool = True,
        include_trends: bool = True,
    ) -> MetricResultSet:
        """Compute all metrics for a dataset.

        Args:
            df: The DataFrame to compute metrics from.
            model: The SemanticModel describing the dataset.
            include_breakdowns: Whether to compute dimension breakdowns.
            include_trends: Whether to compute time trends.

        Returns:
            MetricResultSet with all computed metrics.
        """
        results: list[MetricResult] = []

        # Compute each metric defined in the model
        for metric_def in model.metrics:
            result = cls._compute_metric(df, model, metric_def, include_breakdowns, include_trends)
            if result:
                results.append(result)

        # Compute additional derived metrics
        derived = cls._compute_derived_metrics(df, model, include_breakdowns, include_trends)
        results.extend(derived)

        return MetricResultSet(
            metrics=results,
            dataset=model.dataset,
            domain=model.domain,
        )

    @classmethod
    def _compute_metric(
        cls,
        df: pd.DataFrame,
        model: SemanticModel,
        metric_def: MetricDefinition,
        include_breakdowns: bool,
        include_trends: bool,
    ) -> MetricResult | None:
        """Compute a single metric from its definition."""
        value = metric_def.value if metric_def.value is not None else 0.0
        formatted = metric_def.formatted or _fmt_number(value)

        # Determine alert level
        alert = cls._check_threshold(value, metric_def.threshold)

        # Compute breakdowns by each dimension
        breakdown = None
        if include_breakdowns and metric_def.column:
            breakdown = cls._compute_breakdown(df, model, metric_def)

        # Compute trend over time
        trend = None
        if include_trends:
            trend = cls._compute_trend(df, model, metric_def)

        return MetricResult(
            key=metric_def.key,
            label=metric_def.label,
            value=value,
            formatted=formatted,
            category=metric_def.category,
            entity=metric_def.entity,
            aggregation=metric_def.aggregation,
            breakdown=breakdown,
            trend=trend,
            definition=metric_def.definition,
            threshold=metric_def.threshold,
            alert=alert,
        )

    @classmethod
    def _compute_breakdown(
        cls, df: pd.DataFrame, model: SemanticModel, metric_def: MetricDefinition
    ) -> dict | None:
        """Compute metric broken down by each dimension."""
        if not metric_def.column or metric_def.column not in df.columns:
            return None

        breakdowns: dict[str, dict] = {}

        for dim in model.dimensions:
            if dim.column not in df.columns or dim.column == metric_def.column:
                continue

            try:
                if metric_def.aggregation == "count":
                    grouped = df.groupby(dim.column)[metric_def.column].nunique()
                elif metric_def.aggregation == "sum":
                    if not pd.api.types.is_numeric_dtype(df[metric_def.column]):
                        continue
                    grouped = df.groupby(dim.column)[metric_def.column].sum()
                elif metric_def.aggregation == "avg":
                    if not pd.api.types.is_numeric_dtype(df[metric_def.column]):
                        continue
                    grouped = df.groupby(dim.column)[metric_def.column].mean()
                else:
                    grouped = df.groupby(dim.column)[metric_def.column].nunique()

                if len(grouped) > 0:
                    # Sort descending, take top 10
                    grouped = grouped.sort_values(ascending=False).head(10)
                    breakdowns[dim.key] = {str(k): float(v) for k, v in grouped.items()}
            except Exception:
                continue

        return breakdowns if breakdowns else None

    @classmethod
    def _compute_trend(
        cls, df: pd.DataFrame, model: SemanticModel, metric_def: MetricDefinition
    ) -> list[dict] | None:
        """Compute metric trended over time (by date dimension)."""
        date_dim = None
        for dim in model.dimensions:
            if dim.key == "date":
                date_dim = dim
                break

        if not date_dim or not date_dim.column or date_dim.column not in df.columns:
            return None

        date_col = date_dim.column
        metric_col = metric_def.column

        # If no explicit column, try to find a suitable numeric column
        if not metric_col or metric_col not in df.columns:
            if metric_def.aggregation == "count":
                # For count metrics, trend the row count per period
                metric_col = None
            else:
                # Try to find a numeric column related to the entity
                for entity in model.entities:
                    if entity.key == metric_def.entity:
                        for col in entity.columns:
                            if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
                                metric_col = col
                                break
                        break
                if not metric_col:
                    return None

        try:
            # Ensure date column is datetime
            if not pd.api.types.is_datetime64_any_dtype(df[date_col]):
                df_temp = df.copy()
                df_temp[date_col] = pd.to_datetime(df_temp[date_col], errors="coerce")
                df_temp = df_temp.dropna(subset=[date_col])
            else:
                df_temp = df

            if df_temp.empty:
                return None

            # Group by month for trend
            df_temp = df_temp.copy()
            df_temp["_period"] = df_temp[date_col].dt.to_period("M").astype(str)

            if metric_col is None:
                # Count rows per period
                grouped = df_temp.groupby("_period").size()
            elif metric_def.aggregation == "count":
                grouped = df_temp.groupby("_period")[metric_col].nunique()
            elif metric_def.aggregation == "sum":
                if not pd.api.types.is_numeric_dtype(df_temp[metric_col]):
                    return None
                grouped = df_temp.groupby("_period")[metric_col].sum()
            else:
                grouped = df_temp.groupby("_period")[metric_col].nunique()

            if len(grouped) < 2:
                return None

            return [{"period": str(idx), "value": float(val)} for idx, val in grouped.items()]
        except Exception:
            return None

    @classmethod
    def _compute_derived_metrics(
        cls,
        df: pd.DataFrame,
        model: SemanticModel,
        include_breakdowns: bool,
        include_trends: bool,
    ) -> list[MetricResult]:
        """Compute derived metrics that aren't in the base KPI set."""
        derived: list[MetricResult] = []

        # Row count
        derived.append(
            MetricResult(
                key="record_count",
                label="Total Records",
                value=float(len(df)),
                formatted=_fmt_number(len(df)),
                category="operational",
                entity="universal",
                aggregation="count",
                definition="Total number of data records (rows) in the dataset.",
            )
        )

        # Column count
        derived.append(
            MetricResult(
                key="column_count",
                label="Total Columns",
                value=float(len(df.columns)),
                formatted=str(len(df.columns)),
                category="operational",
                entity="universal",
                aggregation="count",
                definition="Total number of columns (attributes) in the dataset.",
            )
        )

        # Completeness
        total_cells = len(df) * len(df.columns) if len(df.columns) > 0 else 0
        if total_cells > 0:
            null_cells = int(df.isnull().sum().sum())
            completeness = ((total_cells - null_cells) / total_cells) * 100
            derived.append(
                MetricResult(
                    key="data_completeness",
                    label="Data Completeness",
                    value=completeness,
                    formatted=_fmt_pct(completeness),
                    category="quality",
                    entity="universal",
                    aggregation="avg",
                    definition="Percentage of non-null cells across all columns.",
                )
            )

        # Duplicate rate
        dup_count = int(df.duplicated().sum())
        if len(df) > 0:
            dup_rate = (dup_count / len(df)) * 100
            derived.append(
                MetricResult(
                    key="duplicate_rate",
                    label="Duplicate Rate",
                    value=dup_rate,
                    formatted=_fmt_pct(dup_rate),
                    category="quality",
                    entity="universal",
                    aggregation="avg",
                    definition="Percentage of duplicate rows in the dataset.",
                )
            )

        # Numeric column averages (if any numeric columns exist)
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            # Skip ID-like columns (sequential integers)
            if col.lower().endswith("_id") or col.lower() == "id":
                continue

            non_null = df[col].dropna()
            if len(non_null) == 0:
                continue

            avg_val = float(non_null.mean())
            # Determine if monetary
            col_lower = col.lower()
            is_monetary = any(
                kw in col_lower
                for kw in (
                    "amount",
                    "revenue",
                    "sales",
                    "price",
                    "cost",
                    "fee",
                    "billing",
                    "balance",
                    "profit",
                    "income",
                    "salary",
                    "tuition",
                    "offering",
                    "tithe",
                    "donation",
                    "premium",
                )
            )

            fmt = _fmt_currency(avg_val) if is_monetary else _fmt_number(avg_val)

            derived.append(
                MetricResult(
                    key=f"avg_{col}",
                    label=f"Avg {col.replace('_', ' ').title()}",
                    value=avg_val,
                    formatted=fmt,
                    category="statistical",
                    entity="universal",
                    aggregation="avg",
                    definition=f"Average value of the {col} column across all records.",
                )
            )

        return derived

    @staticmethod
    def _check_threshold(value: float, threshold: dict | None) -> str | None:
        """Check a metric value against its threshold and return alert level."""
        if not threshold:
            return None

        # Thresholds can be ">X" or "<X" format
        warning = threshold.get("warning")
        critical = threshold.get("critical")

        if critical is not None and isinstance(critical, (int, float)):
            if value >= critical:
                return "critical"

        if warning is not None and isinstance(warning, (int, float)) and value >= warning:
            return "warning"

        return "ok"
