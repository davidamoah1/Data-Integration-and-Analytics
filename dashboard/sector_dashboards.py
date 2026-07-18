"""Sector-specific dashboard rendering.

Each sector gets a completely different dashboard layout with:
- Different KPI cards (different metrics, not just relabeled)
- Different chart types and combinations
- Sector-specific charts (e.g. funding source pie for NGO, payment method breakdown for Church)
- Different section headers and descriptions
"""

import pandas as pd
import plotly.express as px
import streamlit as st

from dashboard.charts import (
    _chart_container,
    _close_container,
    render_heatmap_sales_region_category,
    render_kpi_cards,
    render_profit_by_region,
    render_profit_margin_by_category,
    render_revenue_by_category,
    render_revenue_over_time,
    render_sales_vs_profit_scatter,
    render_top_products,
)
from dashboard.styles import CHART_LAYOUT, COLORS
from dashboard.utils import fmt_currency, fmt_number


def _kpi_card(value: str, label: str, icon: str, css_class: str):
    st.markdown(
        f'<div class="kpi-card {css_class}"><span class="kpi-icon">{icon}</span>'
        f'<div class="kpi-value">{value}</div>'
        f'<div class="kpi-label">{label}</div></div>',
        unsafe_allow_html=True,
    )


def _section_header(title: str):
    st.markdown(
        f'<div class="section-header">{title}</div><hr class="section-divider">',
        unsafe_allow_html=True,
    )


def _pie_chart(df: pd.DataFrame, col: str, title: str, value_col: str = "sales"):
    _chart_container(title)
    if col in df.columns and value_col in df.columns:
        data = df.groupby(col)[value_col].sum().reset_index()
        data.columns = [col.title(), "Amount"]
        fig = px.pie(
            data,
            names=col.title(),
            values="Amount",
            color_discrete_sequence=COLORS,
            hole=0.45,
            template="none",
        )
        fig.update_traces(
            textfont=dict(color="white", size=12),
            marker=dict(line=dict(color="rgba(0,0,0,0.3)", width=2)),
        )
        layout = {k: v for k, v in CHART_LAYOUT.items() if k not in ("xaxis", "yaxis")}
        fig.update_layout(**layout, height=300)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info(f"No {col} column found.")
    _close_container()


def _bar_chart(df: pd.DataFrame, col: str, title: str, value_col: str = "sales", orientation: str = "h"):
    _chart_container(title)
    if col in df.columns and value_col in df.columns:
        data = df.groupby(col)[value_col].sum().sort_values(ascending=(orientation == "h")).reset_index()
        data.columns = [col.title(), "Amount"]
        fig = px.bar(
            data,
            x="Amount",
            y=col.title(),
            orientation=orientation,
            color="Amount",
            color_continuous_scale=["#4338ca", "#667eea", "#a78bfa"],
            template="none",
        )
        fig.update_coloraxes(showscale=False)
        fig.update_layout(**CHART_LAYOUT, height=300)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info(f"No {col} column found.")
    _close_container()


def _count_bar_chart(df: pd.DataFrame, col: str, title: str):
    _chart_container(title)
    if col in df.columns:
        counts = df[col].value_counts().reset_index()
        counts.columns = [col.title(), "Count"]
        fig = px.bar(
            counts,
            x="Count",
            y=col.title(),
            orientation="h",
            color="Count",
            color_continuous_scale=["#11998e", "#38ef7d"],
            template="none",
        )
        fig.update_coloraxes(showscale=False)
        fig.update_layout(**CHART_LAYOUT, height=300)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info(f"No {col} column found.")
    _close_container()


def _trend_chart(df: pd.DataFrame, title: str, value_col: str = "sales", y_label: str = "Amount"):
    _chart_container(title)
    if "order_date" in df.columns and df["order_date"].notna().any():
        df = df.copy()
        df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
        trend = (
            df.dropna(subset=["order_date"])
            .groupby(df["order_date"].dt.to_period("M").astype(str))[value_col]
            .sum()
            .reset_index()
        )
        trend.columns = ["Month", y_label]
        fig = px.area(
            trend, x="Month", y=y_label, color_discrete_sequence=["#667eea"], template="none"
        )
        fig.update_traces(
            fill="tozeroy",
            fillcolor="rgba(102,126,234,0.15)",
            line=dict(color="#667eea", width=2.5),
        )
        fig.update_layout(**CHART_LAYOUT, height=280)
        fig.update_xaxes(tickangle=-35)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No date column found for this chart.")
    _close_container()


