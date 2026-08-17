"""Automatic KPI Engine.

Detects and computes meaningful KPIs from the dataset.  Unlike the
existing KPIIntelligenceEngine which only *detects* KPI templates,
this engine actually *computes* the values from the data.

Rules:
  - Total Records (COUNT) — always
  - Total of primary measure (SUM) — if a currency/measure exists
  - Average of primary measure (AVG) — if a currency/measure exists
  - Unique dimension count (COUNT DISTINCT) — for primary dimension
  - Date range span — if a time column exists
  - Growth rate — if time column + measure exist (period over period)
  - Top category share — if a dimension exists

Meaningless KPIs are rejected:
  - KPIs from identifier columns
  - KPIs from >80% missing columns
  - KPIs with no business interpretation
"""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd

from services.auto.analysis_engine import DatasetUnderstanding, SemanticRole
from services.auto.chart_specification import KPISpecification

logger = logging.getLogger(__name__)


class AutomaticKPIEngine:
    """Automatically detects and computes meaningful KPIs."""

    MAX_KPIS = 6

    def select_kpis(
        self,
        df: pd.DataFrame,
        understanding: DatasetUnderstanding,
    ) -> list[KPISpecification]:
        """Detect and compute KPIs from the dataset.

        Args:
            df: The dataset DataFrame.
            understanding: DatasetUnderstanding from AutomaticAnalysisEngine.

        Returns:
            List of KPISpecification objects with computed values.
        """
        kpis: list[KPISpecification] = []
        order = 0

        # 1. Total Records — always meaningful
        kpis.append(
            KPISpecification(
                key="total_records",
                label="Total Records",
                value=int(len(df)),
                unit="",
                metric="count",
                category="operational",
                source_columns=[],
                aggregation="count",
                confidence=1.0,
                icon="📋",
                description="Total number of records in the dataset",
                order=order,
            )
        )
        order += 1

        # 2. Column count
        kpis.append(
            KPISpecification(
                key="column_count",
                label="Data Columns",
                value=int(len(df.columns)),
                unit="",
                metric="count",
                category="operational",
                source_columns=[],
                aggregation="count",
                confidence=1.0,
                icon="📊",
                description="Number of columns in the dataset",
                order=order,
            )
        )
        order += 1

        # 3. Total of primary measure (currency/revenue)
        primary_measure = self._find_primary_measure(df, understanding)
        if primary_measure:
            total = float(df[primary_measure].sum())
            col_u = self._find_col_understanding(primary_measure, understanding)
            unit = "" if (col_u and col_u.semantic_role == SemanticRole.CURRENCY) else ""
            kpis.append(
                KPISpecification(
                    key=f"total_{primary_measure}",
                    label=f"Total {self._label(primary_measure)}",
                    value=round(total, 2),
                    unit=unit,
                    metric="sum",
                    category=(
                        "financial"
                        if col_u and col_u.semantic_role == SemanticRole.CURRENCY
                        else "operational"
                    ),
                    source_columns=[primary_measure],
                    aggregation="sum",
                    confidence=0.9,
                    icon="💰" if col_u and col_u.semantic_role == SemanticRole.CURRENCY else "📈",
                    description=f"Sum of all {self._label(primary_measure)} values",
                    order=order,
                )
            )
            order += 1

            # 4. Average of primary measure
            avg = float(df[primary_measure].mean())
            kpis.append(
                KPISpecification(
                    key=f"avg_{primary_measure}",
                    label=f"Average {self._label(primary_measure)}",
                    value=round(avg, 2),
                    unit=unit,
                    metric="avg",
                    category=(
                        "financial"
                        if col_u and col_u.semantic_role == SemanticRole.CURRENCY
                        else "operational"
                    ),
                    source_columns=[primary_measure],
                    aggregation="avg",
                    confidence=0.85,
                    icon="📊",
                    description=f"Average {self._label(primary_measure)} per record",
                    order=order,
                )
            )
            order += 1

        # 5. Unique dimension count
        primary_dim = self._find_primary_dimension(df, understanding)
        if primary_dim:
            unique_count = int(df[primary_dim].nunique())
            kpis.append(
                KPISpecification(
                    key=f"unique_{primary_dim}",
                    label=f"Unique {self._label(primary_dim)}",
                    value=unique_count,
                    unit="",
                    metric="count_distinct",
                    category="operational",
                    source_columns=[primary_dim],
                    aggregation="count_distinct",
                    confidence=0.8,
                    icon="🏷️",
                    description=f"Number of distinct {self._label(primary_dim)} values",
                    order=order,
                )
            )
            order += 1

        # 6. Date range span
        if understanding.time_columns:
            time_col = understanding.time_columns[0]
            if time_col in df.columns:
                if pd.api.types.is_datetime64_any_dtype(df[time_col]):
                    dates = df[time_col].dropna()
                else:
                    dates = pd.to_datetime(df[time_col], errors="coerce").dropna()

                if len(dates) > 0:
                    span_days = (dates.max() - dates.min()).days
                    kpis.append(
                        KPISpecification(
                            key="date_span",
                            label="Date Range",
                            value=span_days,
                            unit="days",
                            metric="range",
                            category="operational",
                            source_columns=[time_col],
                            aggregation="range",
                            confidence=0.9,
                            icon="📅",
                            description=f"Data spans {span_days} days from {dates.min().strftime('%Y-%m-%d')} to {dates.max().strftime('%Y-%m-%d')}",
                            time_context=f"{dates.min().strftime('%Y-%m-%d')} to {dates.max().strftime('%Y-%m-%d')}",
                            order=order,
                        )
                    )
                    order += 1

        # 7. Growth rate (period over period) — if time + measure
        if understanding.time_columns and primary_measure:
            growth = self._compute_growth_rate(df, understanding.time_columns[0], primary_measure)
            if growth is not None:
                kpis.append(
                    KPISpecification(
                        key="growth_rate",
                        label="Growth Rate",
                        value=round(growth["rate"], 1),
                        unit="%",
                        metric="growth",
                        category="financial",
                        source_columns=[understanding.time_columns[0], primary_measure],
                        aggregation="custom",
                        confidence=0.75,
                        icon="📈" if growth["rate"] > 0 else "📉",
                        description=growth["description"],
                        comparison_value=growth["previous_value"],
                        comparison_label="vs previous period",
                        comparison_direction=(
                            "up" if growth["rate"] > 0 else "down" if growth["rate"] < 0 else "flat"
                        ),
                        order=order,
                    )
                )
                order += 1

        # 8. Top category share
        if primary_dim and primary_measure:
            share = self._compute_top_share(df, primary_dim, primary_measure)
            if share is not None:
                kpis.append(
                    KPISpecification(
                        key="top_category_share",
                        label="Top Category Share",
                        value=round(share["pct"], 1),
                        unit="%",
                        metric="share",
                        category="operational",
                        source_columns=[primary_dim, primary_measure],
                        aggregation="custom",
                        confidence=0.7,
                        icon="🏆",
                        description=share["description"],
                        order=order,
                    )
                )
                order += 1

        # Limit and return
        return kpis[: self.MAX_KPIS]

    # ── Helpers ──

    @staticmethod
    def _find_primary_measure(df: pd.DataFrame, understanding: DatasetUnderstanding) -> str | None:
        """Find the most important measure column."""
        # Prefer currency columns
        for col in understanding.currency_columns:
            if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
                return col
        # Then measures with business-relevant names
        for col in understanding.measures:
            if col not in df.columns:
                continue
            col_lower = col.lower()
            if any(
                kw in col_lower
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
                return col
        # Then first numeric measure
        for col in understanding.measures:
            if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
                return col
        return None

    @staticmethod
    def _find_primary_dimension(
        df: pd.DataFrame, understanding: DatasetUnderstanding
    ) -> str | None:
        """Find the most important dimension column."""
        # Prefer category columns with low cardinality
        for col in understanding.dimensions:
            if col not in df.columns:
                continue
            cardinality = df[col].nunique()
            if 2 <= cardinality <= 20:
                return col
        # Then first dimension
        for col in understanding.dimensions:
            if col in df.columns:
                return col
        return None

    @staticmethod
    def _find_col_understanding(col_name: str, understanding: DatasetUnderstanding):
        """Find ColumnUnderstanding by name."""
        for col in understanding.columns:
            if col.name == col_name:
                return col
        return None

    @staticmethod
    def _label(col: str) -> str:
        """Convert column name to human-readable label."""
        return col.replace("_", " ").title()

    @staticmethod
    def _compute_growth_rate(
        df: pd.DataFrame,
        time_col: str,
        metric_col: str,
    ) -> dict[str, Any] | None:
        """Compute period-over-period growth rate."""
        try:
            if pd.api.types.is_datetime64_any_dtype(df[time_col]):
                dates = df[time_col]
            else:
                dates = pd.to_datetime(df[time_col], errors="coerce")

            df_temp = df.copy()
            df_temp["_period"] = dates.dt.to_period("M")
            monthly = df_temp.groupby("_period")[metric_col].sum().sort_index()

            if len(monthly) < 2:
                return None

            current = float(monthly.iloc[-1])
            previous = float(monthly.iloc[-2])

            if previous == 0:
                return None

            rate = ((current - previous) / previous) * 100

            return {
                "rate": rate,
                "current_value": current,
                "previous_value": previous,
                "description": f"{AutomaticKPIEngine._label(metric_col)} {'increased' if rate > 0 else 'decreased'} by {abs(rate):.1f}% compared to the previous month",
            }
        except Exception:
            return None

    @staticmethod
    def _compute_top_share(
        df: pd.DataFrame,
        dim_col: str,
        metric_col: str,
    ) -> dict[str, Any] | None:
        """Compute the share of the top category."""
        try:
            grouped = (
                df.groupby(dim_col, dropna=False)[metric_col].sum().sort_values(ascending=False)
            )
            if len(grouped) == 0:
                return None
            total = grouped.sum()
            if total == 0:
                return None
            top_cat = grouped.index[0]
            top_val = grouped.iloc[0]
            pct = (top_val / total) * 100
            return {
                "pct": pct,
                "top_category": str(top_cat),
                "top_value": float(top_val),
                "description": f"{str(top_cat)} accounts for {pct:.1f}% of total {AutomaticKPIEngine._label(metric_col)}",
            }
        except Exception:
            return None
