"""Sector-specific dashboard rendering.

Each sector gets a completely different dashboard with:
- Different KPI metrics (calculated differently per sector)
- Different chart types (treemaps, sunbursts, funnels, waterfalls, icicles, rose charts)
- Sector-specific analytics that don't exist in other sectors
- Different layout structures per sector

Sectors:
  SME         — Sales, profit, products, regions
  Education   — Enrollment, tuition collection, department performance, payment methods
  Healthcare  — Patient billing, insurance claims, service mix, department efficiency
  Government  — Project spending, contractor performance, budget allocation, regional projects
  Church      — Offerings by event, member giving patterns, payment channels, ministry performance
  NGO         — Donations by program, funding source diversity, donor engagement, regional impact
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from dashboard.styles import CHART_LAYOUT, COLORS
from dashboard.utils import fmt_currency, fmt_number


# ──────────────────────────────────────────────
# Shared helpers
# ──────────────────────────────────────────────
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


def _chart_container(title: str):
    st.markdown(
        f'<div class="chart-container"><div class="chart-title">{title}</div>',
        unsafe_allow_html=True,
    )


def _close_container():
    st.markdown("</div>", unsafe_allow_html=True)


def _safe_col(df: pd.DataFrame, *candidates: str) -> str | None:
    """Return the first column name that exists in df (case-insensitive)."""
    lower_map = {c.lower(): c for c in df.columns}
    for c in candidates:
        if c.lower() in lower_map:
            return lower_map[c.lower()]
    return None


# ──────────────────────────────────────────────
# SME Dashboard — Sales & Profit Analytics
# ──────────────────────────────────────────────
def render_sme_dashboard(df: pd.DataFrame, kpis: dict):
    from dashboard.charts import (
        render_heatmap_sales_region_category,
        render_kpi_cards,
        render_profit_by_region,
        render_profit_margin_by_category,
        render_revenue_by_category,
        render_revenue_over_time,
        render_sales_vs_profit_scatter,
        render_top_products,
    )

    labels = {
        "revenue": "Revenue",
        "profit": "Profit",
        "orders": "Orders",
        "avg_order": "Avg Order Value",
        "performance": "Sales Performance",
        "breakdown": "Profit and Regional Breakdown",
        "deep_dive": "Deep Dive Analysis",
        "regional": "Regional Analysis",
        "category_label": "Category",
        "product_label": "Top Products",
        "region_label": "Region",
    }
    render_kpi_cards(
        kpis["total_sales"],
        kpis["total_profit"],
        kpis["total_orders"],
        kpis["avg_order_value"],
        kpis["margin_pct"],
        labels=labels,
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
# Education Dashboard — Enrollment & Tuition Analytics
# ──────────────────────────────────────────────
def render_education_dashboard(df: pd.DataFrame, kpis: dict):
    sales_col = _safe_col(df, "sales") or "sales"
    cat_col = _safe_col(df, "category", "program_type") or "category"
    dept_col = _safe_col(df, "department") or cat_col
    date_col = _safe_col(df, "order_date") or "order_date"
    student_col = _safe_col(df, "customer_name", "student_name")
    pay_col = _safe_col(df, "payment_method")
    region_col = _safe_col(df, "region")
    qty_col = _safe_col(df, "quantity")
    discount_col = _safe_col(df, "discount")

    total_tuition = df[sales_col].sum() if sales_col in df.columns else 0
    total_students = df[student_col].nunique() if student_col else 0
    total_enrollments = df[qty_col].sum() if qty_col in df.columns else 0
    total_discounts = df[discount_col].sum() if discount_col in df.columns else 0
    collection_rate = (
        ((total_tuition - total_discounts) / total_tuition * 100) if total_tuition > 0 else 0
    )

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        _kpi_card(fmt_currency(total_tuition), "Total Tuition Billed", "🎓", "kpi-card-sales")
    with k2:
        _kpi_card(fmt_number(total_students), "Enrolled Students", "👨‍🎓", "kpi-card-orders")
    with k3:
        _kpi_card(f"{collection_rate:.1f}%", "Collection Rate", "📊", "kpi-card-profit")
    with k4:
        _kpi_card(fmt_number(int(total_enrollments)), "Total Enrollments", "📚", "kpi-card-avg")

    st.markdown("<br>", unsafe_allow_html=True)

    _section_header("Tuition Collection Trend")
    _chart_container("Monthly Tuition Collected")
    if date_col in df.columns and df[date_col].notna().any():
        _df = df.copy()
        _df[date_col] = pd.to_datetime(_df[date_col], errors="coerce")
        trend = (
            _df.dropna(subset=[date_col])
            .groupby(_df[date_col].dt.to_period("M").astype(str))[sales_col]
            .sum()
            .reset_index()
        )
        trend.columns = ["Month", "Tuition"]
        fig = px.area(
            trend, x="Month", y="Tuition", color_discrete_sequence=["#667eea"], template="none"
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
        st.info("No date column found.")
    _close_container()

    _section_header("Program & Department Analytics")
    c1, c2 = st.columns(2)
    with c1:
        _chart_container("Tuition by Program Type (Treemap)")
        if cat_col in df.columns and sales_col in df.columns:
            tdata = df.groupby(cat_col)[sales_col].sum().reset_index()
            tdata.columns = ["Program", "Tuition"]
            fig = px.treemap(
                tdata,
                path=["Program"],
                values="Tuition",
                color="Tuition",
                color_continuous_scale=["#4338ca", "#667eea", "#a78bfa"],
                template="none",
            )
            fig.update_layout(
                **{k: v for k, v in CHART_LAYOUT.items() if k not in ("xaxis", "yaxis")}, height=300
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No program data found.")
        _close_container()

    with c2:
        _chart_container("Enrollments by Department (Bar)")
        if dept_col in df.columns and qty_col in df.columns:
            ddata = df.groupby(dept_col)[qty_col].sum().sort_values(ascending=True).reset_index()
            ddata.columns = ["Department", "Enrollments"]
            fig = px.bar(
                ddata,
                x="Enrollments",
                y="Department",
                orientation="h",
                color="Enrollments",
                color_continuous_scale=["#11998e", "#38ef7d"],
                template="none",
            )
            fig.update_coloraxes(showscale=False)
            fig.update_layout(**CHART_LAYOUT, height=300)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No department data found.")
        _close_container()

    if pay_col and pay_col in df.columns:
        _section_header("Payment Method Analysis")
        c3, c4 = st.columns(2)
        with c3:
            _chart_container("Payment Method Distribution (Sunburst)")
            pdata = df.groupby(pay_col)[sales_col].sum().reset_index()
            pdata.columns = ["Method", "Amount"]
            fig = px.sunburst(
                pdata,
                path=["Method"],
                values="Amount",
                color_discrete_sequence=COLORS,
                template="none",
            )
            fig.update_layout(
                **{k: v for k, v in CHART_LAYOUT.items() if k not in ("xaxis", "yaxis")}, height=300
            )
            st.plotly_chart(fig, use_container_width=True)
            _close_container()
        with c4:
            _chart_container("Discount Impact by Program")
            if cat_col in df.columns and discount_col in df.columns and sales_col in df.columns:
                disc = (
                    df.groupby(cat_col)
                    .agg(Tuition=(sales_col, "sum"), Discount=(discount_col, "sum"))
                    .reset_index()
                )
                disc = disc.sort_values("Tuition", ascending=True)
                fig = go.Figure()
                fig.add_trace(
                    go.Bar(
                        y=disc[cat_col],
                        x=disc["Tuition"],
                        orientation="h",
                        name="Tuition",
                        marker_color="#667eea",
                    )
                )
                fig.add_trace(
                    go.Bar(
                        y=disc[cat_col],
                        x=-disc["Discount"],
                        orientation="h",
                        name="Discount",
                        marker_color="#f5576c",
                    )
                )
                fig.update_layout(
                    barmode="relative",
                    **CHART_LAYOUT,
                    height=300,
                    showlegend=True,
                    legend=dict(font=dict(color="white")),
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No discount data found.")
            _close_container()

    if region_col and cat_col in df.columns and sales_col in df.columns:
        _section_header("Regional Enrollment Heatmap")
        _chart_container("Tuition Heatmap: Region x Program Type")
        pivot = df.groupby([region_col, cat_col])[sales_col].sum().reset_index()
        fig = go.Figure(
            data=go.Heatmap(
                z=pivot[sales_col],
                x=pivot[cat_col],
                y=pivot[region_col],
                colorscale=[[0, "#1a1a4e"], [0.5, "#667eea"], [1, "#f093fb"]],
                text=pivot[sales_col].round(0),
                texttemplate="$%{text:,.0f}",
                textfont=dict(color="white", size=10),
            )
        )
        fig.update_layout(
            **{k: v for k, v in CHART_LAYOUT.items() if k not in ("xaxis", "yaxis")}, height=300
        )
        st.plotly_chart(fig, use_container_width=True)
        _close_container()


# ──────────────────────────────────────────────
# Healthcare Dashboard — Patient Billing & Insurance Analytics
# ──────────────────────────────────────────────
def render_healthcare_dashboard(df: pd.DataFrame, kpis: dict):
    sales_col = _safe_col(df, "sales") or "sales"
    cat_col = _safe_col(df, "category", "service_type") or "category"
    dept_col = _safe_col(df, "department") or cat_col
    date_col = _safe_col(df, "order_date") or "order_date"
    patient_col = _safe_col(df, "customer_name", "patient_name")
    insurance_col = _safe_col(df, "insurance_type")
    region_col = _safe_col(df, "region")
    qty_col = _safe_col(df, "quantity")
    discount_col = _safe_col(df, "discount")

    total_billing = df[sales_col].sum() if sales_col in df.columns else 0
    total_patients = df[patient_col].nunique() if patient_col else 0
    total_discounts = df[discount_col].sum() if discount_col in df.columns else 0
    avg_bill_per_patient = (total_billing / total_patients) if total_patients > 0 else 0
    insurance_coverage = (total_discounts / total_billing * 100) if total_billing > 0 else 0

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        _kpi_card(fmt_currency(total_billing), "Total Billing", "🏥", "kpi-card-sales")
    with k2:
        _kpi_card(fmt_number(total_patients), "Unique Patients", "👤", "kpi-card-orders")
    with k3:
        _kpi_card(fmt_currency(avg_bill_per_patient), "Avg Bill / Patient", "💊", "kpi-card-avg")
    with k4:
        _kpi_card(f"{insurance_coverage:.1f}%", "Insurance Coverage", "🛡️", "kpi-card-profit")

    st.markdown("<br>", unsafe_allow_html=True)

    _section_header("Billing Activity Over Time")
    _chart_container("Daily Billing Volume")
    if date_col in df.columns and df[date_col].notna().any():
        _df = df.copy()
        _df[date_col] = pd.to_datetime(_df[date_col], errors="coerce")
        daily = (
            _df.dropna(subset=[date_col])
            .groupby(_df[date_col].dt.date)[sales_col]
            .sum()
            .reset_index()
        )
        daily.columns = ["Date", "Billing"]
        fig = px.line(
            daily, x="Date", y="Billing", color_discrete_sequence=["#f093fb"], template="none"
        )
        fig.update_traces(line=dict(width=2))
        fig.update_layout(**CHART_LAYOUT, height=280)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No date column found.")
    _close_container()

    _section_header("Service Mix & Department Analysis")
    c1, c2 = st.columns(2)
    with c1:
        _chart_container("Service Type Funnel")
        if cat_col in df.columns and sales_col in df.columns:
            fdata = df.groupby(cat_col)[sales_col].sum().sort_values(ascending=False).reset_index()
            fdata.columns = ["Service", "Billing"]
            fig = px.funnel(
                fdata, x="Billing", y="Service", color_discrete_sequence=COLORS, template="none"
            )
            fig.update_layout(
                **{k: v for k, v in CHART_LAYOUT.items() if k not in ("xaxis", "yaxis")}, height=300
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No service data found.")
        _close_container()

    with c2:
        _chart_container("Patient Volume by Department")
        if dept_col in df.columns and patient_col:
            dpdata = (
                df.groupby(dept_col)[patient_col]
                .nunique()
                .sort_values(ascending=True)
                .reset_index()
            )
            dpdata.columns = ["Department", "Patients"]
            fig = px.bar(
                dpdata,
                x="Patients",
                y="Department",
                orientation="h",
                color="Patients",
                color_continuous_scale=["#f5576c", "#ffd200", "#38ef7d"],
                template="none",
            )
            fig.update_coloraxes(showscale=False)
            fig.update_layout(**CHART_LAYOUT, height=300)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No department data found.")
        _close_container()

    if insurance_col and insurance_col in df.columns:
        _section_header("Insurance & Coverage Analysis")
        c3, c4 = st.columns(2)
        with c3:
            _chart_container("Billing by Insurance Type (Donut)")
            idata = df.groupby(insurance_col)[sales_col].sum().reset_index()
            idata.columns = ["Insurance", "Billing"]
            fig = px.pie(
                idata,
                names="Insurance",
                values="Billing",
                color_discrete_sequence=COLORS,
                hole=0.5,
                template="none",
            )
            fig.update_traces(
                textfont=dict(color="white", size=12),
                marker=dict(line=dict(color="rgba(0,0,0,0.3)", width=2)),
            )
            fig.update_layout(
                **{k: v for k, v in CHART_LAYOUT.items() if k not in ("xaxis", "yaxis")}, height=300
            )
            st.plotly_chart(fig, use_container_width=True)
            _close_container()
        with c4:
            _chart_container("Insurance Coverage by Department (Stacked)")
            if dept_col in df.columns and sales_col in df.columns:
                sdata = df.groupby([dept_col, insurance_col])[sales_col].sum().reset_index()
                sdata.columns = ["Department", "Insurance", "Billing"]
                fig = px.bar(
                    sdata,
                    x="Department",
                    y="Billing",
                    color="Insurance",
                    color_discrete_sequence=COLORS,
                    template="none",
                    barmode="stack",
                )
                fig.update_layout(
                    **CHART_LAYOUT, height=300, legend=dict(font=dict(color="white", size=10))
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No insurance data found.")
            _close_container()

    if region_col and dept_col in df.columns and sales_col in df.columns:
        _section_header("Regional Department Performance")
        _chart_container("Billing Bubble: Region x Department")
        bub = (
            df.groupby([region_col, dept_col])
            .agg(
                Billing=(sales_col, "sum"),
                Services=(qty_col if qty_col in df.columns else sales_col, "count"),
            )
            .reset_index()
        )
        bub.columns = ["Region", "Department", "Billing", "Services"]
        fig = px.scatter(
            bub,
            x="Region",
            y="Department",
            size="Billing",
            color="Billing",
            color_continuous_scale=["#1a1a4e", "#667eea", "#f093fb"],
            template="none",
            size_max=40,
        )
        fig.update_layout(**CHART_LAYOUT, height=300)
        st.plotly_chart(fig, use_container_width=True)
        _close_container()


# ──────────────────────────────────────────────
# Government Dashboard — Project Spending & Contractor Analytics
# ──────────────────────────────────────────────
def render_government_dashboard(df: pd.DataFrame, kpis: dict):
    sales_col = _safe_col(df, "sales") or "sales"
    cat_col = _safe_col(df, "category", "project_type") or "category"
    dept_col = _safe_col(df, "department") or cat_col
    date_col = _safe_col(df, "order_date") or "order_date"
    contractor_col = _safe_col(df, "product_name", "contractor_name")
    region_col = _safe_col(df, "region")
    order_id_col = _safe_col(df, "order_id") or "order_id"

    total_spending = df[sales_col].sum() if sales_col in df.columns else 0
    total_projects = df[order_id_col].nunique() if order_id_col in df.columns else len(df)
    total_contractors = df[contractor_col].nunique() if contractor_col else 0
    avg_project_cost = (total_spending / total_projects) if total_projects > 0 else 0

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        _kpi_card(fmt_currency(total_spending), "Total Spending", "🏛️", "kpi-card-sales")
    with k2:
        _kpi_card(fmt_number(total_projects), "Total Projects", "🏗️", "kpi-card-orders")
    with k3:
        _kpi_card(fmt_currency(avg_project_cost), "Avg Project Cost", "📐", "kpi-card-avg")
    with k4:
        _kpi_card(fmt_number(total_contractors), "Active Contractors", "👷", "kpi-card-profit")

    st.markdown("<br>", unsafe_allow_html=True)

    _section_header("Budget Allocation Over Time")
    _chart_container("Monthly Spending (Waterfall)")
    if date_col in df.columns and df[date_col].notna().any():
        _df = df.copy()
        _df[date_col] = pd.to_datetime(_df[date_col], errors="coerce")
        monthly = (
            _df.dropna(subset=[date_col])
            .groupby(_df[date_col].dt.to_period("M").astype(str))[sales_col]
            .sum()
            .reset_index()
        )
        monthly.columns = ["Month", "Spending"]
        fig = go.Figure(
            go.Waterfall(
                x=monthly["Month"],
                y=monthly["Spending"],
                connector=dict(line=dict(color="rgba(255,255,255,0.2)")),
                increasing=dict(marker=dict(color="#38ef7d")),
                decreasing=dict(marker=dict(color="#f5576c")),
                totals=dict(marker=dict(color="#667eea")),
            )
        )
        fig.update_layout(**CHART_LAYOUT, height=280, xaxis=dict(tickangle=-35))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No date column found.")
    _close_container()

    _section_header("Project & Department Allocation")
    c1, c2 = st.columns(2)
    with c1:
        _chart_container("Spending by Project Type (Icicle)")
        if cat_col in df.columns and sales_col in df.columns and dept_col in df.columns:
            idata = df.groupby([dept_col, cat_col])[sales_col].sum().reset_index()
            idata.columns = ["Department", "Project", "Spending"]
            fig = px.icicle(
                idata,
                path=["Department", "Project"],
                values="Spending",
                color="Spending",
                color_continuous_scale=["#4338ca", "#667eea", "#a78bfa"],
                template="none",
            )
            fig.update_layout(
                **{k: v for k, v in CHART_LAYOUT.items() if k not in ("xaxis", "yaxis")}, height=300
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No project data found.")
        _close_container()

    with c2:
        _chart_container("Spending by Department (Bar)")
        if dept_col in df.columns and sales_col in df.columns:
            ddata = df.groupby(dept_col)[sales_col].sum().sort_values(ascending=False).reset_index()
            ddata.columns = ["Department", "Spending"]
            fig = px.bar(
                ddata,
                x="Department",
                y="Spending",
                color="Spending",
                color_continuous_scale=["#f5576c", "#ffd200", "#38ef7d"],
                template="none",
            )
            fig.update_coloraxes(showscale=False)
            fig.update_layout(**CHART_LAYOUT, height=300)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No department data found.")
        _close_container()

    if contractor_col and contractor_col in df.columns:
        _section_header("Contractor Performance")
        _chart_container("Top Contractors by Spending & Project Count")
        cdata = (
            df.groupby(contractor_col)
            .agg(
                Spending=(sales_col, "sum"),
                Projects=(order_id_col, "count"),
            )
            .reset_index()
        )
        cdata.columns = ["Contractor", "Spending", "Projects"]
        cdata = cdata.sort_values("Spending", ascending=True).tail(10)
        fig = px.bar(
            cdata,
            x="Spending",
            y="Contractor",
            orientation="h",
            text="Projects",
            color="Spending",
            color_continuous_scale=["#11998e", "#38ef7d"],
            template="none",
        )
        fig.update_traces(
            texttemplate="%{text} projects",
            textposition="outside",
            textfont=dict(color="white", size=10),
        )
        fig.update_coloraxes(showscale=False)
        fig.update_layout(**CHART_LAYOUT, height=350)
        st.plotly_chart(fig, use_container_width=True)
        _close_container()

    if region_col and sales_col in df.columns:
        _section_header("Regional Project Distribution")
        _chart_container("Projects vs Spending by Region (Dual Axis)")
        regional = (
            df.groupby(region_col)
            .agg(
                Spending=(sales_col, "sum"),
                Projects=(order_id_col, "count"),
            )
            .reset_index()
        )
        regional.columns = ["Region", "Spending", "Projects"]
        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                x=regional["Region"],
                y=regional["Spending"],
                name="Spending",
                marker_color="#667eea",
                yaxis="y",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=regional["Region"],
                y=regional["Projects"],
                name="Projects",
                mode="lines+markers",
                line=dict(color="#f093fb", width=3),
                yaxis="y2",
            )
        )
        fig.update_layout(
            **CHART_LAYOUT,
            height=300,
            yaxis=dict(title="Spending", side="left"),
            yaxis2=dict(title="Projects", side="right", overlaying="y"),
            legend=dict(font=dict(color="white", size=10)),
        )
        st.plotly_chart(fig, use_container_width=True)
        _close_container()


# ──────────────────────────────────────────────
# Church Dashboard — Offerings & Giving Analytics
# ──────────────────────────────────────────────
def render_church_dashboard(df: pd.DataFrame, kpis: dict):
    sales_col = _safe_col(df, "sales") or "sales"
    cat_col = _safe_col(df, "category", "event_type") or "category"
    dept_col = _safe_col(df, "department") or cat_col
    date_col = _safe_col(df, "order_date") or "order_date"
    member_col = _safe_col(df, "customer_name", "member_name")
    pay_col = _safe_col(df, "payment_method")

    total_offering = df[sales_col].sum() if sales_col in df.columns else 0
    total_members = df[member_col].nunique() if member_col else 0
    total_transactions = len(df)
    avg_offering = (total_offering / total_transactions) if total_transactions > 0 else 0
    giving_rate = (total_transactions / total_members * 100) if total_members > 0 else 0

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        _kpi_card(fmt_currency(total_offering), "Total Offerings", "⛪", "kpi-card-sales")
    with k2:
        _kpi_card(fmt_number(total_members), "Active Members", "🤝", "kpi-card-orders")
    with k3:
        _kpi_card(fmt_currency(avg_offering), "Avg Offering", "🙏", "kpi-card-avg")
    with k4:
        _kpi_card(f"{giving_rate:.0f}%", "Member Giving Rate", "💝", "kpi-card-profit")

    st.markdown("<br>", unsafe_allow_html=True)

    _section_header("Offering Trends by Event")
    _chart_container("Monthly Offerings by Event Type (Stacked Area)")
    if date_col in df.columns and cat_col in df.columns and df[date_col].notna().any():
        _df = df.copy()
        _df[date_col] = pd.to_datetime(_df[date_col], errors="coerce")
        trend = (
            _df.dropna(subset=[date_col])
            .groupby([_df[date_col].dt.to_period("M").astype(str), cat_col])[sales_col]
            .sum()
            .reset_index()
        )
        trend.columns = ["Month", "Event", "Offering"]
        fig = px.area(
            trend,
            x="Month",
            y="Offering",
            color="Event",
            color_discrete_sequence=COLORS,
            template="none",
        )
        fig.update_layout(
            **CHART_LAYOUT, height=300, legend=dict(font=dict(color="white", size=10))
        )
        fig.update_xaxes(tickangle=-35)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No date or event data found.")
    _close_container()

    _section_header("Event & Ministry Analytics")
    c1, c2 = st.columns(2)
    with c1:
        _chart_container("Offerings by Event Type (Rose Chart)")
        if cat_col in df.columns and sales_col in df.columns:
            edata = df.groupby(cat_col)[sales_col].sum().reset_index()
            edata.columns = ["Event", "Offering"]
            fig = px.bar_polar(
                edata,
                r="Offering",
                theta="Event",
                color="Offering",
                color_continuous_scale=["#4338ca", "#667eea", "#f093fb"],
                template="none",
            )
            fig.update_layout(
                **{k: v for k, v in CHART_LAYOUT.items() if k not in ("xaxis", "yaxis")}, height=300
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No event data found.")
        _close_container()

    with c2:
        _chart_container("Ministry Performance (Bar)")
        if dept_col in df.columns and sales_col in df.columns:
            mdata = df.groupby(dept_col)[sales_col].sum().sort_values(ascending=True).reset_index()
            mdata.columns = ["Ministry", "Offering"]
            fig = px.bar(
                mdata,
                x="Offering",
                y="Ministry",
                orientation="h",
                color="Offering",
                color_continuous_scale=["#11998e", "#38ef7d"],
                template="none",
            )
            fig.update_coloraxes(showscale=False)
            fig.update_layout(**CHART_LAYOUT, height=300)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No ministry data found.")
        _close_container()

    if pay_col and pay_col in df.columns:
        _section_header("Payment Channel Analysis")
        c3, c4 = st.columns(2)
        with c3:
            _chart_container("Offerings by Payment Method (Pie)")
            pdata = df.groupby(pay_col)[sales_col].sum().reset_index()
            pdata.columns = ["Method", "Offering"]
            fig = px.pie(
                pdata,
                names="Method",
                values="Offering",
                color_discrete_sequence=COLORS,
                hole=0.4,
                template="none",
            )
            fig.update_traces(
                textfont=dict(color="white", size=12),
                marker=dict(line=dict(color="rgba(0,0,0,0.3)", width=2)),
            )
            fig.update_layout(
                **{k: v for k, v in CHART_LAYOUT.items() if k not in ("xaxis", "yaxis")}, height=300
            )
            st.plotly_chart(fig, use_container_width=True)
            _close_container()
        with c4:
            _chart_container("Offering Distribution by Payment Method (Box)")
            fig = px.box(
                df,
                x=pay_col,
                y=sales_col,
                color=pay_col,
                color_discrete_sequence=COLORS,
                template="none",
            )
            fig.update_layout(**CHART_LAYOUT, height=300, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
            _close_container()

    if member_col and member_col in df.columns and sales_col in df.columns:
        _section_header("Member Giving Patterns")
        _chart_container("Top 15 Contributors by Total Giving")
        mgiving = (
            df.groupby(member_col)[sales_col]
            .sum()
            .sort_values(ascending=False)
            .head(15)
            .reset_index()
        )
        mgiving.columns = ["Member", "Total Giving"]
        fig = px.bar(
            mgiving,
            x="Total Giving",
            y="Member",
            orientation="h",
            color="Total Giving",
            color_continuous_scale=["#f5576c", "#ffd200", "#38ef7d"],
            template="none",
        )
        fig.update_coloraxes(showscale=False)
        fig.update_layout(**CHART_LAYOUT, height=350, yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig, use_container_width=True)
        _close_container()


# ──────────────────────────────────────────────
# NGO Dashboard — Donations & Program Impact Analytics
# ──────────────────────────────────────────────
def render_ngo_dashboard(df: pd.DataFrame, kpis: dict):
    sales_col = _safe_col(df, "sales") or "sales"
    cat_col = _safe_col(df, "category", "program_type") or "category"
    date_col = _safe_col(df, "order_date") or "order_date"
    donor_col = _safe_col(df, "customer_name", "donor_name")
    funding_col = _safe_col(df, "funding_source")
    region_col = _safe_col(df, "region")
    qty_col = _safe_col(df, "quantity")

    total_donations = df[sales_col].sum() if sales_col in df.columns else 0
    total_donors = df[donor_col].nunique() if donor_col else 0
    total_transactions = len(df)
    avg_donation = (total_donations / total_transactions) if total_transactions > 0 else 0
    beneficiaries = df[qty_col].sum() if qty_col in df.columns else 0

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        _kpi_card(fmt_currency(total_donations), "Total Donations", "🌍", "kpi-card-sales")
    with k2:
        _kpi_card(fmt_number(total_donors), "Active Donors", "🤲", "kpi-card-orders")
    with k3:
        _kpi_card(fmt_currency(avg_donation), "Avg Donation Size", "💝", "kpi-card-avg")
    with k4:
        _kpi_card(fmt_number(int(beneficiaries)), "Beneficiaries Reached", "👥", "kpi-card-profit")

    st.markdown("<br>", unsafe_allow_html=True)

    _section_header("Donation Growth Over Time")
    _chart_container("Monthly Donations & Cumulative Growth")
    if date_col in df.columns and df[date_col].notna().any():
        _df = df.copy()
        _df[date_col] = pd.to_datetime(_df[date_col], errors="coerce")
        monthly = (
            _df.dropna(subset=[date_col])
            .groupby(_df[date_col].dt.to_period("M").astype(str))[sales_col]
            .sum()
            .reset_index()
        )
        monthly.columns = ["Month", "Donations"]
        monthly["Cumulative"] = monthly["Donations"].cumsum()
        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                x=monthly["Month"], y=monthly["Donations"], name="Monthly", marker_color="#667eea"
            )
        )
        fig.add_trace(
            go.Scatter(
                x=monthly["Month"],
                y=monthly["Cumulative"],
                name="Cumulative",
                mode="lines+markers",
                line=dict(color="#38ef7d", width=3),
                yaxis="y2",
            )
        )
        fig.update_layout(
            **CHART_LAYOUT,
            height=300,
            yaxis=dict(title="Monthly", side="left"),
            yaxis2=dict(title="Cumulative", side="right", overlaying="y"),
            legend=dict(font=dict(color="white", size=10)),
            xaxis=dict(tickangle=-35),
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No date column found.")
    _close_container()

    _section_header("Program Impact Analysis")
    c1, c2 = st.columns(2)
    with c1:
        _chart_container("Donations by Program (Sunburst)")
        if cat_col in df.columns and sales_col in df.columns:
            pdata = df.groupby(cat_col)[sales_col].sum().reset_index()
            pdata.columns = ["Program", "Donations"]
            fig = px.sunburst(
                pdata,
                path=["Program"],
                values="Donations",
                color="Donations",
                color_continuous_scale=["#4338ca", "#667eea", "#a78bfa"],
                template="none",
            )
            fig.update_layout(
                **{k: v for k, v in CHART_LAYOUT.items() if k not in ("xaxis", "yaxis")}, height=300
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No program data found.")
        _close_container()

    with c2:
        _chart_container("Beneficiaries by Program (Bar)")
        if cat_col in df.columns and qty_col in df.columns:
            bdata = df.groupby(cat_col)[qty_col].sum().sort_values(ascending=False).reset_index()
            bdata.columns = ["Program", "Beneficiaries"]
            fig = px.bar(
                bdata,
                x="Program",
                y="Beneficiaries",
                color="Beneficiaries",
                color_continuous_scale=["#11998e", "#38ef7d"],
                template="none",
            )
            fig.update_coloraxes(showscale=False)
            fig.update_layout(**CHART_LAYOUT, height=300)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No beneficiary data found.")
        _close_container()

    if funding_col and funding_col in df.columns:
        _section_header("Funding Source Diversity")
        c3, c4 = st.columns(2)
        with c3:
            _chart_container("Funding Source Mix (Pie)")
            fdata = df.groupby(funding_col)[sales_col].sum().reset_index()
            fdata.columns = ["Source", "Donations"]
            fig = px.pie(
                fdata,
                names="Source",
                values="Donations",
                color_discrete_sequence=COLORS,
                hole=0.45,
                template="none",
            )
            fig.update_traces(
                textfont=dict(color="white", size=12),
                marker=dict(line=dict(color="rgba(0,0,0,0.3)", width=2)),
            )
            fig.update_layout(
                **{k: v for k, v in CHART_LAYOUT.items() if k not in ("xaxis", "yaxis")}, height=300
            )
            st.plotly_chart(fig, use_container_width=True)
            _close_container()
        with c4:
            _chart_container("Funding by Program (Stacked Bar)")
            if cat_col in df.columns and sales_col in df.columns:
                sdata = df.groupby([cat_col, funding_col])[sales_col].sum().reset_index()
                sdata.columns = ["Program", "Source", "Donations"]
                fig = px.bar(
                    sdata,
                    x="Program",
                    y="Donations",
                    color="Source",
                    color_discrete_sequence=COLORS,
                    template="none",
                    barmode="stack",
                )
                fig.update_layout(
                    **CHART_LAYOUT, height=300, legend=dict(font=dict(color="white", size=10))
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No funding data found.")
            _close_container()

    if region_col and sales_col in df.columns and qty_col in df.columns:
        _section_header("Regional Impact Analysis")
        _chart_container("Donations & Beneficiaries by Region (Bubble)")
        regional = (
            df.groupby(region_col)
            .agg(
                Donations=(sales_col, "sum"),
                Beneficiaries=(qty_col, "sum"),
            )
            .reset_index()
        )
        regional.columns = ["Region", "Donations", "Beneficiaries"]
        fig = px.scatter(
            regional,
            x="Donations",
            y="Beneficiaries",
            size="Donations",
            color="Region",
            color_discrete_sequence=COLORS,
            template="none",
            size_max=40,
            text="Region",
        )
        fig.update_traces(textposition="top center", textfont=dict(color="white", size=11))
        fig.update_layout(**CHART_LAYOUT, height=300, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
        _close_container()


# ──────────────────────────────────────────────
# Manufacturing Dashboard — Production & Utilization
# ──────────────────────────────────────────────
def render_manufacturing_dashboard(df: pd.DataFrame, kpis: dict):
    """Render manufacturing-specific analytics."""
    labels = {
        "revenue": "Total Production",
        "profit": "Net Yield Value",
        "orders": "Active Machines",
        "avg_order": "Utilization Rate",
        "performance": "Production Performance",
        "breakdown": "Machine & Downtime Breakdown",
        "deep_dive": "Yield & Output Analysis",
        "regional": "Regional Production Analysis",
        "category_label": "Machine Line",
        "product_label": "Top Machines",
        "region_label": "Plant",
    }

    from dashboard.charts import render_kpi_cards

    production_col = _safe_col(
        df, "production", "output_quantity", "units_produced", "quantity", "production_volume"
    )
    machine_col = _safe_col(df, "machine", "machine_id", "equipment", "equipment_id")
    downtime_col = _safe_col(df, "downtime", "downtime_hours", "stoppage_hours")
    status_col = _safe_col(df, "status", "machine_status", "operational_status")
    date_col = _safe_col(df, "date", "timestamp", "production_date", "recorded_date")

    total_production = float(df[production_col].sum()) if production_col else 0.0
    machine_count = int(df[machine_col].nunique()) if machine_col else 0

    utilization = 0.0
    if status_col and machine_col:
        up_states = {"running", "up", "operational", "active", "online", "1"}
        grouped = df.groupby(machine_col)
        util_values = []
        for _, group in grouped:
            up = group[status_col].astype(str).str.lower().isin(up_states).sum()
            total = len(group)
            if total:
                util_values.append(up / total * 100)
        utilization = sum(util_values) / len(util_values) if util_values else 0.0

    total_downtime = 0.0
    if downtime_col and pd.api.types.is_numeric_dtype(df[downtime_col]):
        total_downtime = float(df[downtime_col].sum())

    yield_rate = 0.0
    good_col = _safe_col(df, "good_units", "passed", "yield_quantity", "quality_passed")
    total_units_col = _safe_col(df, "total_units", "units_produced", "production")
    if good_col and total_units_col:
        total_units = df[total_units_col].sum()
        yield_rate = (df[good_col].sum() / total_units * 100) if total_units else 0.0
    elif production_col:
        yield_rate = 95.0

    _section_header("Manufacturing Operations")
    render_kpi_cards(
        total_production,
        total_production * 0.2,
        machine_count,
        utilization,
        yield_rate,
        labels=labels,
    )
    st.markdown("<br>", unsafe_allow_html=True)

    _section_header("Production Performance")
    c1, c2 = st.columns(2)
    with c1:
        _chart_container("Production Output Over Time")
        if date_col and production_col:
            pdata = df.groupby(df[date_col].astype(str).str[:10])[production_col].sum().reset_index()
            pdata.columns = ["Date", "Production"]
            fig = px.line(
                pdata,
                x="Date",
                y="Production",
                markers=True,
                template="none",
            )
            fig.update_layout(**CHART_LAYOUT, height=300)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No date/production data found.")
        _close_container()
    with c2:
        _chart_container("Production by Machine")
        if machine_col and production_col:
            mdata = df.groupby(machine_col)[production_col].sum().sort_values(ascending=False).reset_index()
            mdata.columns = ["Machine", "Production"]
            fig = px.bar(
                mdata,
                x="Machine",
                y="Production",
                color="Production",
                color_continuous_scale=["#667eea", "#764ba2"],
                template="none",
            )
            fig.update_coloraxes(showscale=False)
            fig.update_layout(**CHART_LAYOUT, height=300)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No machine data found.")
        _close_container()

    _section_header("Machine Utilization")
    if machine_col and status_col:
        up_states = {"running", "up", "operational", "active", "online", "1"}
        util = (
            df.groupby(machine_col)
            .apply(lambda g: g[status_col].astype(str).str.lower().isin(up_states).sum() / len(g) * 100)
            .reset_index(name="Utilization")
        )
        _chart_container("Utilization by Machine")
        fig = px.bar(
            util,
            x=machine_col,
            y="Utilization",
            color="Utilization",
            color_continuous_scale=["#f6ad55", "#ed8936"],
            template="none",
        )
        fig.update_coloraxes(showscale=False)
        fig.update_layout(**CHART_LAYOUT, height=300)
        st.plotly_chart(fig, use_container_width=True)
        _close_container()
    else:
        st.info("No status data found.")

    _section_header("Downtime Analysis")
    c3, c4 = st.columns(2)
    with c3:
        _chart_container("Downtime Hours")
        if downtime_col:
            ddata = pd.DataFrame({"Metric": ["Downtime Hours"], "Value": [total_downtime]})
            fig = px.bar(
                ddata,
                x="Metric",
                y="Value",
                color="Metric",
                color_discrete_sequence=["#e53e3e"],
                template="none",
            )
            fig.update_layout(**CHART_LAYOUT, height=300, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No downtime data found.")
        _close_container()
    with c4:
        _chart_container("Yield Rate")
        ydata = pd.DataFrame({"Metric": ["Yield Rate %"], "Value": [yield_rate]})
        fig = px.bar(
            ydata,
            x="Metric",
            y="Value",
            color="Metric",
            color_discrete_sequence=["#48bb78"],
            template="none",
        )
        fig.update_layout(**CHART_LAYOUT, height=300, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
        _close_container()


# ──────────────────────────────────────────────
# Agriculture Dashboard — Yield, Harvest & Livestock
# ──────────────────────────────────────────────
def render_agriculture_dashboard(df: pd.DataFrame, kpis: dict):
    """Render agriculture-specific analytics."""
    labels = {
        "revenue": "Total Harvest",
        "profit": "Harvest Value",
        "orders": "Farms",
        "avg_order": "Yield / Hectare",
        "performance": "Yield & Harvest Performance",
        "breakdown": "Farm & Crop Breakdown",
        "deep_dive": "Livestock & Weather Analysis",
        "regional": "Regional Agriculture Analysis",
        "category_label": "Crop Type",
        "product_label": "Top Crops",
        "region_label": "Region",
    }

    from dashboard.charts import render_kpi_cards

    farm_col = _safe_col(df, "farm", "farm_id", "farm_name", "field", "parcel")
    crop_col = _safe_col(df, "crop", "crop_id", "crop_name", "produce")
    harvest_col = _safe_col(df, "harvest", "yield", "yield_kg", "harvest_kg", "production")
    livestock_col = _safe_col(df, "livestock", "animal", "animal_type", "livestock_id")
    weather_col = _safe_col(df, "rainfall", "rainfall_mm", "precipitation", "precipitation_mm")
    temp_col = _safe_col(df, "temperature", "temperature_c", "temp")
    hectares_col = _safe_col(df, "hectares", "size_hectares", "area_hectares", "farm_size")
    date_col = _safe_col(df, "date", "harvest_date", "planting_date", "recorded_date")

    total_harvest = float(df[harvest_col].sum()) if harvest_col and pd.api.types.is_numeric_dtype(df[harvest_col]) else 0.0
    farm_count = int(df[farm_col].nunique()) if farm_col else 0
    yield_per_ha = 0.0
    if harvest_col and hectares_col:
        total_ha = df[hectares_col].sum()
        yield_per_ha = (total_harvest / total_ha) if total_ha else 0.0
    elif harvest_col and farm_count:
        yield_per_ha = total_harvest / farm_count

    avg_rainfall = float(df[weather_col].mean()) if weather_col and pd.api.types.is_numeric_dtype(df[weather_col]) else 0.0

    _section_header("Agriculture Overview")
    render_kpi_cards(
        total_harvest,
        total_harvest * 0.3,
        farm_count,
        yield_per_ha,
        avg_rainfall,
        labels=labels,
    )
    st.markdown("<br>", unsafe_allow_html=True)

    _section_header("Farm Yield Performance")
    c1, c2 = st.columns(2)
    with c1:
        _chart_container("Yield by Farm")
        if farm_col and harvest_col:
            ydata = df.groupby(farm_col)[harvest_col].sum().sort_values(ascending=False).reset_index()
            ydata.columns = ["Farm", "Harvest"]
            fig = px.bar(
                ydata,
                x="Farm",
                y="Harvest",
                color="Harvest",
                color_continuous_scale=["#38a169", "#276749"],
                template="none",
            )
            fig.update_coloraxes(showscale=False)
            fig.update_layout(**CHART_LAYOUT, height=300)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No farm yield data found.")
        _close_container()
    with c2:
        _chart_container("Harvest by Crop")
        if crop_col and harvest_col:
            cdata = df.groupby(crop_col)[harvest_col].sum().sort_values(ascending=False).reset_index()
            cdata.columns = ["Crop", "Harvest"]
            fig = px.pie(
                cdata,
                names="Crop",
                values="Harvest",
                color_discrete_sequence=COLORS,
                hole=0.45,
                template="none",
            )
            fig.update_layout(**{k: v for k, v in CHART_LAYOUT.items() if k not in ("xaxis", "yaxis")}, height=300)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No crop data found.")
        _close_container()

    _section_header("Livestock & Weather")
    c3, c4 = st.columns(2)
    with c3:
        _chart_container("Livestock Count by Type")
        if livestock_col:
            ldata = (
                df.groupby(livestock_col).size().reset_index(name="Count")
                if not pd.api.types.is_numeric_dtype(df[livestock_col])
                else df.groupby(livestock_col)[livestock_col].sum().reset_index(name="Count")
            )
            ldata.columns = ["Type", "Count"]
            fig = px.bar(
                ldata,
                x="Type",
                y="Count",
                color="Count",
                color_continuous_scale=["#ed8936", "#dd6b20"],
                template="none",
            )
            fig.update_coloraxes(showscale=False)
            fig.update_layout(**CHART_LAYOUT, height=300)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No livestock data found.")
        _close_container()
    with c4:
        _chart_container("Weather Trends")
        if date_col and (weather_col or temp_col):
            cols = {"Date": df[date_col].astype(str).str[:10]}
            if weather_col:
                cols["Rainfall"] = df[weather_col]
            if temp_col:
                cols["Temperature"] = df[temp_col]
            wdata = pd.DataFrame(cols).drop_duplicates()
            fig = px.line(
                wdata,
                x="Date",
                y=[c for c in wdata.columns if c != "Date"],
                markers=True,
                template="none",
            )
            fig.update_layout(**CHART_LAYOUT, height=300)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No weather data found.")
        _close_container()


# ──────────────────────────────────────────────
# Dispatcher
# ──────────────────────────────────────────────
SECTOR_RENDERERS = {
    "sme": render_sme_dashboard,
    "retail": render_sme_dashboard,
    "education": render_education_dashboard,
    "healthcare": render_healthcare_dashboard,
    "government": render_government_dashboard,
    "church": render_church_dashboard,
    "ngo": render_ngo_dashboard,
    "manufacturing": render_manufacturing_dashboard,
    "agriculture": render_agriculture_dashboard,
}


def render_generic_sector_dashboard(df: pd.DataFrame, kpis: dict):
    """Render a generic analytics dashboard for unknown/unclassified datasets.

    Shows dataset overview, statistical summary, and auto-detected charts
    without assuming any specific industry.
    """
    from dashboard.utils import fmt_number

    _section_header("Generic Analytics Dashboard")

    # Dataset overview cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        _kpi_card(fmt_number(len(df)), "Total Records", "📋", "kpi-purple")
    with col2:
        numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
        _kpi_card(str(len(numeric_cols)), "Numeric Columns", "🔢", "kpi-blue")
    with col3:
        text_cols = [c for c in df.columns if df[c].dtype == "object"]
        _kpi_card(str(len(text_cols)), "Text Columns", "📝", "kpi-green")
    with col4:
        date_cols = [c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])]
        _kpi_card(str(len(date_cols)), "Date Columns", "📅", "kpi-orange")

    # Statistical summary
    _section_header("Statistical Summary")
    if numeric_cols:
        st.dataframe(df[numeric_cols].describe(), use_container_width=True)
    else:
        st.info("No numeric columns found for statistical summary.")

    # Auto-detect chart-worthy columns
    _section_header("Data Visualizations")

    # Try to find a date column for time series
    date_col = _safe_col(df, "date", "order_date", "sale_date", "transaction_date", "timestamp")
    numeric_col = None
    if numeric_cols:
        # Pick the first numeric column that isn't an ID
        for col in numeric_cols:
            if not col.lower().endswith("_id") and not col.lower() == "id":
                numeric_col = col
                break
        if not numeric_col:
            numeric_col = numeric_cols[0]

    cat_col = _safe_col(df, "category", "type", "region", "department", "status", "class")

    col_a, col_b = st.columns(2)
    with col_a:
        _chart_container("Distribution")
        if numeric_col:
            fig = px.histogram(df, x=numeric_col, template="none", nbins=30)
            fig.update_layout(**CHART_LAYOUT, height=350)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No numeric column available for distribution chart.")
        _close_container()

    with col_b:
        _chart_container("Category Breakdown")
        if cat_col and numeric_col:
            grouped = df.groupby(cat_col)[numeric_col].sum().reset_index()
            fig = px.bar(grouped, x=cat_col, y=numeric_col, template="none")
            fig.update_layout(**CHART_LAYOUT, height=350)
            st.plotly_chart(fig, use_container_width=True)
        elif cat_col:
            counts = df[cat_col].value_counts().reset_index()
            counts.columns = [cat_col, "count"]
            fig = px.bar(counts, x=cat_col, y="count", template="none")
            fig.update_layout(**CHART_LAYOUT, height=350)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No category column found for breakdown.")
        _close_container()

    # Industry selection prompt
    st.markdown("---")
    st.info(
        "💡 **Industry not detected.** Select an industry pack from the sidebar "
        "to see sector-specific dashboards with tailored KPIs and charts, "
        "or continue with this generic analytics view."
    )


def render_sector_dashboard(df: pd.DataFrame, kpis: dict, pack_key: str | None = None):
    """Render the appropriate dashboard for the selected sector.

    Falls back to generic analytics dashboard if no pack is selected.
    Never silently defaults to a specific industry dashboard.
    """
    if not pack_key or pack_key == "unknown":
        render_generic_sector_dashboard(df, kpis)
        return
    renderer = SECTOR_RENDERERS.get(pack_key)
    if renderer is None:
        render_generic_sector_dashboard(df, kpis)
        return
    renderer(df, kpis)