# ──────────────────────────────────────────────
# SME Dashboard (default — sales focused)
# ──────────────────────────────────────────────
def render_sme_dashboard(df: pd.DataFrame, kpis: dict):
    labels = {
        "revenue": "Revenue", "profit": "Profit", "orders": "Orders",
        "avg_order": "Avg Order Value", "performance": "Sales Performance",
        "breakdown": "Profit and Regional Breakdown", "deep_dive": "Deep Dive Analysis",
        "regional": "Regional Analysis", "category_label": "Category",
        "product_label": "Top Products", "region_label": "Region",
    }
    render_kpi_cards(
        kpis["total_sales"], kpis["total_profit"], kpis["total_orders"],
        kpis["avg_order_value"], kpis["margin_pct"], labels=labels,
    )
    st.markdown("<br>", unsafe_allow_html=True)

    _section_header("Sales Performance")
    c1, c2 = st.columns(2)
    with c1:
        render_revenue_over_time(df, labels=labels)
    with c2:
        render_revenue_by_category(df, labels=labels)

    _section_header("Profit and Regional Breakdown")
    c3, c4 = st.columns(2)
    with c3:
        render_profit_by_region(df, labels=labels)
    with c4:
        render_top_products(df, labels=labels)

    if "profit" in df.columns and "sales" in df.columns and "category" in df.columns:
        _section_header("Deep Dive Analysis")
        c5, c6 = st.columns([3, 2])
        with c5:
            render_sales_vs_profit_scatter(df, labels=labels)
        with c6:
            render_profit_margin_by_category(df, labels=labels)

    if "region" in df.columns and "category" in df.columns and "sales" in df.columns:
        _section_header("Regional Analysis")
        render_heatmap_sales_region_category(df, labels=labels)


# ──────────────────────────────────────────────
# Healthcare Dashboard — patient billing focused
# ──────────────────────────────────────────────
def render_healthcare_dashboard(df: pd.DataFrame, kpis: dict):
    total_billing = kpis["total_sales"]
    total_patients = df["customer_name"].nunique() if "customer_name" in df.columns else kpis["total_orders"]
    avg_bill = kpis["avg_order_value"]
    dept_count = df["category"].nunique() if "category" in df.columns else 0

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        _kpi_card(fmt_currency(total_billing), "Total Billing", "🏥", "kpi-card-sales")
    with k2:
        _kpi_card(fmt_number(total_patients), "Total Patients", "👤", "kpi-card-orders")
    with k3:
        _kpi_card(fmt_currency(avg_bill), "Avg Bill Amount", "💊", "kpi-card-avg")
    with k4:
        _kpi_card(fmt_number(dept_count), "Departments", "📋", "kpi-card-profit")

    st.markdown("<br>", unsafe_allow_html=True)

    _section_header("Billing Performance")
    c1, c2 = st.columns(2)
    with c1:
        _trend_chart(df, "Billing Over Time", y_label="Billing Amount")
    with c2:
        _pie_chart(df, "category", "Billing by Department")

    _section_header("Service and Regional Breakdown")
    c3, c4 = st.columns(2)
    with c3:
        _bar_chart(df, "service_type" if "service_type" in df.columns else "category", "Billing by Service Type")
    with c4:
        render_profit_by_region(df, labels={"profit": "Net Billing"})

    if "insurance_type" in df.columns:
        _section_header("Insurance Breakdown")
        c5, c6 = st.columns(2)
        with c5:
            _pie_chart(df, "insurance_type", "Billing by Insurance Type")
        with c6:
            _count_bar_chart(df, "insurance_type", "Patient Count by Insurance")

    if "region" in df.columns and "category" in df.columns and "sales" in df.columns:
        _section_header("Regional Analysis")
        render_heatmap_sales_region_category(df, labels={
            "revenue": "Billing", "category_label": "Department"})


