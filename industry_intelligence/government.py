"""Government Intelligence — Budget, projects, regional analytics.

Specialized analytics for government and public sector:
  - Budget allocation and utilization
  - Project status and completion rates
  - Procurement and contractor performance
  - Regional distribution of government spending
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


class GovernmentAnalytics(IndustryAnalytics):
    industry = "government"

    @classmethod
    def analyze(cls, df: pd.DataFrame, col_mapping: dict | None = None) -> AnalyticsResult:
        col_mapping = col_mapping or {}
        insights: list[Insight] = []
        breakdowns: list[Breakdown] = []
        trends: list[Trend] = []
        recommendations: list[str] = []
        alerts: list[str] = []

        project_col = cls._find_col(df, col_mapping, ["project_gov", "project"])
        budget_col = cls._find_numeric_col(df, col_mapping, ["budget_gov", "budget"])
        revenue_col = cls._find_numeric_col(df, col_mapping, ["revenue_gov", "revenue"])
        dept_col = cls._find_col(df, col_mapping, ["department_gov", "department"])
        contractor_col = cls._find_col(df, col_mapping, ["contractor"])
        procurement_col = cls._find_col(df, col_mapping, ["procurement"])
        cls._find_col(df, col_mapping, ["citizen"])
        date_col = cls._find_date_col(df, col_mapping)
        region_col = cls._find_col(df, col_mapping, ["region"])

        # ── Budget Analytics ─────────────────────────────
        if budget_col and budget_col in df.columns:
            total_budget = float(df[budget_col].sum())
            insights.append(
                Insight(
                    title="Total Budget",
                    value=total_budget,
                    formatted=cls._fmt_currency(total_budget),
                    category="financial",
                    description="Total budget allocation across all records.",
                )
            )

            if dept_col and dept_col in df.columns:
                dept_bd = cls._compute_breakdown(df, dept_col, budget_col, "sum")
                if dept_bd:
                    dept_bd.dimension = "Department"
                    dept_bd.metric = "budget"
                    breakdowns.append(dept_bd)

        # ── Revenue ──────────────────────────────────────
        if revenue_col and revenue_col in df.columns:
            total_revenue = float(df[revenue_col].sum())
            insights.append(
                Insight(
                    title="Total Revenue",
                    value=total_revenue,
                    formatted=cls._fmt_currency(total_revenue),
                    category="financial",
                    description="Total government revenue recorded.",
                )
            )

            if budget_col and budget_col in df.columns and total_budget > 0:
                deficit = total_budget - total_revenue
                deficit_pct = deficit / total_budget * 100
                insights.append(
                    Insight(
                        title="Budget Deficit",
                        value=deficit_pct,
                        formatted=cls._fmt_pct(deficit_pct),
                        category="financial",
                        description="Budget deficit as percentage of total budget.",
                        alert=(
                            "critical"
                            if deficit_pct > 10
                            else "warning" if deficit_pct > 5 else "ok"
                        ),
                    )
                )

        # ── Project Analytics ────────────────────────────
        if project_col and project_col in df.columns:
            project_count = int(df[project_col].nunique())
            insights.append(
                Insight(
                    title="Total Projects",
                    value=project_count,
                    formatted=cls._fmt_number(project_count),
                    category="operational",
                    description="Unique government projects.",
                )
            )

            if dept_col and dept_col in df.columns:
                proj_bd = cls._compute_breakdown(df, dept_col, project_col, "count")
                if proj_bd:
                    proj_bd.dimension = "Department"
                    proj_bd.metric = "projects"
                    breakdowns.append(proj_bd)

        # ── Procurement ──────────────────────────────────
        if procurement_col and procurement_col in df.columns:
            proc_count = int(df[procurement_col].nunique())
            insights.append(
                Insight(
                    title="Procurement Records",
                    value=proc_count,
                    formatted=cls._fmt_number(proc_count),
                    category="operational",
                    description="Unique procurement activities.",
                )
            )

        # ── Contractor Performance ───────────────────────
        if contractor_col and contractor_col in df.columns:
            contractor_count = int(df[contractor_col].nunique())
            insights.append(
                Insight(
                    title="Active Contractors",
                    value=contractor_count,
                    formatted=cls._fmt_number(contractor_count),
                    category="operational",
                    description="Unique contractors engaged.",
                )
            )

            if project_col and project_col in df.columns:
                con_bd = cls._compute_breakdown(df, contractor_col, project_col, "count")
                if con_bd:
                    con_bd.dimension = "Contractor"
                    con_bd.metric = "projects"
                    breakdowns.append(con_bd)

        # ── Regional Analytics ───────────────────────────
        if region_col and region_col in df.columns:
            region_count = int(df[region_col].nunique())
            insights.append(
                Insight(
                    title="Regions Covered",
                    value=region_count,
                    formatted=cls._fmt_number(region_count),
                    category="operational",
                    description="Number of distinct regions served.",
                )
            )

            if budget_col and budget_col in df.columns:
                region_bd = cls._compute_breakdown(df, region_col, budget_col, "sum")
                if region_bd:
                    region_bd.dimension = "Region"
                    region_bd.metric = "budget"
                    breakdowns.append(region_bd)

        # ── Department Analytics ─────────────────────────
        if dept_col and dept_col in df.columns:
            dept_count = int(df[dept_col].nunique())
            insights.append(
                Insight(
                    title="Government Departments",
                    value=dept_count,
                    formatted=cls._fmt_number(dept_count),
                    category="operational",
                    description="Number of distinct departments/ministries.",
                )
            )

        # ── Trends ───────────────────────────────────────
        if date_col and budget_col and budget_col in df.columns:
            budget_trend = cls._compute_trend(df, date_col, budget_col, "sum")
            if budget_trend:
                budget_trend.metric = "budget"
                trends.append(budget_trend)

        recommendations.extend(
            [
                "Monitor budget utilization by department for fiscal discipline.",
                "Track project completion rates against timelines.",
                "Review procurement competition to ensure value for money.",
                "Analyze regional budget allocation for equitable distribution.",
            ]
        )

        for insight in insights:
            if insight.alert == "critical":
                alerts.append(
                    f"CRITICAL: {insight.title}: {insight.formatted} — immediate fiscal review needed."
                )
            elif insight.alert == "warning":
                alerts.append(f"{insight.title}: {insight.formatted} — requires monitoring.")

        return AnalyticsResult(
            industry="government",
            insights=insights,
            breakdowns=breakdowns,
            trends=trends,
            recommendations=recommendations,
            alerts=alerts,
        )


IndustryAnalyticsRegistry.register("government", GovernmentAnalytics)
