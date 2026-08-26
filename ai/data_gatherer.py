"""Shared Data Gatherer â€” semantic-aware data gathering for AI engines.

Replaces the hardcoded sales queries in decision_center.py, report_writer.py,
dashboard_insights.py, and kpi_engine.py with a unified, dataset-agnostic
approach that works with any DataFrame via semantic mappings.
"""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd

from ai.context_engine import EnterpriseAIContext

logger = logging.getLogger(__name__)


class DataGatherer:
    """Gathers and structures data from any dataset using semantic mappings."""

    def __init__(self, df: pd.DataFrame | None = None, context: EnterpriseAIContext | None = None):
        self.df = df
        self.context = context

    def gather_for_summary(self) -> dict:
        """Gather data suitable for executive summary generation."""
        if self.df is None or self.df.empty:
            return {"note": "No data available"}

        data: dict[str, Any] = {"data_sources": [{"source": "dataset", "records": len(self.df)}]}

        # Overall summary
        data["overall"] = self._overall_summary()

        # By dimension (categorical columns)
        data["by_dimension"] = self._by_dimension()

        # Time trends
        data["time_trends"] = self._time_trends()

        # Top contributors
        data["top_contributors"] = self._top_contributors()

        # Numeric column statistics
        data["numeric_stats"] = self._numeric_stats()

        return data

    def gather_for_root_cause(self, metric: str, direction: str = "decrease") -> dict:
        """Gather data for root cause analysis.

        Args:
            metric: The metric that changed (e.g., 'revenue', 'billing_amount').
            direction: Whether it increased or decreased.
        """
        if self.df is None or self.df.empty:
            return {"note": "No data available"}

        data: dict[str, Any] = {
            "metric": metric,
            "direction": direction,
            "data_sources": [{"source": "dataset", "records": len(self.df)}],
        }

        # Find the metric column
        metric_col = self._find_metric_column(metric)
        if not metric_col:
            data["note"] = f"Could not find column for metric: {metric}"
            return data

        # Overall metric stats
        data["metric_stats"] = {
            "total": (
                float(self.df[metric_col].sum())
                if pd.api.types.is_numeric_dtype(self.df[metric_col])
                else None
            ),
            "mean": (
                float(self.df[metric_col].mean())
                if pd.api.types.is_numeric_dtype(self.df[metric_col])
                else None
            ),
            "count": int(self.df[metric_col].count()),
        }

        # Contribution by each dimension
        data["contributions"] = self._contribution_analysis(metric_col)

        # Period comparison (if date column exists)
        data["period_comparison"] = self._period_comparison(metric_col)

        # Correlation with other numeric columns
        data["correlations"] = self._correlation_analysis(metric_col)

        return data

    def gather_for_trend(self, metric: str) -> dict:
        """Gather data for trend analysis."""
        if self.df is None or self.df.empty:
            return {"note": "No data available"}

        metric_col = self._find_metric_column(metric)
        if not metric_col:
            return {"note": f"Could not find column for metric: {metric}"}

        data: dict[str, Any] = {"metric": metric, "column": metric_col}

        # Time-based aggregation
        date_col = self._find_date_column()
        if date_col:
            df = self.df.copy()
            df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
            df = df.dropna(subset=[date_col, metric_col])

            if not df.empty:
                # Monthly trend
                df["period"] = df[date_col].dt.to_period("M")
                monthly = df.groupby("period")[metric_col].sum().sort_index()
                data["monthly_trend"] = [
                    {"period": str(p), "value": float(v)} for p, v in monthly.items()
                ]

                # Last vs previous period
                if len(monthly) >= 2:
                    current = float(monthly.iloc[-1])
                    previous = float(monthly.iloc[-2])
                    change = current - previous
                    pct_change = (change / previous * 100) if previous != 0 else 0
                    data["period_comparison"] = {
                        "current_period": str(monthly.index[-1]),
                        "previous_period": str(monthly.index[-2]),
                        "current_value": round(current, 2),
                        "previous_value": round(previous, 2),
                        "absolute_change": round(change, 2),
                        "percentage_change": round(pct_change, 2),
                    }

                # Weekly trend (if enough data)
                if len(df) >= 14:
                    df["week"] = df[date_col].dt.to_period("W")
                    weekly = df.groupby("week")[metric_col].sum().sort_index()
                    data["weekly_trend"] = [
                        {"period": str(p), "value": float(v)} for p, v in weekly.items()
                    ]

        # Overall trend direction
        if "monthly_trend" in data and len(data["monthly_trend"]) >= 2:
            values = [d["value"] for d in data["monthly_trend"]]
            data["trend_direction"] = "increasing" if values[-1] > values[0] else "decreasing"
            data["total_change"] = round(values[-1] - values[0], 2)
            data["total_pct_change"] = round(
                ((values[-1] - values[0]) / values[0] * 100) if values[0] != 0 else 0, 2
            )

        return data

    def gather_for_forecast(self, metric: str, horizon: int = 30) -> dict:
        """Gather and prepare time series for forecasting."""
        if self.df is None or self.df.empty:
            return {"note": "No data available"}

        metric_col = self._find_metric_column(metric)
        date_col = self._find_date_column()

        if not metric_col or not date_col:
            return {"note": "Could not find metric or date column"}

        df = self.df.copy()
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        df = df.dropna(subset=[date_col, metric_col])

        if df.empty:
            return {"note": "No valid time series data"}

        # Aggregate by date
        ts = df.groupby(date_col)[metric_col].sum().sort_index()
        data = {
            "metric": metric,
            "column": metric_col,
            "date_column": date_col,
            "data_points": len(ts),
            "date_range": [str(ts.index[0].date()), str(ts.index[-1].date())],
            "values": [float(v) for v in ts.values],
            "dates": [str(d.date()) for d in ts.index],
            "mean": float(ts.mean()),
            "std": float(ts.std()),
            "min": float(ts.min()),
            "max": float(ts.max()),
            "trend": "increasing" if ts.iloc[-1] > ts.iloc[0] else "decreasing",
            "horizon": horizon,
        }

        return data

    def gather_for_anomaly(self, metric: str) -> dict:
        """Gather data for anomaly detection."""
        if self.df is None or self.df.empty:
            return {"note": "No data available"}

        metric_col = self._find_metric_column(metric)
        if not metric_col:
            return {"note": f"Could not find column for metric: {metric}"}

        date_col = self._find_date_column()
        data: dict[str, Any] = {
            "metric": metric,
            "column": metric_col,
        }

        if date_col:
            df = self.df.copy()
            df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
            df = df.dropna(subset=[date_col, metric_col])
            ts = df.groupby(date_col)[metric_col].sum().sort_index()

            data["time_series"] = [
                {"date": str(d.date()), "value": float(v)} for d, v in ts.items()
            ]
            data["stats"] = {
                "mean": float(ts.mean()),
                "std": float(ts.std()),
                "min": float(ts.min()),
                "max": float(ts.max()),
            }
        else:
            values = self.df[metric_col].dropna()
            data["values"] = [float(v) for v in values]
            data["stats"] = {
                "mean": float(values.mean()),
                "std": float(values.std()),
                "min": float(values.min()),
                "max": float(values.max()),
            }

        return data

    def gather_for_report(self, report_type: str = "executive") -> dict:
        """Gather comprehensive data for report generation."""
        if self.df is None or self.df.empty:
            return {"note": "No data available"}

        data = self.gather_for_summary()
        data["report_type"] = report_type
        data["dataset_info"] = {
            "row_count": len(self.df),
            "column_count": len(self.df.columns),
            "columns": list(self.df.columns),
        }

        if self.context and self.context.dataset.semantic_mappings:
            data["semantic_mappings"] = self.context.dataset.semantic_mappings

        if self.context and self.context.industry.industry != "unknown":
            data["industry"] = self.context.industry.to_dict()

        return data

    # â”€â”€ Private helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def _find_metric_column(self, metric: str) -> str | None:
        """Find the column name for a given metric."""
        if self.df is None:
            return None

        metric_lower = metric.lower().replace(" ", "_")

        # Check semantic mappings
        if self.context and self.context.dataset.semantic_mappings:
            for col, role in self.context.dataset.semantic_mappings.items():
                if role == metric_lower or metric_lower in role or role in metric_lower:
                    if col in self.df.columns:
                        return col

        # Direct column match
        if metric in self.df.columns:
            return metric

        # Fuzzy match
        for col in self.df.columns:
            if metric_lower in col.lower() or col.lower() in metric_lower:
                return col

        # Try common revenue/sales columns
        for candidate in [metric_lower, "sales", "revenue", "billing_amount", "amount", "total"]:
            if candidate in self.df.columns:
                return candidate

        # First numeric column
        for col in self.df.columns:
            if pd.api.types.is_numeric_dtype(self.df[col]):
                return col

        return None

    def _find_date_column(self) -> str | None:
        """Find the date column in the dataset."""
        if self.df is None:
            return None

        # Check semantic mappings
        if self.context and self.context.dataset.semantic_mappings:
            for col, role in self.context.dataset.semantic_mappings.items():
                if (role == "date" or "date" in role) and col in self.df.columns:
                    return col

        # Check known date columns
        if self.context and self.context.dataset.date_columns:
            for col in self.context.dataset.date_columns:
                if col in self.df.columns:
                    return col

        # Try common date column names
        for candidate in ["date", "order_date", "admission_date", "created_at", "timestamp"]:
            if candidate in self.df.columns:
                return candidate

        # Check datetime columns
        for col in self.df.columns:
            if pd.api.types.is_datetime64_any_dtype(self.df[col]):
                return col

        return None

    def _overall_summary(self) -> dict:
        """Generate overall dataset summary."""
        if self.df is None:
            return {}

        summary: dict[str, Any] = {
            "row_count": len(self.df),
            "column_count": len(self.df.columns),
        }

        # Numeric column sums
        for col in self.df.columns:
            if pd.api.types.is_numeric_dtype(self.df[col]):
                summary[f"total_{col}"] = float(self.df[col].sum())
                summary[f"avg_{col}"] = float(self.df[col].mean())

        # Categorical column cardinalities
        for col in self.df.columns:
            if not pd.api.types.is_numeric_dtype(self.df[col]):
                summary[f"unique_{col}"] = int(self.df[col].nunique())

        return summary

    def _by_dimension(self, max_dims: int = 5) -> dict:
        """Break down numeric metrics by categorical dimensions."""
        if self.df is None:
            return {}

        result = {}
        numeric_cols = [c for c in self.df.columns if pd.api.types.is_numeric_dtype(self.df[c])]
        categorical_cols = [
            c
            for c in self.df.columns
            if not pd.api.types.is_numeric_dtype(self.df[c])
            and self.df[c].nunique() <= 20
            and c not in self._find_date_column_safe()
        ]

        for cat_col in categorical_cols[:max_dims]:
            for num_col in numeric_cols[:3]:
                grouped = self.df.groupby(cat_col)[num_col].sum().sort_values(ascending=False)
                result[f"{num_col}_by_{cat_col}"] = [
                    {cat_col: str(k), num_col: float(v)} for k, v in grouped.head(10).items()
                ]

        return result

    def _time_trends(self) -> dict:
        """Generate time-based trends."""
        if self.df is None:
            return {}

        date_col = self._find_date_column()
        if not date_col:
            return {}

        df = self.df.copy()
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        df = df.dropna(subset=[date_col])

        if df.empty:
            return {}

        trends = {}
        numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]

        for num_col in numeric_cols[:3]:
            df["period"] = df[date_col].dt.to_period("M")
            monthly = df.groupby("period")[num_col].sum().sort_index()
            trends[num_col] = [
                {"period": str(p), "value": float(v)} for p, v in monthly.tail(12).items()
            ]

        return trends

    def _top_contributors(self, n: int = 10) -> dict:
        """Identify top contributing items."""
        if self.df is None:
            return {}

        result = {}
        numeric_cols = [c for c in self.df.columns if pd.api.types.is_numeric_dtype(self.df[c])]
        categorical_cols = [
            c
            for c in self.df.columns
            if not pd.api.types.is_numeric_dtype(self.df[c])
            and self.df[c].nunique() <= 50
            and c not in self._find_date_column_safe()
        ]

        for cat_col in categorical_cols[:3]:
            for num_col in numeric_cols[:2]:
                grouped = self.df.groupby(cat_col)[num_col].sum().sort_values(ascending=False)
                total = grouped.sum()
                result[f"top_{cat_col}_by_{num_col}"] = [
                    {
                        cat_col: str(k),
                        num_col: float(v),
                        "share": round(float(v / total * 100), 2) if total != 0 else 0,
                    }
                    for k, v in grouped.head(n).items()
                ]

        return result

    def _numeric_stats(self) -> dict:
        """Generate statistics for numeric columns."""
        if self.df is None:
            return {}

        stats = {}
        for col in self.df.columns:
            if pd.api.types.is_numeric_dtype(self.df[col]):
                stats[col] = {
                    "sum": float(self.df[col].sum()),
                    "mean": float(self.df[col].mean()),
                    "std": float(self.df[col].std()),
                    "min": float(self.df[col].min()),
                    "max": float(self.df[col].max()),
                    "median": float(self.df[col].median()),
                }
        return stats

    def _contribution_analysis(self, metric_col: str) -> list[dict]:
        """Analyze contributions to a metric by each dimension."""
        if self.df is None:
            return []

        contributions = []
        categorical_cols = [
            c
            for c in self.df.columns
            if not pd.api.types.is_numeric_dtype(self.df[c])
            and self.df[c].nunique() <= 50
            and c not in self._find_date_column_safe()
        ]

        for cat_col in categorical_cols[:5]:
            grouped = self.df.groupby(cat_col)[metric_col].sum().sort_values(ascending=False)
            total = grouped.sum()
            for k, v in grouped.head(5).items():
                contributions.append(
                    {
                        "dimension": cat_col,
                        "value": str(k),
                        "metric_value": float(v),
                        "contribution_pct": round(float(v / total * 100), 2) if total != 0 else 0,
                    }
                )

        return contributions

    def _period_comparison(self, metric_col: str) -> dict:
        """Compare metric across time periods."""
        date_col = self._find_date_column()
        if not date_col or self.df is None:
            return {}

        df = self.df.copy()
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        df = df.dropna(subset=[date_col, metric_col])

        if df.empty:
            return {}

        df["period"] = df[date_col].dt.to_period("M")
        monthly = df.groupby("period")[metric_col].sum().sort_index()

        if len(monthly) < 2:
            return {}

        current = float(monthly.iloc[-1])
        previous = float(monthly.iloc[-2])
        change = current - previous
        pct_change = (change / previous * 100) if previous != 0 else 0

        return {
            "current_period": str(monthly.index[-1]),
            "previous_period": str(monthly.index[-2]),
            "current_value": round(current, 2),
            "previous_value": round(previous, 2),
            "absolute_change": round(change, 2),
            "percentage_change": round(pct_change, 2),
        }

    def _correlation_analysis(self, metric_col: str) -> dict:
        """Find correlations between the metric and other numeric columns."""
        if self.df is None:
            return {}

        correlations = {}
        numeric_cols = [
            c
            for c in self.df.columns
            if pd.api.types.is_numeric_dtype(self.df[c]) and c != metric_col
        ]

        for col in numeric_cols[:5]:
            try:
                corr = self.df[metric_col].corr(self.df[col])
                if not pd.isna(corr):
                    correlations[col] = round(float(corr), 3)
            except Exception as e:
                logger.debug("Correlation calculation failed for %s: %s", col, e)

        return correlations

    def _find_date_column_safe(self) -> list[str]:
        """Find date column(s) safely (returns list for `in` checks)."""
        col = self._find_date_column()
        return [col] if col else []