# ──────────────────────────────────────────────
# Education Dashboard — enrollment & tuition focused
# ──────────────────────────────────────────────
def render_education_dashboard(df: pd.DataFrame, kpis: dict):
    total_tuition = kpis["total_sales"]
    total_students = df["customer_name"].nunique() if "customer_name" in df.columns else kpis["total_orders"]
    avg_payment = kpis["avg_order_value"]
    program_count = df["category"].nunique() if "category" in df.columns else 0

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        _kpi_card(fmt_currency(total_tuition), "Total Tuition", "🎓", "kpi-card-sales")
    with k2:
        _kpi_card(fmt_number(total_students), "Total Students", "👨‍🎓", "kpi-card-orders")
    with k3:
        _kpi_card(fmt_currency(avg_payment), "Avg Payment", "💳", "kpi-card-avg")
    with k4:
        _kpi_card(fmt_number(program_count), "Programs", "📚", "kpi-card-profit")

    st.markdown("<br>", unsafe_allow_html=True)

    _section_header("Enrollment & Revenue Performance")
    c1, c2 = st.columns(2)
    with c1:
        _trend_chart(df, "Tuition Revenue Over Time", y_label="Tuition")
    with c2:
        _pie_chart(df, "category", "Revenue by Program Type")

    _section_header("Department and Regional Breakdown")
    c3, c4 = st.columns(2)
    with c3:
        _bar_chart(df, "department" if "department" in df.columns else "category", "Revenue by Department")
    with c4:
        render_profit_by_region(df, labels={"profit": "Net Revenue"})

    if "payment_method" in df.columns:
        _section_header("Payment Analysis")
        c5, c6 = st.columns(2)
        with c5:
            _pie_chart(df, "payment_method", "Revenue by Payment Method")
        with c6:
            _count_bar_chart(df, "payment_method", "Transactions by Payment Method")

    if "region" in df.columns and "category" in df.columns and "sales" in df.columns:
        _section_header("Regional Analysis")
        render_heatmap_sales_region_category(df, labels={
            "revenue": "Tuition", "category_label": "Program Type"})


# ──────────────────────────────────────────────
# Government Dashboard — public spending focused
# ──────────────────────────────────────────────
def render_government_dashboard(df: pd.DataFrame, kpis: dict):
    total_spending = kpis["total_sales"]
    total_projects = kpis["total_orders"]
    avg_project = kpis["avg_order_value"]
    dept_count = df["category"].nunique() if "category" in df.columns else 0

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        _kpi_card(fmt_currency(total_spending), "Total Spending", "🏛️", "kpi-card-sales")
    with k2:
        _kpi_card(fmt_number(total_projects), "Total Projects", "🏗️", "kpi-card-orders")
    with k3:
        _kpi_card(fmt_currency(avg_project), "Avg Project Cost", "📐", "kpi-card-avg")
    with k4:
        _kpi_card(fmt_number(dept_count), "Departments", "📋", "kpi-card-profit")

    st.markdown("<br>", unsafe_allow_html=True)

    _section_header("Spending Performance")
    c1, c2 = st.columns(2)
    with c1:
        _trend_chart(df, "Spending Over Time", y_label="Spending")
    with c2:
        _pie_chart(df, "category", "Spending by Project Type")

    _section_header("Department and Regional Breakdown")
    c3, c4 = st.columns(2)
    with c3:
        _bar_chart(df, "department" if "department" in df.columns else "category", "Spending by Department")
    with c4:
        _bar_chart(df, "region", "Spending by Region")

    if "contractor_name" in df.columns:
        _section_header("Contractor Analysis")
        render_top_products(df, labels={
            "product_label": "Contractors", "revenue": "Spending"})

    if "region" in df.columns and "category" in df.columns and "sales" in df.columns:
        _section_header("Regional Analysis")
        render_heatmap_sales_region_category(df, labels={
            "revenue": "Spending", "category_label": "Project Type"})


