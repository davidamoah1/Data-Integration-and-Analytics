"""Manufacturing Intelligence — Production, downtime, quality analytics.

Specialized analytics for manufacturing operations:
  - Production volume and throughput
  - Machine utilization and performance
  - Downtime analysis and OEE
  - Quality metrics (yield, defect, scrap rates)
"""

from __future__ import annotations

import pandas as pd

from industry_intelligence.base import (
    AnalyticsResult,
    Breakdown,
    IndustryAnalytics,
    IndustryAnalyticsRegistry,
    Insight,
    Trend,
)


class ManufacturingAnalytics(IndustryAnalytics):
    industry = "manufacturing"

    @classmethod
    def analyze(cls, df: pd.DataFrame, col_mapping: dict | None = None) -> AnalyticsResult:
        col_mapping = col_mapping or {}
        insights: list[Insight] = []
        breakdowns: list[Breakdown] = []
        trends: list[Trend] = []
        recommendations: list[str] = []
        alerts: list[str] = []

        machine_col = cls._find_col(df, col_mapping, ["machine"])
        production_col = cls._find_numeric_col(df, col_mapping, ["production"])
        downtime_col = cls._find_numeric_col(df, col_mapping, ["downtime"])
        product_col = cls._find_col(df, col_mapping, ["product_manufacturing", "product"])
        date_col = cls._find_date_col(df, col_mapping)
        yield_col = cls._find_numeric_col(df, col_mapping, ["yield", "yield_rate"])
        defect_col = cls._find_numeric_col(df, col_mapping, ["defect", "defect_rate"])

        # ── Production Analytics ─────────────────────────
        if production_col and production_col in df.columns:
            total_production = float(df[production_col].sum())
            insights.append(
                Insight(
                    title="Total Production",
                    value=total_production,
                    formatted=cls._fmt_number(total_production),
                    category="operational",
                    description="Total production output volume.",
                )
            )

            if date_col:
                prod_trend = cls._compute_trend(df, date_col, production_col, "sum")
                if prod_trend:
                    prod_trend.metric = "production"
                    trends.append(prod_trend)

        # ── Machine Analytics ────────────────────────────
        if machine_col and machine_col in df.columns:
            machine_count = int(df[machine_col].nunique())
            insights.append(
                Insight(
                    title="Active Machines",
                    value=machine_count,
                    formatted=cls._fmt_number(machine_count),
                    category="operational",
                    description="Unique machines in operation.",
                )
            )

            if production_col and production_col in df.columns:
                machine_bd = cls._compute_breakdown(df, machine_col, production_col, "sum")
                if machine_bd:
                    machine_bd.dimension = "Machine"
                    machine_bd.metric = "production"
                    breakdowns.append(machine_bd)

                if machine_count > 0:
                    prod_per_machine = total_production / machine_count
                    insights.append(
                        Insight(
                            title="Production per Machine",
                            value=prod_per_machine,
                            formatted=cls._fmt_number(prod_per_machine),
                            category="operational",
                            description="Average production output per machine.",
                        )
                    )

        # ── Downtime Analysis ────────────────────────────
        if downtime_col and downtime_col in df.columns:
            total_downtime = float(df[downtime_col].sum())
            insights.append(
                Insight(
                    title="Total Downtime",
                    value=total_downtime,
                    formatted=f"{total_downtime:,.0f}h",
                    category="maintenance",
                    description="Total downtime hours across all machines.",
                    alert=(
                        "critical"
                        if total_downtime > 100
                        else "warning" if total_downtime > 50 else "ok"
                    ),
                )
            )

            if machine_col and machine_col in df.columns:
                dt_bd = cls._compute_breakdown(df, machine_col, downtime_col, "sum")
                if dt_bd:
                    dt_bd.dimension = "Machine"
                    dt_bd.metric = "downtime"
                    breakdowns.append(dt_bd)

        # ── Quality Metrics ──────────────────────────────
        if yield_col and yield_col in df.columns:
            avg_yield = float(df[yield_col].dropna().mean())
            insights.append(
                Insight(
                    title="Average Yield Rate",
                    value=avg_yield,
                    formatted=(
                        cls._fmt_pct(avg_yield) if avg_yield <= 100 else cls._fmt_number(avg_yield)
                    ),
                    category="quality",
                    description="Mean yield rate across production runs.",
                    alert="warning" if avg_yield < 95 else "ok",
                )
            )

        if defect_col and defect_col in df.columns:
            avg_defect = float(df[defect_col].dropna().mean())
            insights.append(
                Insight(
                    title="Average Defect Rate",
                    value=avg_defect,
                    formatted=(
                        cls._fmt_pct(avg_defect)
                        if avg_defect <= 100
                        else cls._fmt_number(avg_defect)
                    ),
                    category="quality",
                    description="Mean defect rate across production runs.",
                    alert="warning" if avg_defect > 5 else "ok",
                )
            )

        # ── Product Line Analytics ───────────────────────
        if product_col and product_col in df.columns:
            product_count = int(df[product_col].nunique())
            insights.append(
                Insight(
                    title="Product Lines",
                    value=product_count,
                    formatted=cls._fmt_number(product_count),
                    category="operational",
                    description="Distinct product lines manufactured.",
                )
            )

            if production_col and production_col in df.columns:
                prod_bd = cls._compute_breakdown(df, product_col, production_col, "sum")
                if prod_bd:
                    prod_bd.dimension = "Product Line"
                    prod_bd.metric = "production"
                    breakdowns.append(prod_bd)

        recommendations.extend(
            [
                "Monitor machine utilization to identify underperforming equipment.",
                "Schedule preventive maintenance based on downtime patterns.",
                "Track yield rates by product line for quality improvement.",
                "Analyze production trends to optimize throughput and capacity planning.",
            ]
        )

        for insight in insights:
            if insight.alert == "critical":
                alerts.append(
                    f"CRITICAL: {insight.title}: {insight.formatted} — immediate action required."
                )
            elif insight.alert == "warning":
                alerts.append(f"{insight.title}: {insight.formatted} — needs attention.")

        return AnalyticsResult(
            industry="manufacturing",
            insights=insights,
            breakdowns=breakdowns,
            trends=trends,
            recommendations=recommendations,
            alerts=alerts,
        )


IndustryAnalyticsRegistry.register("manufacturing", ManufacturingAnalytics)
