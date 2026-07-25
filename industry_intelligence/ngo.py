"""NGO Intelligence — Donors, programs, beneficiaries, impact analytics.

Specialized analytics for non-governmental organizations:
  - Donor engagement and retention
  - Program reach and effectiveness
  - Beneficiary coverage and demographics
  - Funding sources and grant utilization
  - Impact measurement
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


class NGOAnalytics(IndustryAnalytics):
    industry = "ngo"

    @classmethod
    def analyze(cls, df: pd.DataFrame, col_mapping: dict | None = None) -> AnalyticsResult:
        col_mapping = col_mapping or {}
        insights: list[Insight] = []
        breakdowns: list[Breakdown] = []
        trends: list[Trend] = []
        recommendations: list[str] = []
        alerts: list[str] = []

        donor_col = cls._find_col(df, col_mapping, ["donor"])
        beneficiary_col = cls._find_col(df, col_mapping, ["beneficiary"])
        program_col = cls._find_col(df, col_mapping, ["program"])
        project_col = cls._find_col(df, col_mapping, ["project_ngo", "project"])
        donation_col = cls._find_numeric_col(df, col_mapping, ["donation", "revenue"])
        grant_col = cls._find_col(df, col_mapping, ["grant"])
        date_col = cls._find_date_col(df, col_mapping)
        region_col = cls._find_col(df, col_mapping, ["region"])

        # ── Donor Analytics ──────────────────────────────
        if donor_col and donor_col in df.columns:
            donor_count = int(df[donor_col].nunique())
            insights.append(Insight(
                title="Total Donors",
                value=donor_count,
                formatted=cls._fmt_number(donor_count),
                category="financial",
                description="Unique donors contributing to the organization.",
            ))

        # ── Funding / Donations ──────────────────────────
        if donation_col and donation_col in df.columns:
            total_donations = float(df[donation_col].sum())
            insights.append(Insight(
                title="Total Funding",
                value=total_donations,
                formatted=cls._fmt_currency(total_donations),
                category="financial",
                description="Total donations/funding received.",
            ))

            if donor_col and donor_col in df.columns and donor_count > 0:
                avg_donation = total_donations / donor_count
                insights.append(Insight(
                    title="Avg Donation per Donor",
                    value=avg_donation,
                    formatted=cls._fmt_currency(avg_donation),
                    category="financial",
                    description="Average contribution per donor.",
                ))

            if date_col:
                funding_trend = cls._compute_trend(df, date_col, donation_col, "sum")
                if funding_trend:
                    funding_trend.metric = "funding"
                    trends.append(funding_trend)

        # ── Beneficiary Analytics ────────────────────────
        if beneficiary_col and beneficiary_col in df.columns:
            beneficiary_count = int(df[beneficiary_col].nunique())
            insights.append(Insight(
                title="Beneficiaries Reached",
                value=beneficiary_count,
                formatted=cls._fmt_number(beneficiary_count),
                category="impact",
                description="Unique beneficiaries served by programs.",
            ))

            if region_col and region_col in df.columns:
                ben_region_bd = cls._compute_breakdown(df, region_col, beneficiary_col, "count")
                if ben_region_bd:
                    ben_region_bd.dimension = "Region"
                    ben_region_bd.metric = "beneficiaries"
                    breakdowns.append(ben_region_bd)

        # ── Program Analytics ────────────────────────────
        if program_col and program_col in df.columns:
            program_count = int(df[program_col].nunique())
            insights.append(Insight(
                title="Active Programs",
                value=program_count,
                formatted=cls._fmt_number(program_count),
                category="operational",
                description="Distinct programs running.",
            ))

            if beneficiary_col and beneficiary_col in df.columns:
                prog_bd = cls._compute_breakdown(df, program_col, beneficiary_col, "count")
                if prog_bd:
                    prog_bd.dimension = "Program"
                    prog_bd.metric = "beneficiaries"
                    breakdowns.append(prog_bd)

            if donation_col and donation_col in df.columns:
                prog_fund_bd = cls._compute_breakdown(df, program_col, donation_col, "sum")
                if prog_fund_bd:
                    prog_fund_bd.dimension = "Program"
                    prog_fund_bd.metric = "funding"
                    breakdowns.append(prog_fund_bd)

        # ── Project Analytics ────────────────────────────
        if project_col and project_col in df.columns:
            project_count = int(df[project_col].nunique())
            insights.append(Insight(
                title="Active Projects",
                value=project_count,
                formatted=cls._fmt_number(project_count),
                category="operational",
                description="Unique NGO projects.",
            ))

        # ── Grant Analytics ──────────────────────────────
        if grant_col and grant_col in df.columns:
            grant_count = int(df[grant_col].nunique())
            insights.append(Insight(
                title="Active Grants",
                value=grant_count,
                formatted=cls._fmt_number(grant_count),
                category="financial",
                description="Distinct grants received.",
            ))

        # ── Regional Coverage ─────────────────────────────
        if region_col and region_col in df.columns:
            region_count = int(df[region_col].nunique())
            insights.append(Insight(
                title="Regions Covered",
                value=region_count,
                formatted=cls._fmt_number(region_count),
                category="operational",
                description="Number of distinct regions served.",
            ))

        # ── Impact Metrics ───────────────────────────────
        if donation_col and donation_col in df.columns and beneficiary_col and beneficiary_col in df.columns:
            beneficiary_count = max(int(df[beneficiary_col].nunique()), 1)
            cost_per_beneficiary = float(df[donation_col].sum()) / beneficiary_count
            insights.append(Insight(
                title="Cost per Beneficiary",
                value=cost_per_beneficiary,
                formatted=cls._fmt_currency(cost_per_beneficiary),
                category="impact",
                description="Total funding divided by number of beneficiaries.",
            ))

        recommendations.extend([
            "Track donor retention patterns to sustain funding streams.",
            "Monitor program impact against beneficiary targets.",
            "Diversify funding sources to reduce dependency risk.",
            "Analyze regional coverage to identify underserved areas.",
        ])

        for insight in insights:
            if insight.alert == "warning":
                alerts.append(f"{insight.title}: {insight.formatted} — review needed.")

        return AnalyticsResult(
            industry="ngo",
            insights=insights,
            breakdowns=breakdowns,
            trends=trends,
            recommendations=recommendations,
            alerts=alerts,
        )


IndustryAnalyticsRegistry.register("ngo", NGOAnalytics)
