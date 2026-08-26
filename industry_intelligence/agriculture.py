"""Agriculture Intelligence â€” Production, yield, crop analysis, livestock.

Specialized analytics for farms, agricultural operations:
  - Production volume and harvest totals
  - Yield per hectare / per farm
  - Crop distribution and performance
  - Livestock counts and distribution
  - Weather impact analysis
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


class AgricultureAnalytics(IndustryAnalytics):
    industry = "agriculture"

    @classmethod
    def analyze(cls, df: pd.DataFrame, col_mapping: dict | None = None) -> AnalyticsResult:
        col_mapping = col_mapping or {}
        insights: list[Insight] = []
        breakdowns: list[Breakdown] = []
        trends: list[Trend] = []
        recommendations: list[str] = []
        alerts: list[str] = []

        farm_col = cls._find_col(df, col_mapping, ["farm"])
        crop_col = cls._find_col(df, col_mapping, ["crop"])
        harvest_col = cls._find_numeric_col(df, col_mapping, ["crop", "production", "revenue"])
        livestock_col = cls._find_col(df, col_mapping, ["livestock"])
        weather_col = cls._find_numeric_col(df, col_mapping, ["weather"])
        hectares_col = cls._find_numeric_col(df, col_mapping, ["hectares", "area", "size"])
        date_col = cls._find_date_col(df, col_mapping)
        region_col = cls._find_col(df, col_mapping, ["region"])

        # â”€â”€ Farm Analytics â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        if farm_col and farm_col in df.columns:
            farm_count = int(df[farm_col].nunique())
            insights.append(
                Insight(
                    title="Total Farms",
                    value=farm_count,
                    formatted=cls._fmt_number(farm_count),
                    category="operational",
                    description="Unique farms in the dataset.",
                )
            )

        # â”€â”€ Production / Harvest â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        if harvest_col and harvest_col in df.columns:
            total_harvest = float(df[harvest_col].sum())
            insights.append(
                Insight(
                    title="Total Production",
                    value=total_harvest,
                    formatted=cls._fmt_number(total_harvest),
                    category="operational",
                    description="Total production/harvest volume.",
                )
            )

            # Yield per farm
            if farm_col and farm_col in df.columns and farm_count > 0:
                yield_per_farm = total_harvest / farm_count
                insights.append(
                    Insight(
                        title="Yield per Farm",
                        value=yield_per_farm,
                        formatted=cls._fmt_number(yield_per_farm),
                        category="operational",
                        description="Average production per farm.",
                    )
                )

            # Yield per hectare
            if hectares_col and hectares_col in df.columns:
                total_ha = float(df[hectares_col].sum())
                if total_ha > 0:
                    yield_per_ha = total_harvest / total_ha
                    insights.append(
                        Insight(
                            title="Yield per Hectare",
                            value=yield_per_ha,
                            formatted=f"{yield_per_ha:.1f}",
                            category="operational",
                            description="Production efficiency per hectare.",
                        )
                    )

            # Production trend
            if date_col:
                prod_trend = cls._compute_trend(df, date_col, harvest_col, "sum")
                if prod_trend:
                    prod_trend.metric = "production"
                    trends.append(prod_trend)

        # â”€â”€ Crop Analysis â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        if crop_col and crop_col in df.columns:
            crop_count = int(df[crop_col].nunique())
            insights.append(
                Insight(
                    title="Crop Varieties",
                    value=crop_count,
                    formatted=cls._fmt_number(crop_count),
                    category="operational",
                    description="Distinct crop types cultivated.",
                )
            )

            if harvest_col and harvest_col in df.columns:
                crop_bd = cls._compute_breakdown(df, crop_col, harvest_col, "sum")
                if crop_bd:
                    crop_bd.dimension = "Crop"
                    crop_bd.metric = "production"
                    breakdowns.append(crop_bd)

        # â”€â”€ Livestock â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        if livestock_col and livestock_col in df.columns:
            livestock_count = int(df[livestock_col].nunique())
            insights.append(
                Insight(
                    title="Livestock Categories",
                    value=livestock_count,
                    formatted=cls._fmt_number(livestock_count),
                    category="operational",
                    description="Distinct livestock types/categories.",
                )
            )

            livestock_bd = cls._compute_breakdown(df, livestock_col, livestock_col, "count")
            if livestock_bd:
                livestock_bd.dimension = "Livestock"
                livestock_bd.metric = "count"
                breakdowns.append(livestock_bd)

        # â”€â”€ Weather Impact â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        if weather_col and weather_col in df.columns:
            avg_weather = float(df[weather_col].dropna().mean())
            insights.append(
                Insight(
                    title="Average Rainfall",
                    value=avg_weather,
                    formatted=f"{avg_weather:.1f}mm",
                    category="environmental",
                    description="Mean rainfall/precipitation across records.",
                    alert="warning" if avg_weather < 500 else "ok",
                )
            )

        # â”€â”€ Regional Analytics â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        if region_col and region_col in df.columns:
            region_count = int(df[region_col].nunique())
            insights.append(
                Insight(
                    title="Regions Covered",
                    value=region_count,
                    formatted=cls._fmt_number(region_count),
                    category="operational",
                    description="Number of distinct regions.",
                )
            )

            if harvest_col and harvest_col in df.columns:
                region_bd = cls._compute_breakdown(df, region_col, harvest_col, "sum")
                if region_bd:
                    region_bd.dimension = "Region"
                    region_bd.metric = "production"
                    breakdowns.append(region_bd)

        # â”€â”€ Farm Performance â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        if farm_col and farm_col in df.columns and harvest_col and harvest_col in df.columns:
            farm_bd = cls._compute_breakdown(df, farm_col, harvest_col, "sum")
            if farm_bd:
                farm_bd.dimension = "Farm"
                farm_bd.metric = "production"
                breakdowns.append(farm_bd)

        recommendations.extend(
            [
                "Compare yield per hectare across farms to identify best practices.",
                "Monitor rainfall patterns to optimize irrigation scheduling.",
                "Diversify crop production to reduce single-crop risk.",
                "Track livestock health and mortality by category.",
            ]
        )

        for insight in insights:
            if insight.alert == "warning":
                alerts.append(
                    f"{insight.title}: {insight.formatted} â€” below recommended threshold."
                )

        return AnalyticsResult(
            industry="agriculture",
            insights=insights,
            breakdowns=breakdowns,
            trends=trends,
            recommendations=recommendations,
            alerts=alerts,
        )


IndustryAnalyticsRegistry.register("agriculture", AgricultureAnalytics)
