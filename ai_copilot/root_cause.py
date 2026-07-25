"""Root Cause Analysis Engine.

Decomposes a metric change into its contributing factors by dimension.
When a metric changes (e.g., "sales dropped 15%"), this engine identifies
which dimension values (products, regions, customers) contributed most
to the change.

Example output:
    Sales dropped 15% ($12,000 → $10,200, -$1,800)

    Main reasons:
    1. Product A declined by 40% (-$1,200) — 67% of total decline
    2. Northern region sales reduced by 25% (-$800) — 44% of total decline
    3. Customer segment 'Enterprise' dropped 30% (-$500) — 28% of total decline

    Recommendation:
    Increase Product A marketing in the Northern region.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd


@dataclass
class Contribution:
    """A single dimension value's contribution to a metric change."""

    dimension: str
    value: str
    old_value: float
    new_value: float
    change: float
    change_pct: float
    contribution_pct: float  # share of total change
    direction: str  # "increase", "decrease"

    def to_dict(self) -> dict:
        return {
            "dimension": self.dimension,
            "value": self.value,
            "old_value": round(self.old_value, 2),
            "new_value": round(self.new_value, 2),
            "change": round(self.change, 2),
            "change_pct": round(self.change_pct, 2),
            "contribution_pct": round(self.contribution_pct, 2),
            "direction": self.direction,
        }


@dataclass
class RootCauseResult:
    """Result of root cause analysis for a metric change."""

    metric: str
    metric_label: str
    direction: str  # "increase", "decrease", "change"
    old_total: float
    new_total: float
    total_change: float
    total_change_pct: float
    contributions: list[Contribution] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    summary: str = ""

    def to_dict(self) -> dict:
        return {
            "metric": self.metric,
            "metric_label": self.metric_label,
            "direction": self.direction,
            "old_total": round(self.old_total, 2),
            "new_total": round(self.new_total, 2),
            "total_change": round(self.total_change, 2),
            "total_change_pct": round(self.total_change_pct, 2),
            "contributions": [c.to_dict() for c in self.contributions],
            "recommendations": self.recommendations,
            "summary": self.summary,
        }


