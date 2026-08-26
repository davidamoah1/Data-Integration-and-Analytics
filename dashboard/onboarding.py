"""Onboarding module for first-time user experience.

Provides:
  - Welcome screen
  - Product tour steps
  - Guided setup wizard
  - Quick start checklist
"""

import streamlit as st

from enterprise.industry_packs import get_all_packs, get_pack, get_pack_names

ONBOARDING_STEPS = [
    {"key": "welcome", "title": "Welcome", "icon": "ðŸ‘‹", "desc": "Get started with DataFlow"},
    {
        "key": "org_profile",
        "title": "Organization Profile",
        "icon": "ðŸ¢",
        "desc": "Set up your organization",
    },
    {
        "key": "user_profile",
        "title": "Your Profile",
        "icon": "ðŸ‘¤",
        "desc": "Personalize your account",
    },
    {"key": "team_invite", "title": "Invite Your Team", "icon": "ðŸ‘¥", "desc": "Add team members"},
    {
        "key": "data_import",
        "title": "Import Data",
        "icon": "ï¿½",
        "desc": "Upload your first dataset",
    },
    {
        "key": "etl_pipeline",
        "title": "ETL Pipeline",
        "icon": "ðŸ”„",
        "desc": "Set up data transformation",
    },
    {"key": "dashboard", "title": "First Dashboard", "icon": "ðŸ“Š", "desc": "View your analytics"},
    {"key": "ai_copilot", "title": "AI Copilot", "icon": "ðŸ¤–", "desc": "Chat with your data"},
    {"key": "report", "title": "First Report", "icon": "ï¿½", "desc": "Generate insights"},
]

QUICK_START_CHECKLIST = [
    {"key": "connect_data", "label": "Connect to a data source", "done": False},
    {"key": "view_dashboard", "label": "View your first dashboard", "done": False},
    {"key": "apply_filters", "label": "Apply filters to your data", "done": False},
    {"key": "ask_ai", "label": "Ask the AI Copilot a question", "done": False},
    {"key": "export_data", "label": "Export filtered data to CSV", "done": False},
    {"key": "explore_charts", "label": "Explore at least 3 charts", "done": False},
]


def is_onboarding_complete() -> bool:
    """Check if the user has completed onboarding."""
    return st.session_state.get("onboarding_complete", False)


