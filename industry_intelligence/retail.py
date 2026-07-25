"""Retail / SME Intelligence — Sales, inventory, customer analytics.

Specialized analytics for retail, SME, and commerce:
  - Sales performance and revenue trends
  - Product and category analysis
  - Customer segmentation and behavior
  - Inventory health and stock analysis
  - Profitability and margin analysis
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


class RetailAnalytics(IndustryAnalytics):
    industry = "retail"

    @classmethod
    def analyze(cls, df: pd.DataFrame, col_mapping: dict | None = None) -> AnalyticsResult:
        col_mapping = col_mapping or {}
        insights: list[Insight] = []
        breakdowns: list[Breakdown] = []
        trends: list[Trend] = []
        recommendations: list[str] = []
        alerts: list[str] = []

        order_col = cls._find_col(df, col_mapping, ["order"])
        customer_col = cls._find_col(df, col_mapping, ["customer"])
        product_col = cls._find_col(df, col_mapping, ["product"])
        revenue_col = cls._find_numeric_col(df, col_mapping, ["revenue", "sales"])
        profit_col = cls._find_numeric_col(df, col_mapping, ["profit"])
        inventory_col = cls._find_col(df, col_mapping, ["inventory"])
        supplier_col = cls._find_col(df, col_mapping, ["supplier"])
        date_col = cls._find_date_col(df, col_mapping)
        region_col = cls._find_col(df, col_mapping, ["region"])
        category_col = cls._find_col(df, col_mapping, ["category", "product"])

        # ── Sales Performance ────────────────────────────
        if revenue_col and revenue_col in df.columns:
            total_sales = float(df[revenue_col].sum())
            insights.append(Insight(
                title="Total Sales",
                value=total_sales,
                formatted=cls._fmt_currency(total_sales),
                category="financial",
                description="Total sales/revenue across all records.",
            ))

            if order_col and order_col in df.columns:
                order_count = max(int(df[order_col].nunique()), 1)
                avg_order = total_sales / order_count
                insights.append(Insight(
                    title="Avg Order Value",
                    value=avg_order,
                    formatted=cls._fmt_currency(avg_order),
                    category="financial",
                    description="Average revenue per order.",
                ))

            if date_col:
                sales_trend = cls._compute_trend(df, date_col, revenue_col, "sum")
                if sales_trend:
                    sales_trend.metric = "sales"
                    trends.append(sales_trend)

        # ── Profitability ────────────────────────────────
        if profit_col and profit_col in df.columns:
            total_profit = float(df[profit_col].sum())
            insights.append(Insight(
                title="Total Profit",
                value=total_profit,
                formatted=cls._fmt_currency(total_profit),
                category="financial",
                description="Total profit across all records.",
            ))

            if revenue_col and revenue_col in df.columns:
                total_rev = float(df[revenue_col].sum())
                if total_rev > 0:
                    margin = (total_profit / total_rev * 100)
                    insights.append(Insight(
                        title="Profit Margin",
                        value=margin,
                        formatted=cls._fmt_pct(margin),
                        category="financial",
                        description="Profit as percentage of revenue.",
                        alert="warning" if margin < 15 else "ok",
                    ))

        # ── Customer Analytics ───────────────────────────
        if customer_col and customer_col in df.columns:
            customer_count = int(df[customer_col].nunique())
            insights.append(Insight(
                title="Total Customers",
                value=customer_count,
                formatted=cls._fmt_number(customer_count),
                category="operational",
                description="Unique customers.",
            ))

            if revenue_col and revenue_col in df.columns and customer_count > 0:
                revenue_per_customer = float(df[revenue_col].sum()) / customer_count
                insights.append(Insight(
                    title="Revenue per Customer",
                    value=revenue_per_customer,
                    formatted=cls._fmt_currency(revenue_per_customer),
                    category="financial",
                    description="Average revenue generated per customer.",
                ))

        # ── Product / Category Analysis ──────────────────
        if product_col and product_col in df.columns:
            product_count = int(df[product_col].nunique())
            insights.append(Insight(
                title="Products Sold",
                value=product_count,
                formatted=cls._fmt_number(product_count),
                category="operational",
                description="Distinct products in the dataset.",
            ))

            if revenue_col and revenue_col in df.columns:
                prod_bd = cls._compute_breakdown(df, product_col, revenue_col, "sum")
                if prod_bd:
                    prod_bd.dimension = "Product"
                    prod_bd.metric = "sales"
                    breakdowns.append(prod_bd)

        if category_col and category_col in df.columns and category_col != product_col:
            cat_count = int(df[category_col].nunique())
            insights.append(Insight(
                title="Product Categories",
                value=cat_count,
                formatted=cls._fmt_number(cat_count),
                category="operational",
                description="Distinct product categories.",
            ))

            if revenue_col and revenue_col in df.columns:
                cat_bd = cls._compute_breakdown(df, category_col, revenue_col, "sum")
                if cat_bd:
                    cat_bd.dimension = "Category"
                    cat_bd.metric = "sales"
                    breakdowns.append(cat_bd)

        # ── Order Analytics ──────────────────────────────
        if order_col and order_col in df.columns:
            order_count = int(df[order_col].nunique())
            insights.append(Insight(
                title="Total Orders",
                value=order_count,
                formatted=cls._fmt_number(order_count),
                category="operational",
                description="Unique orders processed.",
            ))

        # ── Inventory ────────────────────────────────────
        if inventory_col and inventory_col in df.columns:
            inventory_count = int(df[inventory_col].nunique())
            insights.append(Insight(
                title="Inventory Items",
                value=inventory_count,
                formatted=cls._fmt_number(inventory_count),
                category="operational",
                description="Unique inventory items tracked.",
            ))

        # ── Supplier ─────────────────────────────────────
        if supplier_col and supplier_col in df.columns:
            supplier_count = int(df[supplier_col].nunique())
            insights.append(Insight(
                title="Active Suppliers",
                value=supplier_count,
                formatted=cls._fmt_number(supplier_count),
                category="operational",
                description="Unique suppliers.",
            ))

        # ── Regional Analytics ───────────────────────────
        if region_col and region_col in df.columns:
            region_count = int(df[region_col].nunique())
            insights.append(Insight(
                title="Sales Regions",
                value=region_count,
                formatted=cls._fmt_number(region_count),
                category="operational",
                description="Number of distinct sales regions.",
            ))

            if revenue_col and revenue_col in df.columns:
                region_bd = cls._compute_breakdown(df, region_col, revenue_col, "sum")
                if region_bd:
                    region_bd.dimension = "Region"
                    region_bd.metric = "sales"
                    breakdowns.append(region_bd)

        recommendations.extend([
            "Monitor product profitability by category for pricing optimization.",
            "Track customer lifetime value segments for retention strategies.",
            "Review inventory turnover to identify slow-moving products.",
            "Analyze regional sales patterns for market expansion opportunities.",
        ])

        for insight in insights:
            if insight.alert == "warning":
                alerts.append(f"{insight.title}: {insight.formatted} — below target.")

        return AnalyticsResult(
            industry="retail",
            insights=insights,
            breakdowns=breakdowns,
            trends=trends,
            recommendations=recommendations,
            alerts=alerts,
        )


IndustryAnalyticsRegistry.register("retail", RetailAnalytics)
