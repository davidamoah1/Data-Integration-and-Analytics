"""DataFlow â€” Business Analytics Dashboard.

Main Streamlit application entry point.
Supports two data sources:
  1. Live database (MySQL/SQLite) â€” queries via DashboardDataService
  2. File upload (CSV/Excel) â€” processes uploaded files

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
from dashboard.copilot import render_copilot_panel
from dashboard.onboarding import (
    get_industry_labels,
    render_industry_pack_selector,
    render_onboarding,
    render_quick_start_checklist,
)
from dashboard.pwa import register_pwa
from dashboard.sector_dashboards import render_sector_dashboard
from dashboard.semantic_dashboard import render_semantic_dashboard
from dashboard.styles import DARK_THEME_CSS, RESPONSIVE_CSS
from dashboard.utils import MAX_UPLOAD_SIZE_BYTES, MAX_UPLOAD_SIZE_MB, sanitize_text
from dashboard.validation_dashboard import render_approval_section, render_validation_dashboard
from semantic.mapping_engine import SemanticMappingEngine, SemanticMappingResult
from services.dashboard_data_service import DashboardDataService
from validation.engine import ValidationEngine

st.set_page_config(
    page_title="DataFlow - Business Analytics",
    page_icon="ðŸ“Š",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(f"<style>{DARK_THEME_CSS}\n{RESPONSIVE_CSS}</style>", unsafe_allow_html=True)
register_pwa()


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Authentication
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
if not require_auth():
    st.stop()

user = get_current_user()


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Onboarding (first-time users)
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
render_onboarding()


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Cached data service
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Sidebar
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
with st.sidebar:
    st.markdown('<div class="sidebar-logo">Data<span>Flow</span></div>', unsafe_allow_html=True)

    st.markdown(
        f"""
    <div style="color:rgba(255,255,255,0.5);font-size:0.8rem;margin-bottom:12px;">
        ðŸ‘¤ {sanitize_text(user.get('name', ''))} <span style="color:#a78bfa;">({sanitize_text(user.get('role', ''))})</span>
    </div>
    """,
        unsafe_allow_html=True,
    )
    if st.button("Logout", use_container_width=True):
        st.session_state["show_logout_confirm"] = True

    if st.session_state.get("show_logout_confirm"):
        st.warning("Log out of DataFlow? You'll need to sign in again to access your dashboards.")
        col_y, col_n = st.columns(2)
        with col_y:
            if st.button("Yes, log out", use_container_width=True, type="primary"):
                logout()
        with col_n:
            if st.button("Cancel", use_container_width=True):
                st.session_state["show_logout_confirm"] = False
                st.rerun()

    st.markdown("---")

    render_quick_start_checklist()
    render_industry_pack_selector()

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

    st.markdown("---")
    st.markdown('<div class="sidebar-section">Navigation</div>', unsafe_allow_html=True)
    page = st.radio(
        "Page",
        ["Dashboard", "Administration", "Support", "Observability"],
        key="nav_page",
        label_visibility="collapsed",
    )


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Industry labels (from selected pack)
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
labels = get_industry_labels()

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Page routing
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
_current_page = st.session_state.get("nav_page", "Dashboard")

if _current_page == "Administration":
    from dashboard.admin import render_admin_page

    render_admin_page()
    st.stop()

elif _current_page == "Support":
    from dashboard.support import render_support_page

    render_support_page()
    st.stop()

elif _current_page == "Observability":
    from dashboard.observability import render_observability_page

    render_observability_page()
    st.stop()


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Hero
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
st.markdown(
    """
<div class="hero-header">
    <div class="hero-badge">Enterprise Data Intelligence</div>
    <h1 class="hero-title">Turn your data into<br>clear business insights</h1>
    <p class="hero-subtitle">Upload a dataset and the platform detects your industry,<br>
    maps business entities, and generates governed KPIs and dashboards automatically.</p>