class RootCauseAnalyzer:
    """Analyzes why a metric changed by decomposing across dimensions."""

    @staticmethod
    def analyze(
        df: pd.DataFrame,
        metric_col: str,
        date_col: str,
        dimension_cols: list[str] | None = None,
        metric_label: str | None = None,
        direction: str | None = None,
    ) -> RootCauseResult | None:
        """Analyze why a metric changed over time.

        Splits the data into two halves (by date) and compares the metric
        across dimension values to identify top contributors to the change.

        Args:
            df: DataFrame with the data.
            metric_col: Column name of the metric to analyze.
            date_col: Column name of the date/time column.
            dimension_cols: List of dimension columns to decompose by.
            metric_label: Human-readable label for the metric.
            direction: Expected direction ("increase" or "decrease").

        Returns:
            RootCauseResult with contributions and recommendations, or None
            if analysis cannot be performed.
        """
        if metric_col not in df.columns or date_col not in df.columns:
            return None

        if not pd.api.types.is_numeric_dtype(df[metric_col]):
            return None

        dimension_cols = dimension_cols or []
        dimension_cols = [c for c in dimension_cols if c in df.columns and c != metric_col and c != date_col]

        # Parse dates
        df = df.copy()
        if not pd.api.types.is_datetime64_any_dtype(df[date_col]):
            df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        df = df.dropna(subset=[date_col, metric_col])

        if len(df) < 4:
            return None

        # Split into two halves by date midpoint
        date_midpoint = df[date_col].median()
        old_period = df[df[date_col] <= date_midpoint]
        new_period = df[df[date_col] > date_midpoint]

        if old_period.empty or new_period.empty:
            return None

        old_total = float(old_period[metric_col].sum())
        new_total = float(new_period[metric_col].sum())
        total_change = new_total - old_total
        total_change_pct = (total_change / old_total * 100) if old_total != 0 else 0.0

        # Determine actual direction
        if total_change < 0:
            actual_direction = "decrease"
        elif total_change > 0:
            actual_direction = "increase"
        else:
            actual_direction = "stable"

        # Use user-specified direction if provided, otherwise actual
        effective_direction = direction or actual_direction

        metric_label = metric_label or metric_col.replace("_", " ").title()

        # Decompose by each dimension
        all_contributions: list[Contribution] = []

        for dim_col in dimension_cols:
            dim_contributions = RootCauseAnalyzer._decompose_dimension(
                old_period, new_period, metric_col, dim_col, total_change
            )
            all_contributions.extend(dim_contributions)

        # Sort by absolute contribution (largest impact first)
        all_contributions.sort(key=lambda c: abs(c.change), reverse=True)

        # Keep top 10
        all_contributions = all_contributions[:10]

        # Generate recommendations
        recommendations = RootCauseAnalyzer._generate_recommendations(
            metric_label, effective_direction, all_contributions, total_change_pct
        )

        # Generate summary
        summary = RootCauseAnalyzer._generate_summary(
            metric_label, effective_direction, old_total, new_total,
            total_change, total_change_pct, all_contributions
        )

        return RootCauseResult(
            metric=metric_col,
            metric_label=metric_label,
            direction=effective_direction,
            old_total=old_total,
            new_total=new_total,
            total_change=total_change,
            total_change_pct=total_change_pct,
            contributions=all_contributions,
            recommendations=recommendations,
            summary=summary,
        )

    @staticmethod
    def _decompose_dimension(
        old_period: pd.DataFrame,
        new_period: pd.DataFrame,
        metric_col: str,
        dim_col: str,
        total_change: float,
    ) -> list[Contribution]:
        """Decompose the metric change by a single dimension."""
        old_by_dim = old_period.groupby(dim_col)[metric_col].sum()
        new_by_dim = new_period.groupby(dim_col)[metric_col].sum()

        # Align indices
        all_values = set(old_by_dim.index) | set(new_by_dim.index)
        contributions = []

        for value in all_values:
            old_val = float(old_by_dim.get(value, 0))
            new_val = float(new_by_dim.get(value, 0))
            change = new_val - old_val
            change_pct = (change / old_val * 100) if old_val != 0 else 0.0
            contribution_pct = (abs(change) / abs(total_change) * 100) if total_change != 0 else 0.0

            if abs(change) < 1e-6:
                continue

            direction = "increase" if change > 0 else "decrease"

            contributions.append(Contribution(
                dimension=dim_col,
                value=str(value),
                old_value=old_val,
                new_value=new_val,
                change=change,
                change_pct=change_pct,
                contribution_pct=contribution_pct,
                direction=direction,
            ))

        return contributions

    @staticmethod
    def _generate_recommendations(
        metric_label: str,
        direction: str,
        contributions: list[Contribution],
        total_change_pct: float,
    ) -> list[str]:
        """Generate actionable recommendations based on root causes."""
        recommendations = []

        if not contributions:
            return ["Insufficient data to generate recommendations."]

        # Top 3 contributors aligned with the overall direction
        top_aligned = [c for c in contributions if c.direction == direction][:3]
        # Top 3 going against the direction (positive outliers)
        opposite = "increase" if direction == "decrease" else "decrease"
        top_opposite = [c for c in contributions if c.direction == opposite][:2]

        if direction == "decrease":
            for c in top_aligned:
                recommendations.append(
                    f"Increase {c.dimension.replace('_', ' ').title()} '{c.value}' "
                    f"marketing/effort — it declined {abs(c.change_pct):.0f}% "
                    f"and accounts for {c.contribution_pct:.0f}% of the total drop."
                )
            for c in top_opposite:
                recommendations.append(
                    f"Study what worked for {c.dimension.replace('_', ' ').title()} '{c.value}' "
                    f"— it grew {c.change_pct:.0f}% despite the overall decline."
                )
        elif direction == "increase":
            for c in top_aligned:
                recommendations.append(
                    f"Replicate the success of {c.dimension.replace('_', ' ').title()} '{c.value}' "
                    f"— it grew {c.change_pct:.0f}% and drove {c.contribution_pct:.0f}% of the increase."
                )
            for c in top_opposite:
                recommendations.append(
                    f"Investigate why {c.dimension.replace('_', ' ').title()} '{c.value}' "
                    f"declined {abs(c.change_pct):.0f}% despite overall growth."
                )
        else:
            recommendations.append(
                f"Review the top contributors to {metric_label} changes for strategic adjustments."
            )

        return recommendations

    @staticmethod
    def _generate_summary(
        metric_label: str,
        direction: str,
        old_total: float,
        new_total: float,
        total_change: float,
        total_change_pct: float,
        contributions: list[Contribution],
    ) -> str:
        """Generate a human-readable summary of the root cause analysis."""
        if direction == "decrease":
            verb = "dropped"
            preposition = "down"
        elif direction == "increase":
            verb = "grew"
            preposition = "up"
        else:
            verb = "changed"
            preposition = ""

        summary_parts = [
            f"{metric_label} {verb} {abs(total_change_pct):.1f}% "
            f"(${old_total:,.0f} → ${new_total:,.0f}"
            f"{f', {preposition} {abs(total_change):,.0f}' if preposition else ''}).\n\n"
            f"Main reasons:"
        ]

        for i, c in enumerate(contributions[:5], 1):
            change_word = "declined" if c.direction == "decrease" else "grew"
            summary_parts.append(
                f"{i}. {c.dimension.replace('_', ' ').title()} '{c.value}' "
                f"{change_word} {abs(c.change_pct):.0f}% "
                f"({c.contribution_pct:.0f}% of total change)"
            )

        if contributions:
            top = contributions[0]
            rec = (
                f"Increase {top.dimension.replace('_', ' ').title()} '{top.value}' marketing."
                if direction == "decrease"
                else f"Scale up {top.dimension.replace('_', ' ').title()} '{top.value}' strategy."
            )
            summary_parts.append(f"\nRecommendation:\n{rec}")

        return "\n".join(summary_parts)