# ──────────────────────────────────────────────
# Church Dashboard — tithes & offerings focused
# ──────────────────────────────────────────────
def render_church_dashboard(df: pd.DataFrame, kpis: dict):
    total_offering = kpis["total_sales"]
    total_transactions = kpis["total_orders"]
    avg_offering = kpis["avg_order_value"]
    event_count = df["category"].nunique() if "category" in df.columns else 0

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        _kpi_card(fmt_currency(total_offering), "Total Offerings", "⛪", "kpi-card-sales")
    with k2:
        _kpi_card(fmt_number(total_transactions), "Transactions", "🤝", "kpi-card-orders")
    with k3:
        _kpi_card(fmt_currency(avg_offering), "Avg Offering", "🙏", "kpi-card-avg")
    with k4:
        _kpi_card(fmt_number(event_count), "Event Types", "📅", "kpi-card-profit")

    st.markdown("<br>", unsafe_allow_html=True)

    _section_header("Offerings Performance")
    c1, c2 = st.columns(2)
    with c1:
        _trend_chart(df, "Offerings Over Time", y_label="Offerings")
    with c2:
        _pie_chart(df, "category", "Offerings by Event Type")

    _section_header("Department and Regional Breakdown")
    c3, c4 = st.columns(2)
    with c3:
        _bar_chart(df, "department" if "department" in df.columns else "category", "Offerings by Department")
    with c4:
        _bar_chart(df, "region", "Offerings by Region")

    if "payment_method" in df.columns:
        _section_header("Payment Analysis")
        c5, c6 = st.columns(2)
        with c5:
            _pie_chart(df, "payment_method", "Offerings by Payment Method")
        with c6:
            _count_bar_chart(df, "payment_method", "Transactions by Payment Method")

    if "region" in df.columns and "category" in df.columns and "sales" in df.columns:
        _section_header("Regional Analysis")
        render_heatmap_sales_region_category(df, labels={
            "revenue": "Offerings", "category_label": "Event Type"})


# ──────────────────────────────────────────────
# NGO Dashboard — donations & programs focused
# ──────────────────────────────────────────────
def render_ngo_dashboard(df: pd.DataFrame, kpis: dict):
    total_donations = kpis["total_sales"]
    total_transactions = kpis["total_orders"]
    avg_donation = kpis["avg_order_value"]
    program_count = df["category"].nunique() if "category" in df.columns else 0

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        _kpi_card(fmt_currency(total_donations), "Total Donations", "🌍", "kpi-card-sales")
    with k2:
        _kpi_card(fmt_number(total_transactions), "Transactions", "📦", "kpi-card-orders")
    with k3:
        _kpi_card(fmt_currency(avg_donation), "Avg Donation", "💝", "kpi-card-avg")
    with k4:
        _kpi_card(fmt_number(program_count), "Programs", "🎯", "kpi-card-profit")

    st.markdown("<br>", unsafe_allow_html=True)

    _section_header("Donations Performance")
    c1, c2 = st.columns(2)
    with c1:
        _trend_chart(df, "Donations Over Time", y_label="Donations")
    with c2:
        _pie_chart(df, "category", "Donations by Program Type")

    _section_header("Program and Regional Breakdown")
    c3, c4 = st.columns(2)
    with c3:
        _bar_chart(df, "region", "Donations by Region")
    with c4:
        _bar_chart(df, "funding_source" if "funding_source" in df.columns else "category",
                    "Donations by Funding Source")

    if "funding_source" in df.columns:
        _section_header("Funding Source Analysis")
        c5, c6 = st.columns(2)
        with c5:
            _pie_chart(df, "funding_source", "Donations by Funding Source")
        with c6:
            _count_bar_chart(df, "funding_source", "Transactions by Funding Source")

    if "region" in df.columns and "category" in df.columns and "sales" in df.columns:
        _section_header("Regional Analysis")
        render_heatmap_sales_region_category(df, labels={
            "revenue": "Donations", "category_label": "Program Type"})


# ──────────────────────────────────────────────
# Dispatcher
# ──────────────────────────────────────────────
SECTOR_RENDERERS = {
    "sme": render_sme_dashboard,
    "education": render_education_dashboard,
    "healthcare": render_healthcare_dashboard,
    "government": render_government_dashboard,
    "church": render_church_dashboard,
    "ngo": render_ngo_dashboard,
}


def render_sector_dashboard(df: pd.DataFrame, kpis: dict, pack_key: str | None = None):
    """Render the appropriate dashboard for the selected sector.

    Falls back to SME dashboard if no pack is selected.
    """
    renderer = SECTOR_RENDERERS.get(pack_key or "sme", render_sme_dashboard)
    renderer(df, kpis)