</div>
""",
    unsafe_allow_html=True,
)


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Load data
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
df = None
semantic_mapping_result = None

if data_source == "Live Database":
    if db_count == 0:
        st.markdown(
            """
        <div class="empty-state">
            <div class="empty-state-icon">ðŸ—„ï¸</div>
            <div class="empty-state-title">Database is empty</div>
            <div class="empty-state-desc">
                No data has been loaded into the database yet. You can:<br><br>
                <strong>Option 1:</strong> Upload a CSV or Excel file using <strong>Upload File</strong> mode in the sidebar<br><br>
                <strong>Option 2:</strong> Connect a data source via the Dataset Library API<br>
                <code>POST /datasets/production/database</code><br><br>
                <strong>Option 3:</strong> Run an ETL pipeline to load data from an external source
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
    st.session_state.pop("semantic_dataset_context", None)

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
        ðŸ“¡ Connected to live database. {len(df):,} records matching current filters.
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
            <div class="empty-state-icon">ðŸ“‚</div>
            <div class="empty-state-title">No dataset loaded yet</div>
            <div class="empty-state-desc">
                Upload a CSV or Excel file using the panel on the left to get started.<br>
                The system will automatically detect your columns and build your dashboard instantly.<br><br>
                <strong>Supported formats:</strong> .csv, .xlsx, .xls<br>
                <strong>Max file size:</strong> 50 MB<br>
                <strong>Auto-detected concepts:</strong> revenue, cost, date, region, category, product, customer, enrollment, patient, project, and more.<br><br>
                Works with business, financial, operational, educational, healthcare, government, and NGO data.
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
            # Clear all previous session state related to prior uploads
            # This ensures complete dataset isolation â€” no old metadata reuse
            for key in (
                "semantic_dataset_context",
                "admin_confirmed_industry",
                "admin_overridden_industry",
                "validation_result",
                "validation_filename",
                "copilot_messages",
                "copilot_conversation_id",
                "active_industry_pack",
                "dataset_id",
                "dataset_metadata",
                "dataset_analysis_history",
            ):
                st.session_state.pop(key, None)

            # Generate unique dataset ID for this upload
            import uuid as _uuid

            dataset_id = str(_uuid.uuid4())
            st.session_state["dataset_id"] = dataset_id

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

    # â”€â”€ Hospital Data Validation (mandatory pre-ETL stage) â”€â”€
    if (
        "validation_result" not in st.session_state
        or st.session_state.get("validation_filename") != uploaded_file.name
    ):
        with st.spinner("Running hospital data validation..."):
            validation_engine = ValidationEngine()
            validation_result = validation_engine.validate(raw_df, dataset_name=uploaded_file.name)
            st.session_state["validation_result"] = validation_result
            st.session_state["validation_filename"] = uploaded_file.name

    validation_result = st.session_state["validation_result"]

    # Render validation dashboard
    render_validation_dashboard(validation_result)

    # Approval workflow â€” block ETL if validation failed
    if not validation_result.can_proceed_to_etl:
        approved = render_approval_section(validation_result)
        if not approved:
            st.stop()

    st.markdown("---")

    with st.spinner("Discovering business meaning in your data..."):
        semantic_mapping_result = SemanticMappingEngine.analyze(raw_df, uploaded_file.name)
        df = raw_df.copy()

    from datetime import datetime as _dt

    st.session_state["semantic_dataset_context"] = {
        "dataset_id": st.session_state.get("dataset_id"),
        "filename": uploaded_file.name,
        "upload_timestamp": _dt.now().isoformat(),
        "record_count": len(df),
        "column_count": len(df.columns),
        "industry": semantic_mapping_result.industry,
        "industry_confidence": semantic_mapping_result.industry_confidence,
        "business_entities": semantic_mapping_result.business_entities,
        "column_mappings": semantic_mapping_result.semantic_result.to_dict()["mappings"],
        "kpi_definitions": semantic_mapping_result.kpi_definitions,
        "business_rules": semantic_mapping_result.recommendations,
    }
    st.session_state["dataset_metadata"] = st.session_state["semantic_dataset_context"]

    # Admin confirmation for low-confidence industry detection
    # Below 70%: "Industry detection uncertain. Please confirm."
    # 70%-85%: Show recommendation, require confirmation
    # Above 85%: Auto-select (no confirmation needed)
    confidence_threshold = 85.0
    uncertainty_threshold = 70.0
    if (
        semantic_mapping_result.industry_confidence < confidence_threshold
        or semantic_mapping_result.industry == "unknown"
    ):
        from semantic.entity_library import get_all_industries

        available_industries = get_all_industries()

        if semantic_mapping_result.industry_confidence < uncertainty_threshold:
            st.warning(
                f"âš ï¸ **Industry detection uncertain.** "
                f"Best guess: **{semantic_mapping_result.industry.title()}** "
                f"({semantic_mapping_result.industry_confidence:.0f}% confidence). "
                f"Please confirm the correct industry below."
            )
        else:
            st.info(
                f"Detected industry: **{semantic_mapping_result.industry.title()}** "
                f"({semantic_mapping_result.industry_confidence:.0f}% confidence). "
                f"Confidence is below the {confidence_threshold:.0f}% threshold. "
                f"Please confirm or select the correct industry below."
            )
        selected_industry = st.selectbox(
            "Select Industry",
            options=["unknown"] + available_industries,
            index=(
                0
                if semantic_mapping_result.industry == "unknown"
                else (
                    available_industries.index(semantic_mapping_result.industry) + 1
                    if semantic_mapping_result.industry in available_industries
                    else 0
                )
            ),
            format_func=lambda x: x.title(),
        )
        if st.button("Confirm Industry", type="primary"):
            if (
                selected_industry != "unknown"
                and selected_industry != semantic_mapping_result.industry
            ):
                # Override the industry
                semantic_mapping_result = SemanticMappingResult(
                    table_metadata=semantic_mapping_result.table_metadata,
                    data_profile=semantic_mapping_result.data_profile,
                    semantic_result=semantic_mapping_result.semantic_result,
                    relationship_result=semantic_mapping_result.relationship_result,
                    industry=selected_industry,
                    industry_confidence=100.0,
                    business_entities=semantic_mapping_result.business_entities,
                    business_concepts=semantic_mapping_result.business_concepts,
                    kpi_definitions=semantic_mapping_result.kpi_definitions,
                    alerts=semantic_mapping_result.alerts,
                    ai_prompts=semantic_mapping_result.ai_prompts,
                    recommendations=semantic_mapping_result.recommendations,
                    overrides=semantic_mapping_result.overrides,
                )
                st.session_state["semantic_dataset_context"]["industry"] = selected_industry
                st.session_state["semantic_dataset_context"]["industry_confidence"] = 100.0
            st.session_state["admin_confirmed_industry"] = True
            st.rerun()

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

    # File mode filters â€” auto-detect filterable columns
    with st.sidebar:
        st.markdown('<div class="sidebar-section">Filters</div>', unsafe_allow_html=True)

        # Auto-detect categorical columns for filtering (max 3 filters)
        categorical_candidates = []
        for col in df.columns:
            if df[col].dtype == "object" and df[col].nunique() < 50 and df[col].notna().any():
                categorical_candidates.append(col)
        categorical_candidates = sorted(categorical_candidates[:3])

        for col_name in categorical_candidates:
            opts = [f"All {col_name.title()}"] + sorted(df[col_name].dropna().unique().tolist())
            sel = st.selectbox(col_name.title(), opts)
            if sel != f"All {col_name.title()}":
                df = df[df[col_name] == sel]

        # Auto-detect date columns for date range filter
        date_col = None
        for candidate in (
            "order_date",
            "sale_date",
            "transaction_date",
            "admission_date",
            "visit_date",
            "enrollment_date",
            "date",
            "timestamp",
        ):
            if candidate in df.columns and df[candidate].notna().any():
                date_col = candidate
                break
        if date_col:
            try:
                df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
                mn = df[date_col].min().date()
                mx = df[date_col].max().date()
                dr = st.date_input("Date Range", value=(mn, mx))
                if len(dr) == 2:
                    df = df[(df[date_col].dt.date >= dr[0]) & (df[date_col].dt.date <= dr[1])]
            except Exception:
                pass

        st.markdown('<div class="sidebar-section">Export</div>', unsafe_allow_html=True)
        st.download_button(
            "Download Filtered Data",
            df.to_csv(index=False).encode("utf-8"),
            "dataflow_export.csv",
            "text/csv",
            use_container_width=True,
        )

    kpis = {}


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Sector Dashboard (KPIs + Charts)
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
if semantic_mapping_result is not None:
    admin_confirmed = st.session_state.get("admin_confirmed_industry", False)
    render_semantic_dashboard(df, semantic_mapping_result, admin_confirmed=admin_confirmed)
