"""Onboarding module for first-time user experience.

Provides:
  - Welcome screen
  - Product tour steps
  - Guided setup wizard
  - Quick start checklist
  - Sample data seeding
"""

import streamlit as st

from enterprise.industry_packs import get_all_packs, get_pack_names

ONBOARDING_STEPS = [
    {"key": "welcome", "title": "Welcome", "icon": "👋", "desc": "Get started with DataFlow"},
    {"key": "data_source", "title": "Connect Data", "icon": "🗄️", "desc": "Choose your data source"},
    {"key": "explore", "title": "Explore Dashboards", "icon": "📊", "desc": "View your analytics"},
    {"key": "ai_copilot", "title": "Ask AI Copilot", "icon": "🤖", "desc": "Chat with your data"},
    {"key": "export", "title": "Export Reports", "icon": "📤", "desc": "Download your insights"},
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
        <div style="font-size:3rem;margin-bottom:16px;">📊</div>
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
            <div style="font-size:2rem;">🔄</div>
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
            <div style="font-size:2rem;">📈</div>
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
            <div style="font-size:2rem;">🤖</div>
            <h4>AI Copilot</h4>
            <p style="color:rgba(255,255,255,0.5);font-size:0.85rem;">Ask questions in plain English</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("🚀 Get Started (Guided Tour)", use_container_width=True, type="primary"):
            st.session_state["onboarding_step"] = 0
            st.session_state["onboarding_active"] = True
            st.rerun()
    with col_b:
        if st.button("⏭️ Skip — I'll explore on my own", use_container_width=True):
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
            "This quick tour will show you the key features. Let's get started!"
        )

    elif step["key"] == "data_source":
        st.info(
            "DataFlow supports two data sources:\n\n"
            "1. **Live Database** — Connect to your MySQL or SQLite database\n"
            "2. **File Upload** — Upload a CSV or Excel file for instant analysis\n\n"
            "Use the sidebar on the left to choose your data source."
        )

    elif step["key"] == "explore":
        st.info(
            "Once your data is loaded, you'll see:\n\n"
            "- **KPI Cards** — Key metrics at a glance\n"
            "- **Charts** — Revenue trends, category breakdowns, regional analysis\n"
            "- **Data Table** — Browse your records\n"
            "- **Filters** — Narrow down by region, category, or date range"
        )

    elif step["key"] == "ai_copilot":
        st.info(
            "The AI Copilot lets you ask questions in plain English:\n\n"
            "- 'What are the top selling products?'\n"
            "- 'Show me profit by region'\n"
            "- 'Explain the revenue trend'\n\n"
            "The AI understands your data and provides instant insights."
        )

    elif step["key"] == "export":
        st.info(
            "Export your filtered data anytime:\n\n"
            "- Click **Download Filtered Data** in the sidebar\n"
            "- Get a CSV file with your current view\n"
            "- Use for reports, presentations, or further analysis"
        )

    col_prev, col_next = st.columns([1, 2])
    with col_prev:
        if step_idx > 0:
            if st.button("← Previous", use_container_width=True):
                st.session_state["onboarding_step"] = step_idx - 1
                st.rerun()
    with col_next:
        if step_idx < len(ONBOARDING_STEPS) - 1:
            if st.button("Next →", use_container_width=True, type="primary"):
                st.session_state["onboarding_step"] = step_idx + 1
                st.rerun()
        else:
            if st.button("✓ Finish Setup", use_container_width=True, type="primary"):
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
        icon = "✅" if is_done else "⬜"
        if st.checkbox(f"{item['label']}", value=is_done, key=f"checklist_{key}"):
            st.session_state["checklist"][key] = True
        else:
            st.session_state["checklist"][key] = False

    if completed == total:
        st.success("🎉 All done! You're ready to explore.")


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
            st.caption(pack["description"])
            dashboards = pack.get("dashboards", [])
            st.markdown(f"**{len(dashboards)} dashboards** included")
            for d in dashboards[:3]:
                st.markdown(f"- {d['name']}")
            if len(dashboards) > 3:
                st.caption(f"...and {len(dashboards) - 3} more")


def render_onboarding():
    """Main entry point — renders welcome or setup wizard for new users."""
    if is_onboarding_complete():
        return

    if st.session_state.get("onboarding_active"):
        render_setup_wizard()
        st.markdown("---")
    else:
        render_welcome_screen()
        st.stop()