def render_welcome_screen():
    """Render a welcome screen for first-time users."""
    st.markdown(
        """
    <div style="text-align:center;padding:40px 20px;">
        <div style="font-size:3rem;margin-bottom:16px;">ðŸ“Š</div>
        <h1 style="color:#a78bfa;margin-bottom:8px;">Welcome to DataFlow</h1>
        <p style="color:rgba(255,255,255,0.6);font-size:1.1rem;max-width:500px;margin:0 auto 24px;">
            Your Enterprise Data Intelligence Platform. Turn raw data into clear business insights
            with interactive dashboards, AI-powered analytics, and automated ETL pipelines.
        </p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            """
        <div style="text-align:center;padding:20px;border:1px solid rgba(255,255,255,0.1);border-radius:12px;">
            <div style="font-size:2rem;">ðŸ”„</div>
            <h4>ETL Pipelines</h4>
            <p style="color:rgba(255,255,255,0.5);font-size:0.85rem;">Extract, transform, and load data automatically</p>
        </div>
        """,
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            """
        <div style="text-align:center;padding:20px;border:1px solid rgba(255,255,255,0.1);border-radius:12px;">
            <div style="font-size:2rem;">ðŸ“ˆ</div>
            <h4>Live Dashboards</h4>
            <p style="color:rgba(255,255,255,0.5);font-size:0.85rem;">Interactive charts and real-time KPIs</p>
        </div>
        """,
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            """
        <div style="text-align:center;padding:20px;border:1px solid rgba(255,255,255,0.1);border-radius:12px;">
            <div style="font-size:2rem;">ðŸ¤–</div>
            <h4>AI Copilot</h4>
            <p style="color:rgba(255,255,255,0.5);font-size:0.85rem;">Ask questions in plain English</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("ðŸš€ Get Started (Guided Tour)", use_container_width=True, type="primary"):
            st.session_state["onboarding_step"] = 0
            st.session_state["onboarding_active"] = True
            st.rerun()
    with col_b:
        if st.button("â­ï¸ Skip â€” I'll explore on my own", use_container_width=True):
            st.session_state["onboarding_complete"] = True
            st.rerun()


def render_setup_wizard():
    """Render the guided setup wizard."""
    step_idx = st.session_state.get("onboarding_step", 0)
    step = ONBOARDING_STEPS[step_idx]

    st.markdown(
        f"""
    <div style="padding:20px 0;">
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:16px;">
            <span style="font-size:2rem;">{step['icon']}</span>
            <div>
                <h3 style="margin:0;color:#a78bfa;">Step {step_idx + 1}: {step['title']}</h3>
                <p style="margin:0;color:rgba(255,255,255,0.5);font-size:0.9rem;">{step['desc']}</p>
            </div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    progress = (step_idx + 1) / len(ONBOARDING_STEPS)
    st.progress(progress, text=f"Step {step_idx + 1} of {len(ONBOARDING_STEPS)}")

    if step["key"] == "welcome":
        st.info(
            "DataFlow helps you go from raw data to insights in minutes. "
            "This guided setup will walk you through 8 quick steps to get your organization ready. "
            "You can skip at any time and explore on your own."
        )

    elif step["key"] == "org_profile":
        st.info(
            "Your organization profile defines how DataFlow appears to your team.\n\n"
            "1. **Organization Name** â€” Shown in headers and reports\n"
            "2. **Industry** â€” Select from SME, Healthcare, Education, Government, Church, NGO\n"
            "3. **Timezone & Currency** â€” Used for date formatting and financial displays\n"
            "4. **Logo & Branding** â€” Customize colors and upload your logo\n\n"
            "Configure this in **Settings â†’ Organization** after setup."
        )

    elif step["key"] == "user_profile":
        st.info(
            "Personalize your account:\n\n"
            "1. **Full Name** â€” Displayed to team members\n"
            "2. **Role** â€” Admin, Analyst, or Viewer\n"
            "3. **Profile Picture** â€” Upload or use initials\n"
            "4. **Language & Timezone** â€” For localized experience\n\n"
            "Update this in **Settings â†’ Profile** after setup."
        )

    elif step["key"] == "team_invite":
        st.info(
            "Invite team members to collaborate:\n\n"
            "1. Go to **Settings â†’ Users**\n"
            "2. Click **Invite User**\n"
            "3. Enter their email and assign a role\n"
            "4. They'll receive an invitation to join your organization\n\n"
            "Roles available:\n"
            "- **Admin** â€” Full access to all settings and data\n"
            "- **Analyst** â€” Create dashboards, run ETL, use AI Copilot\n"
            "- **Viewer** â€” View dashboards and export data (read-only)"
        )

    elif step["key"] == "data_import":
        st.info(
            "Import your first dataset:\n\n"
            "1. Use the **sidebar** to select 'Upload File'\n"
            "2. Drag and drop a CSV or Excel file (max 50MB on trial)\n"
            "3. DataFlow automatically detects columns and cleans the data\n"
            "4. Common issues fixed automatically: duplicates, date formats, currency strings\n\n"
            "Upload your own CSV or Excel file to get started with real data."
        )

    elif step["key"] == "etl_pipeline":
        st.info(
            "Set up an ETL pipeline for automated data processing:\n\n"
            "1. Go to **ETL â†’ Pipelines**\n"
            "2. Click **Create Pipeline**\n"
            "3. Define your data source (CSV, database, API)\n"
            "4. Configure transformation rules\n"
            "5. Set a schedule (daily, weekly, monthly)\n\n"
            "DataFlow handles extraction, transformation, and loading automatically."
        )

    elif step["key"] == "dashboard":
        st.info(
            "Once your data is loaded, you'll see:\n\n"
            "- **KPI Cards** â€” Key metrics at a glance\n"
            "- **Charts** â€” Sector-specific visualizations (different per industry!)\n"
            "- **Data Table** â€” Browse your records\n"
            "- **Filters** â€” Narrow down by region, category, or date range\n\n"
            "Select an industry pack in the sidebar to see sector-specific dashboards."
        )

    elif step["key"] == "ai_copilot":
        st.info(
            "The AI Copilot lets you ask questions in plain English:\n\n"
            "- 'What are the top selling products?'\n"
            "- 'Show me profit by region'\n"
            "- 'Explain the revenue trend'\n"
            "- 'Generate a monthly report'\n\n"
            "The AI understands your data context and provides instant insights with citations."
        )

    elif step["key"] == "report":
        st.info(
            "Generate your first report:\n\n"
            "1. Use the AI Copilot to ask for a report\n"
            "2. Or go to **Reports â†’ Generate**\n"
            "3. Choose report type: Executive, Monthly, Department, Custom\n"
            "4. Download as Markdown, HTML, or PDF\n\n"
            "Reports include charts, KPIs, and AI-generated insights automatically."
        )

    col_prev, col_next = st.columns([1, 2])
    with col_prev:
        if step_idx > 0 and st.button("â† Previous", use_container_width=True):
            st.session_state["onboarding_step"] = step_idx - 1
            st.rerun()
    with col_next:
        if step_idx < len(ONBOARDING_STEPS) - 1 and st.button(
            "Next â†’", use_container_width=True, type="primary"
        ):
            st.session_state["onboarding_step"] = step_idx + 1
            st.rerun()
        elif step_idx == len(ONBOARDING_STEPS) - 1 and st.button(
            "âœ“ Finish Setup", use_container_width=True, type="primary"
        ):
            st.session_state["onboarding_complete"] = True
            st.session_state["onboarding_active"] = False
            st.rerun()


def render_quick_start_checklist():
    """Render a quick start checklist in the sidebar."""
    if "checklist" not in st.session_state:
        st.session_state["checklist"] = {item["key"]: False for item in QUICK_START_CHECKLIST}

    completed = sum(1 for v in st.session_state["checklist"].values() if v)
    total = len(QUICK_START_CHECKLIST)

    st.markdown(
        f"""
    <div class="sidebar-section">Quick Start ({completed}/{total})</div>
    """,
        unsafe_allow_html=True,
    )

    for item in QUICK_START_CHECKLIST:
        key = item["key"]
        is_done = st.session_state["checklist"].get(key, False)
        if st.checkbox(f"{item['label']}", value=is_done, key=f"checklist_{key}"):
            st.session_state["checklist"][key] = True
        else:
            st.session_state["checklist"][key] = False

    if completed == total:
        st.success("ðŸŽ‰ All done! You're ready to explore.")


def render_industry_pack_selector():
    """Render an industry pack selector for new users."""
    st.markdown(
        """
    <div class="sidebar-section">Industry Templates</div>
    """,
        unsafe_allow_html=True,
    )
    pack_names = get_pack_names()
    pack_labels = [get_all_packs()[p]["name"] for p in pack_names]
    selected = st.selectbox("Choose your industry", ["None"] + pack_labels)
    if selected != "None":
        pack_key = pack_names[pack_labels.index(selected)]
        pack = get_pack(pack_key)
        if pack:
            st.session_state["active_industry_pack"] = pack_key
            st.session_state["active_industry_pack_name"] = pack["name"]
            st.caption(pack["description"])
            dashboards = pack.get("dashboards", [])
            st.markdown(f"**{len(dashboards)} dashboards** included")
            for d in dashboards[:3]:
                st.markdown(f"- {d['name']}")
            if len(dashboards) > 3:
                st.caption(f"...and {len(dashboards) - 3} more")
    else:
        st.session_state["active_industry_pack"] = None
        st.session_state["active_industry_pack_name"] = None


INDUSTRY_LABELS = {
    "sme": {
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
    },
    "education": {
        "revenue": "Tuition Revenue",
        "profit": "Net Revenue",
        "orders": "Transactions",
        "avg_order": "Avg Payment",
        "performance": "Enrollment & Revenue Performance",
        "breakdown": "Department and Regional Breakdown",
        "deep_dive": "Deep Dive Analysis",
        "regional": "Regional Analysis",
        "category_label": "Program Type",
        "product_label": "Top Departments",
        "region_label": "Region",
    },
    "healthcare": {
        "revenue": "Billing Amount",
        "profit": "Net Billing",
        "orders": "Transactions",
        "avg_order": "Avg Bill Amount",
        "performance": "Billing Performance",
        "breakdown": "Department and Regional Breakdown",
        "deep_dive": "Deep Dive Analysis",
        "regional": "Regional Analysis",
        "category_label": "Service Type",
        "product_label": "Top Departments",
        "region_label": "Region",
    },
    "government": {
        "revenue": "Spending Amount",
        "profit": "Net Spending",
        "orders": "Projects",
        "avg_order": "Avg Project Cost",
        "performance": "Spending Performance",
        "breakdown": "Department and Regional Breakdown",
        "deep_dive": "Deep Dive Analysis",
        "regional": "Regional Analysis",
        "category_label": "Project Type",
        "product_label": "Top Departments",
        "region_label": "Region",
    },
    "church": {
        "revenue": "Offerings",
        "profit": "Net Offerings",
        "orders": "Transactions",
        "avg_order": "Avg Offering",
        "performance": "Offerings Performance",
        "breakdown": "Department and Regional Breakdown",
        "deep_dive": "Deep Dive Analysis",
        "regional": "Regional Analysis",
        "category_label": "Event Type",
        "product_label": "Top Departments",
        "region_label": "Region",
    },
    "ngo": {
        "revenue": "Donations",
        "profit": "Net Donations",
        "orders": "Transactions",
        "avg_order": "Avg Donation",
        "performance": "Donations Performance",
        "breakdown": "Program and Regional Breakdown",
        "deep_dive": "Deep Dive Analysis",
        "regional": "Regional Analysis",
        "category_label": "Program Type",
        "product_label": "Top Programs",
        "region_label": "Region",
    },
    "retail": {
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
    },
    "manufacturing": {
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
    },
    "agriculture": {
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
    },
}


def get_industry_labels() -> dict:
    """Get label overrides for the currently selected industry pack."""
    pack_key = st.session_state.get("active_industry_pack")
    if pack_key and pack_key in INDUSTRY_LABELS:
        return INDUSTRY_LABELS[pack_key]
    return INDUSTRY_LABELS["sme"]


def render_onboarding():
    """Main entry point â€” renders welcome or setup wizard for new users."""
    if is_onboarding_complete():
        return

    if st.session_state.get("onboarding_active"):
        render_setup_wizard()
        st.markdown("---")
    else:
        render_welcome_screen()
        st.stop()