else:
    pack_key = st.session_state.get("active_industry_pack")
    render_sector_dashboard(df, kpis, pack_key=pack_key)


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Data Table
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
st.markdown(
    '<div class="section-header">Data Preview</div><hr class="section-divider">',
    unsafe_allow_html=True,
)
if semantic_mapping_result is not None:
    mapped_cols = []
    for mapping in semantic_mapping_result.semantic_result.mappings:
        if mapping.column_name in df.columns:
            mapped_cols.append(mapping.column_name)
    remaining = [c for c in df.columns if c not in mapped_cols]
    for c in remaining:
        if len(mapped_cols) >= 12:
            break
        mapped_cols.append(c)
    display_cols = mapped_cols[:12]
else:
    display_cols = list(df.columns)[:12]

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


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# AI Copilot
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
st.markdown(
    '<div class="section-header">AI Copilot</div><hr class="section-divider">',
    unsafe_allow_html=True,
)
render_copilot_panel()


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Footer
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
st.markdown(
    """
    <div class="app-footer">
        DataFlow v2.0.0 &mdash; Enterprise Data Intelligence Platform<br>
        <a href="/docs" target="_blank">API Docs</a> &bull;
        <a href="https://github.com/davidamoah1/Data-Integration-and-Analytics" target="_blank">GitHub</a>
    </div>
    """,
    unsafe_allow_html=True,
)
