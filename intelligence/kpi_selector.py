"""Automatic KPI Selection.

Identifies meaningful KPIs from the dataset and computes their values.
KPIs are selected based on:
  - Measure columns (sum, mean, count)
  - Domain-specific patterns
  - Time-based growth rates
  - Completion/achievement rates

Never fabricates KPIs — all values come from actual data.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .column_analyzer import (
    ColumnSemanticRole,
    DatasetUnderstanding,
)


@dataclass
class KPICandidate:
    """A selected KPI with computed value."""

    key: str
    label: str
    value: float
    formatted: str
    unit: str = ""
    column: str = ""
    aggregation: str = "sum"
    comparison: str = ""  # e.g., "up 18% from last period"
    context: str = ""  # e.g., "Jan 2024 – Dec 2024"
    importance: float = 0.0

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "label": self.label,
            "value": self.value,
            "formatted": self.formatted,
            "unit": self.unit,
            "column": self.column,
            "aggregation": self.aggregation,
            "comparison": self.comparison,
            "context": self.context,
            "importance": round(self.importance, 2),
        }


class KPISelector:
    """Selects and computes KPIs from dataset understanding."""

    MAX_KPIS = 8

    def select(self, df: pd.DataFrame, u: DatasetUnderstanding) -> list[KPICandidate]:
        """Select and compute KPIs."""
        kpis: list[KPICandidate] = []

        # Total records
        kpis.append(
            KPICandidate(
                key="total_records",
                label="Total Records",
                value=float(len(df)),
                formatted=f"{len(df):,}",
                unit="records",
                aggregation="count",
                importance=70.0,
            )
        )

        # Measure-based KPIs
        for measure in u.measures[:5]:  # limit to top 5 measures
            col_u = next((c for c in u.columns if c.name == measure), None)
            if not col_u:
                continue

            # Sum for currency/measure
            if col_u.role in (ColumnSemanticRole.CURRENCY, ColumnSemanticRole.MEASURE):
                total = df[measure].sum()
                kpis.append(
                    KPICandidate(
                        key=f"total_{measure}",
                        label=f"Total {measure.replace('_', ' ').title()}",
                        value=float(total),
                        formatted=self._format_value(total, col_u.role),
                        unit="currency" if col_u.role == ColumnSemanticRole.CURRENCY else "",
                        column=measure,
                        aggregation="sum",
                        importance=85.0 if col_u.role == ColumnSemanticRole.CURRENCY else 75.0,
                    )
                )

                # Average
                avg = df[measure].mean()
                kpis.append(
                    KPICandidate(
                        key=f"avg_{measure}",
                        label=f"Average {measure.replace('_', ' ').title()}",
                        value=float(avg),
                        formatted=self._format_value(avg, col_u.role),
                        unit="currency" if col_u.role == ColumnSemanticRole.CURRENCY else "",
                        column=measure,
                        aggregation="mean",
                        importance=70.0,
                    )
                )

            # Percentage → average
            elif col_u.role == ColumnSemanticRole.PERCENTAGE:
                avg = df[measure].mean()
                kpis.append(
                    KPICandidate(
                        key=f"avg_{measure}",
                        label=f"Average {measure.replace('_', ' ').title()}",
                        value=float(avg),
                        formatted=f"{avg:.1f}%",
                        unit="%",
                        column=measure,
                        aggregation="mean",
                        importance=72.0,
                    )
                )

        # Time-based growth rate
        if u.date_columns and u.measures:
            growth = self._compute_growth_rate(df, u.date_columns[0], u.measures[0])
            if growth:
                kpis.append(growth)

        # Data quality KPI
        kpis.append(
            KPICandidate(
                key="data_quality",
                label="Data Quality Score",
                value=u.quality_score,
                formatted=f"{u.quality_score:.1f}/100",
                unit="score",
                importance=65.0,
            )
        )

        # Sort by importance and cap
        kpis.sort(key=lambda k: k.importance, reverse=True)
        return kpis[: self.MAX_KPIS]

    def _compute_growth_rate(
        self, df: pd.DataFrame, date_col: str, measure: str
    ) -> KPICandidate | None:
        """Compute growth rate of a measure over time."""
        try:
            temp = df[[date_col, measure]].dropna().copy()
            temp[date_col] = pd.to_datetime(temp[date_col], errors="coerce")
            temp = temp.dropna(subset=[date_col]).sort_values(date_col)

            if len(temp) < 2:
                return None

            # Compare first vs last period
            temp["_period"] = temp[date_col].dt.to_period("M")
            monthly = temp.groupby("_period")[measure].sum()

            if len(monthly) < 2:
                return None

            first_val = monthly.iloc[0]
            last_val = monthly.iloc[-1]

            if first_val == 0:
                return None

            growth_rate = ((last_val - first_val) / abs(first_val)) * 100

            direction = "up" if growth_rate > 0 else "down"
            comparison = f"{direction} {abs(growth_rate):.1f}% from {monthly.index[0]} to {monthly.index[-1]}"

            return KPICandidate(
                key="growth_rate",
                label=f"Growth Rate ({measure.replace('_', ' ').title()})",
                value=float(growth_rate),
                formatted=f"{growth_rate:+.1f}%",
                unit="%",
                column=measure,
                aggregation="growth",
                comparison=comparison,
                context=f"{monthly.index[0]} – {monthly.index[-1]}",
                importance=90.0,
            )
        except Exception:
            return None

    def _format_value(self, value: float, role: ColumnSemanticRole) -> str:
        """Format a value based on its semantic role."""
        if role == ColumnSemanticRole.CURRENCY:
            if abs(value) >= 1_000_000:
                return f"${value / 1_000_000:.2f}M"
            elif abs(value) >= 1_000:
                return f"${value / 1_000:.1f}K"
            else:
                return f"${value:,.2f}"
        else:
            if abs(value) >= 1_000_000:
                return f"{value / 1_000_000:.2f}M"
            elif abs(value) >= 1_000:
                return f"{value / 1_000:.1f}K"
            else:
                return f"{value:,.2f}"
