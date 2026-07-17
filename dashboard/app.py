"""DataFlow — Business Analytics Dashboard.

Main Streamlit application entry point.
Supports two data sources:
  1. Live database (MySQL/SQLite) — queries via DashboardDataService
  2. File upload (CSV/Excel) — processes uploaded files

Features:
  - Authentication with role-based access
  - Interactive filters (region, category, date range)
  - KPI cards, charts, and data table
  - Export filtered data to CSV
  - Caching for database queries
"""

import os
import sys
from contextlib import suppress

import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dashboard.auth import get_current_user, logout, require_auth
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
from dashboard.copilot import render_copilot_panel
from dashboard.styles import DARK_THEME_CSS
from dashboard.utils import MAX_UPLOAD_SIZE_BYTES, MAX_UPLOAD_SIZE_MB, sanitize_text
from services.dashboard_data_service import DashboardDataService

st.set_page_config(
    page_title="DataFlow - Business Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(f"<style>{DARK_THEME_CSS}</style>", unsafe_allow_html=True)


# ──────────────────────────────────────────────
# Authentication
# ──────────────────────────────────────────────
if not require_auth():
    st.stop()

user = get_current_user()


# ──────────────────────────────────────────────
# Cached data service
# ──────────────────────────────────────────────
@st.cache_resource
def get_data_service() -> DashboardDataService:
    """Create a cached DashboardDataService instance."""
    return DashboardDataService()


@st.cache_data(ttl=300)
def load_db_data(_service, region, category, date_from, date_to) -> pd.DataFrame:
    """Load data from the database with caching (5 min TTL)."""
    return _service.load_from_database(
        region=region, category=category, date_from=date_from, date_to=date_to
    )


@st.cache_data(ttl=300)
def get_db_kpis(_service, region, category, date_from, date_to) -> dict:
    """Get KPIs from the database with caching (5 min TTL)."""
    return _service.get_kpis_from_database(
        region=region, category=category, date_from=date_from, date_to=date_to
    )


@st.cache_data(ttl=600)
def get_db_filter_options(_service) -> dict:
    """Get filter options from the database with caching (10 min TTL)."""
    return _service.get_filter_options()


@st.cache_data(ttl=600)
def get_db_record_count(_service) -> int:
    """Get total record count from the database."""
    return _service.get_record_count()


# ──────────────────────────────────────────────
# Sidebar
# ──────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sidebar-logo">Data<span>Flow</span></div>', unsafe_allow_html=True)

    st.markdown(
        f"""
    <div style="color:rgba(255,255,255,0.5);font-size:0.8rem;margin-bottom:12px;">
        👤 {sanitize_text(user.get('name', ''))} <span style="color:#a78bfa;">({sanitize_text(user.get('role', ''))})</span>
    </div>
    """,
        unsafe_allow_html=True,
    )
    if st.button("Logout", use_container_width=True):
        logout()

    st.markdown("---")

    st.markdown('<div class="sidebar-section">Data Source</div>', unsafe_allow_html=True)
    service = get_data_service()
    db_count = 0
    with suppress(Exception):
        db_count = get_db_record_count(service)

    data_source = st.radio(
        "Choose data source",
        ["Live Database", "Upload File"],
        help=f"Database has {db_count:,} records" if db_count > 0 else "Database not available",
    )

    if data_source == "Upload File":
        st.markdown('<div class="sidebar-section">Upload Dataset</div>', unsafe_allow_html=True)
        uploaded_file = st.file_uploader(
            f"Drop your CSV or Excel file here (max {MAX_UPLOAD_SIZE_MB}MB)",
            type=["csv", "xlsx", "xls"],
            help="Supports CSV and Excel. Columns are auto-detected.",
        )
    else:
        uploaded_file = None

    st.markdown("---")
    st.markdown(
        """
    <div style="color:rgba(255,255,255,0.3);font-size:0.75rem;line-height:1.8;">
        <strong style="color:rgba(255,255,255,0.5);">How it works</strong><br>
        1. Choose data source<br>
        2. Apply filters<br>
        3. Explore charts<br>
        4. Download your report
    </div>
    """,
        unsafe_allow_html=True,
    )


# ──────────────────────────────────────────────
# Hero
# ──────────────────────────────────────────────
st.markdown(
    """
<div class="hero-header">
    <div class="hero-badge">Business Intelligence Platform</div>
    <h1 class="hero-title">Turn your data into<br>clear business insights</h1>
    <p class="hero-subtitle">Interactive reports, trend charts, and key metrics.<br>
    Query your live database or upload a file for ad-hoc analysis.</p>
</div>
""",
    unsafe_allow_html=True,
)


# ──────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────
df = None

if data_source == "Live Database":
    if db_count == 0:
        st.markdown(
            """
        <div class="empty-state">
            <div class="empty-state-icon">🗄️</div>
            <div class="empty-state-title">Database is empty</div>
            <div class="empty-state-desc">
                Run the ETL pipeline to populate the database with data.<br>
                <code>python pipeline/run_pipeline.py</code>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )
        st.stop()

    filter_opts = get_db_filter_options(service)

    with st.sidebar:
        st.markdown('<div class="sidebar-section">Filters</div>', unsafe_allow_html=True)
        regions = filter_opts.get("regions", [])
        categories = filter_opts.get("categories", [])
        date_range = filter_opts.get("date_range", (None, None))

        sel_region = None
        sel_category = None
        date_from = None
        date_to = None

        if regions:
            opts = ["All Regions"] + regions
            sel = st.selectbox("Region", opts)
            if sel != "All Regions":
                sel_region = sel

        if categories:
            opts2 = ["All Categories"] + categories
            sel2 = st.selectbox("Category", opts2)
            if sel2 != "All Categories":
                sel_category = sel2

        if date_range and date_range[0] and date_range[1]:
            mn = pd.Timestamp(date_range[0]).date()
            mx = pd.Timestamp(date_range[1]).date()
            dr = st.date_input("Date Range", value=(mn, mx))
            if len(dr) == 2:
                date_from = dr[0]
                date_to = dr[1]

        st.markdown('<div class="sidebar-section">Export</div>', unsafe_allow_html=True)

    df = load_db_data(service, sel_region, sel_category, date_from, date_to)
    kpis = get_db_kpis(service, sel_region, sel_category, date_from, date_to)

    if df is not None and not df.empty:
        with st.sidebar:
            st.download_button(
                "Download Filtered Data",
                df.to_csv(index=False).encode("utf-8"),
                "dataflow_export.csv",
                "text/csv",
                use_container_width=True,
            )

    st.markdown(
        f"""
    <div class="info-banner">
        📡 Connected to live database. {len(df):,} records matching current filters.
    </div>
    """,
        unsafe_allow_html=True,
    )

else:
    # File upload mode
    if not uploaded_file:
        st.markdown(
            """
        <div class="empty-state">
            <div class="empty-state-icon">📂</div>
            <div class="empty-state-title">No dataset loaded yet</div>
            <div class="empty-state-desc">
                Upload a CSV or Excel file using the panel on the left to get started.
                The system will automatically detect your columns and build your dashboard instantly.<br><br>
                Works with sales data, financial records, inventory reports, and more.
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )
        st.stop()

    # File size validation
    uploaded_file.seek(0, 2)
    file_size = uploaded_file.tell()
    uploaded_file.seek(0)
    if file_size > MAX_UPLOAD_SIZE_BYTES:
        st.markdown(
            f'<div class="warning-banner">File too large. Maximum size is {MAX_UPLOAD_SIZE_MB}MB. '
            f"Your file is {file_size / 1024 / 1024:.1f}MB.</div>",
            unsafe_allow_html=True,
        )
        st.stop()

    try:
        with st.spinner("Reading your file..."):
            if uploaded_file.name.endswith(".csv"):
                try:
                    raw_df = pd.read_csv(uploaded_file, encoding="utf-8")
                except UnicodeDecodeError:
                    raw_df = pd.read_csv(uploaded_file, encoding="latin-1")
            else:
                raw_df = pd.read_excel(uploaded_file)
    except Exception as e:
        st.markdown(
            f'<div class="warning-banner">Could not read the file: {sanitize_text(str(e))}. '
            "Please check the format and try again.</div>",
            unsafe_allow_html=True,
        )
        st.stop()

    col_map = DashboardDataService.detect_columns(raw_df)

    if "sales" not in col_map:
        st.markdown(
            '<div class="warning-banner">Could not find a sales or revenue column. '
            "Make sure your file has a column with sales, revenue, or amount data.</div>",
            unsafe_allow_html=True,
        )
        with st.expander("Detected columns in your file"):
            st.write(list(raw_df.columns))
        st.stop()

    with st.spinner("Processing your data..."):
        df = DashboardDataService.clean_df(raw_df, col_map)

    dupes_removed = len(raw_df) - len(df)
    st.markdown(
        f"""
    <div class="success-banner">
        Dataset loaded successfully. {len(df):,} records ready to explore.
        <span class="stat-pill"><strong>{dupes_removed}</strong> duplicates removed</span>
        <span class="stat-pill"><strong>{len(df.columns)}</strong> columns detected</span>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # File mode filters
    with st.sidebar:
        st.markdown('<div class="sidebar-section">Filters</div>', unsafe_allow_html=True)
        if "region" in df.columns:
            opts = ["All Regions"] + sorted(df["region"].dropna().unique().tolist())
            sel = st.selectbox("Region", opts)
            if sel != "All Regions":
                df = df[df["region"] == sel]

        if "category" in df.columns:
            opts2 = ["All Categories"] + sorted(df["category"].dropna().unique().tolist())
            sel2 = st.selectbox("Category", opts2)
            if sel2 != "All Categories":
                df = df[df["category"] == sel2]

        if "order_date" in df.columns and df["order_date"].notna().any():
            mn = df["order_date"].min().date()
            mx = df["order_date"].max().date()
            dr = st.date_input("Date Range", value=(mn, mx))
            if len(dr) == 2:
                df = df[(df["order_date"].dt.date >= dr[0]) & (df["order_date"].dt.date <= dr[1])]

        st.markdown('<div class="sidebar-section">Export</div>', unsafe_allow_html=True)
        st.download_button(
            "Download Filtered Data",
            df.to_csv(index=False).encode("utf-8"),
            "dataflow_export.csv",
            "text/csv",
            use_container_width=True,
        )

    # Compute KPIs from filtered DataFrame
    total_sales = df["sales"].sum() if "sales" in df.columns else 0
    total_profit = df["profit"].sum() if "profit" in df.columns else 0
    total_orders = df["order_id"].nunique() if "order_id" in df.columns else len(df)
    avg_order = df["sales"].mean() if "sales" in df.columns else 0
    margin_pct = (total_profit / total_sales * 100) if total_sales > 0 else 0
    kpis = {
        "total_sales": total_sales,
        "total_profit": total_profit,
        "total_orders": total_orders,
        "avg_order_value": avg_order,
        "margin_pct": margin_pct,
    }


# ──────────────────────────────────────────────
# KPIs
# ──────────────────────────────────────────────
render_kpi_cards(
    kpis["total_sales"],
    kpis["total_profit"],
    kpis["total_orders"],
    kpis["avg_order_value"],
    kpis["margin_pct"],
)

st.markdown("<br>", unsafe_allow_html=True)


# ──────────────────────────────────────────────
# Charts
# ──────────────────────────────────────────────
st.markdown(
    '<div class="section-header">Sales Performance</div><hr class="section-divider">',
    unsafe_allow_html=True,
)
c1, c2 = st.columns(2)
with c1:
    render_revenue_over_time(df)
with c2:
    render_revenue_by_category(df)

st.markdown(
    '<div class="section-header">Profit and Regional Breakdown</div><hr class="section-divider">',
    unsafe_allow_html=True,
)
c3, c4 = st.columns(2)
with c3:
    render_profit_by_region(df)
with c4:
    render_top_products(df)

if "profit" in df.columns and "sales" in df.columns and "category" in df.columns:
    st.markdown(
        '<div class="section-header">Deep Dive Analysis</div><hr class="section-divider">',
        unsafe_allow_html=True,
    )
    c5, c6 = st.columns([3, 2])
    with c5:
        render_sales_vs_profit_scatter(df)
    with c6:
        render_profit_margin_by_category(df)

if "region" in df.columns and "category" in df.columns and "sales" in df.columns:
    st.markdown(
        '<div class="section-header">Regional Analysis</div><hr class="section-divider">',
        unsafe_allow_html=True,
    )
    render_heatmap_sales_region_category(df)


# ──────────────────────────────────────────────
# Data Table
# ──────────────────────────────────────────────
st.markdown(
    '<div class="section-header">Data Preview</div><hr class="section-divider">',
    unsafe_allow_html=True,
)
display_cols = [
    c
    for c in [
        "order_id",
        "order_date",
        "customer_name",
        "region",
        "category",
        "product_name",
        "sales",
        "profit",
        "quantity",
    ]
    if c in df.columns
]
st.dataframe(
    df[display_cols].head(200) if display_cols else df.head(200),
    use_container_width=True,
    height=320,
)
st.markdown(
    f'<div style="color:rgba(255,255,255,0.35);font-size:0.78rem;margin-top:8px;text-align:right;">'
    f"Showing up to 200 of {len(df):,} records. "
    "Use the Download button in the sidebar to export the full dataset.</div>",
    unsafe_allow_html=True,
)


# ──────────────────────────────────────────────
# AI Copilot
# ──────────────────────────────────────────────
st.markdown(
    '<div class="section-header">AI Copilot</div><hr class="section-divider">',
    unsafe_allow_html=True,
)
render_copilot_panel()
