"""Chart components for the dashboard.

Extracted from app.py for maintainability. Each function renders
a specific chart inside a styled container.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from dashboard.styles import CHART_LAYOUT, COLORS


def _chart_container(title: str):
    """Render the opening HTML for a chart container.

    Args:
        title: Title to display above the chart.
    """
    st.markdown(
        f'<div class="chart-container"><div class="chart-title">{title}</div>',
        unsafe_allow_html=True,
    )


def _close_container():
    """Render the closing HTML for a chart container."""
    st.markdown("</div>", unsafe_allow_html=True)


def render_revenue_over_time(df: pd.DataFrame, labels: dict | None = None):
    """Render an area chart showing revenue over time.

    Args:
        df: Filtered DataFrame with 'order_date' and 'sales' columns.
    """
    lbl = labels or {}
    revenue_word = lbl.get("revenue", "Revenue")
    _chart_container(f"{revenue_word} Over Time")
    if "order_date" in df.columns and df["order_date"].notna().any():
        df = df.copy()
        df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
        trend = (
            df.dropna(subset=["order_date"])
            .groupby(df["order_date"].dt.to_period("M").astype(str))["sales"]
            .sum()
            .reset_index()
        )
        trend.columns = ["Month", revenue_word]
        fig = px.area(
            trend, x="Month", y=revenue_word, color_discrete_sequence=["#667eea"], template="none"
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


def render_revenue_by_category(df: pd.DataFrame, labels: dict | None = None):
    """Render a horizontal bar chart of revenue by category.

    Args:
        df: Filtered DataFrame with 'category' and 'sales' columns.
    """
    lbl = labels or {}
    revenue_word = lbl.get("revenue", "Revenue")
    cat_word = lbl.get("category_label", "Category")
    _chart_container(f"{revenue_word} by {cat_word}")
    if "category" in df.columns:
        cat_data = df.groupby("category")["sales"].sum().sort_values(ascending=True).reset_index()
        cat_data.columns = [cat_word, revenue_word]
        fig = px.bar(
            cat_data,
            x=revenue_word,
            y=cat_word,
            orientation="h",
            color=revenue_word,
            color_continuous_scale=["#4338ca", "#667eea", "#a78bfa"],
            template="none",
        )
        fig.update_coloraxes(showscale=False)
        fig.update_layout(**CHART_LAYOUT, height=280)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No category column found.")
    _close_container()


def render_profit_by_region(df: pd.DataFrame, labels: dict | None = None):
    """Render a donut pie chart of profit by region.

    Args:
        df: Filtered DataFrame with 'region' and 'profit' columns.
    """
    lbl = labels or {}
    profit_word = lbl.get("profit", "Profit")
    _chart_container(f"{profit_word} by Region")
    if "region" in df.columns and "profit" in df.columns:
        reg = df.groupby("region")["profit"].sum().reset_index()
        reg.columns = ["Region", profit_word]
        fig = px.pie(
            reg,
            names="Region",
            values=profit_word,
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
        st.info("No region or profit column found.")
    _close_container()


def render_top_products(df: pd.DataFrame, n: int = 10, labels: dict | None = None):
    """Render a horizontal bar chart of top N products by revenue.

    Args:
        df: Filtered DataFrame with 'product_name' and 'sales' columns.
        n: Number of top products to show.
    """
    lbl = labels or {}
    product_word = lbl.get("product_label", "Products")
    revenue_word = lbl.get("revenue", "Revenue")
    _chart_container(f"Top {n} {product_word} by {revenue_word}")
    if "product_name" in df.columns:
        top = (
            df.groupby("product_name")["sales"]
            .sum()
            .sort_values(ascending=False)
            .head(n)
            .reset_index()
        )
        top.columns = ["Product", revenue_word]
        top["Label"] = top["Product"].str[:30] + "..."
        fig = px.bar(
            top,
            x=revenue_word,
            y="Label",
            orientation="h",
            color=revenue_word,
            color_continuous_scale=["#11998e", "#38ef7d"],
            template="none",
        )
        fig.update_coloraxes(showscale=False)
        fig.update_layout(
            **{
                **CHART_LAYOUT,
                "yaxis": dict(
                    autorange="reversed",
                    gridcolor="rgba(255,255,255,0.05)",
                    tickfont=dict(color="rgba(255,255,255,0.6)", size=10),
                ),
            },
            height=300,
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No product column found.")
    _close_container()


def render_sales_vs_profit_scatter(df: pd.DataFrame, labels: dict | None = None):
    """Render a scatter plot of sales vs profit, colored by category.

    Args:
        df: Filtered DataFrame with 'sales', 'profit', and 'category' columns.
    """
    lbl = labels or {}
    revenue_word = lbl.get("revenue", "Revenue")
    profit_word = lbl.get("profit", "Profit")
    cat_word = lbl.get("category_label", "Category")
    _chart_container(f"{revenue_word} vs {profit_word} by {cat_word}")
    if "profit" in df.columns and "sales" in df.columns:
        samp = df.dropna(subset=["sales", "profit"]).sample(min(500, len(df)), random_state=42)
        fig = px.scatter(
            samp,
            x="sales",
            y="profit",
            color="category" if "category" in samp.columns else None,
            color_discrete_sequence=COLORS,
            opacity=0.65,
            template="none",
        )
        fig.update_layout(**CHART_LAYOUT, height=280)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No sales or profit column found.")
    _close_container()


def render_profit_margin_by_category(df: pd.DataFrame, labels: dict | None = None):
    """Render a bar chart of profit margin percentage by category.

    Args:
        df: Filtered DataFrame with 'sales', 'profit', and 'category' columns.
    """
    lbl = labels or {}
    profit_word = lbl.get("profit", "Profit Margin")
    cat_word = lbl.get("category_label", "Category")
    _chart_container(f"{profit_word} by {cat_word}")
    if "profit" in df.columns and "sales" in df.columns and "category" in df.columns:
        mdata = (
            df.groupby("category")
            .agg(sales=("sales", "sum"), profit=("profit", "sum"))
            .reset_index()
        )
        mdata["Margin"] = (mdata["profit"] / mdata["sales"] * 100).round(1)
        fig = px.bar(
            mdata,
            x="category",
            y="Margin",
            color="Margin",
            color_continuous_scale=["#f5576c", "#ffd200", "#38ef7d"],
            template="none",
            text="Margin",
        )
        fig.update_traces(
            texttemplate="%{text:.1f}%", textposition="outside", textfont=dict(color="white")
        )
        fig.update_coloraxes(showscale=False)
        fig.update_layout(**CHART_LAYOUT, height=280)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No category, sales, or profit column found.")
    _close_container()


def render_heatmap_sales_region_category(df: pd.DataFrame, labels: dict | None = None):
    """Render a heatmap of sales by region and category.

    Args:
        df: Filtered DataFrame with 'region', 'category', and 'sales' columns.
    """
    lbl = labels or {}
    revenue_word = lbl.get("revenue", "Revenue")
    cat_word = lbl.get("category_label", "Category")
    _chart_container(f"{revenue_word} Heatmap: Region x {cat_word}")
    if "region" in df.columns and "category" in df.columns and "sales" in df.columns:
        pivot = df.groupby(["region", "category"])["sales"].sum().reset_index()
        fig = go.Figure(
            data=go.Heatmap(
                z=pivot["sales"],
                x=pivot["category"],
                y=pivot["region"],
                colorscale=[[0, "#1a1a4e"], [0.5, "#667eea"], [1, "#f093fb"]],
                text=pivot["sales"].round(0),
                texttemplate="$%{text:,.0f}",
                textfont=dict(color="white", size=10),
            )
        )
        layout = {k: v for k, v in CHART_LAYOUT.items() if k not in ("xaxis", "yaxis")}
        fig.update_layout(**layout, height=300)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No region, category, or sales column found.")
    _close_container()


def render_kpi_cards(
    total_sales: float,
    total_profit: float,
    total_orders: int,
    avg_order: float,
    margin_pct: float,
    labels: dict | None = None,
):
    """Render the 4 KPI cards.

    Args:
        total_sales: Total revenue.
        total_profit: Total profit.
        total_orders: Number of unique orders.
        avg_order: Average order value.
        margin_pct: Profit margin percentage.
    """
    from dashboard.utils import fmt_currency, fmt_number

    lbl = labels or {}
    revenue_label = lbl.get("revenue", "Total Revenue")
    profit_label = lbl.get("profit", "Profit")
    orders_label = lbl.get("orders", "Total Orders")
    avg_label = lbl.get("avg_order", "Avg Order Value")

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(
            f'<div class="kpi-card kpi-card-sales"><span class="kpi-icon">💰</span>'
            f'<div class="kpi-value">{fmt_currency(total_sales)}</div>'
            f'<div class="kpi-label">{revenue_label}</div></div>',
            unsafe_allow_html=True,
        )
    with k2:
        st.markdown(
            f'<div class="kpi-card kpi-card-profit"><span class="kpi-icon">📈</span>'
            f'<div class="kpi-value">{fmt_currency(total_profit)}</div>'
            f'<div class="kpi-label">{profit_label} ({margin_pct:.1f}% margin)</div></div>',
            unsafe_allow_html=True,
        )
    with k3:
        st.markdown(
            f'<div class="kpi-card kpi-card-orders"><span class="kpi-icon">🛒</span>'
            f'<div class="kpi-value">{fmt_number(total_orders)}</div>'
            f'<div class="kpi-label">{orders_label}</div></div>',
            unsafe_allow_html=True,
        )
    with k4:
        st.markdown(
            f'<div class="kpi-card kpi-card-avg"><span class="kpi-icon">✨</span>'
            f'<div class="kpi-value">{fmt_currency(avg_order)}</div>'
            f'<div class="kpi-label">{avg_label}</div></div>',
            unsafe_allow_html=True,
        )
