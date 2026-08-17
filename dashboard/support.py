"""Support tools module — feedback, bug reports, feature requests, diagnostics.

Provides a unified support interface for users to:
  - Submit feedback
  - Report bugs
  - Request features
  - Contact support
  - View system diagnostics
"""

import os
import platform
import sys
from datetime import datetime, timezone

import psutil
import streamlit as st

from dashboard.utils import sanitize_text

SUPPORT_CATEGORIES = [
    "General Feedback",
    "Bug Report",
    "Feature Request",
    "Performance Issue",
    "Security Concern",
    "Data Issue",
    "UI/UX Suggestion",
    "Other",
]

PRIORITY_LEVELS = ["Low", "Medium", "High", "Critical"]


def _save_support_ticket(ticket: dict):
    """Save support ticket to session state (in production, this would persist to DB)."""
    if "support_tickets" not in st.session_state:
        st.session_state["support_tickets"] = []
    st.session_state["support_tickets"].append(ticket)


def render_support_page():
    """Render the full support page with feedback form, diagnostics, and ticket history."""
    st.markdown(
        '<div class="section-header">Support Center</div><hr class="section-divider">',
        unsafe_allow_html=True,
    )

    tab1, tab2, tab3, tab4 = st.tabs(
        ["📝 Submit Ticket", "🐛 Bug Report", "💡 Feature Request", "🔧 Diagnostics"]
    )

    # ── Tab 1: General Feedback / Contact Support ──
    with tab1:
        st.markdown("### Submit Feedback or Contact Support")
        with st.form("feedback_form"):
            col1, col2 = st.columns(2)
            with col1:
                category = st.selectbox("Category", SUPPORT_CATEGORIES, key="fb_category")
                priority = st.selectbox("Priority", PRIORITY_LEVELS, key="fb_priority")
            with col2:
                subject = st.text_input("Subject", key="fb_subject", placeholder="Brief summary")
                email = st.text_input("Contact email", key="fb_email", placeholder="your@email.com")

            description = st.text_area(
                "Description",
                key="fb_description",
                height=150,
                placeholder="Provide details about your feedback, question, or issue...",
            )

            submitted = st.form_submit_button("Submit", type="primary", use_container_width=True)
            if submitted:
                if not subject or not description:
                    st.error("Subject and description are required.")
                else:
                    ticket = {
                        "id": f"TKT-{len(st.session_state.get('support_tickets', [])) + 1001:04d}",
                        "category": category,
                        "priority": priority,
                        "subject": sanitize_text(subject),
                        "description": sanitize_text(description),
                        "email": sanitize_text(email) if email else "",
                        "status": "open",
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    }
                    _save_support_ticket(ticket)
                    st.success(f"Ticket {ticket['id']} submitted! Our team will review it shortly.")

    # ── Tab 2: Bug Report ──
    with tab2:
        st.markdown("### Report a Bug")
        with st.form("bug_form"):
            col1, col2 = st.columns(2)
            with col1:
                bug_severity = st.selectbox(
                    "Severity", ["Minor", "Moderate", "Major", "Critical"], key="bug_severity"
                )
                bug_module = st.selectbox(
                    "Affected Module",
                    [
                        "Dashboard",
                        "ETL Pipeline",
                        "AI Copilot",
                        "Authentication",
                        "Data Upload",
                        "Reports",
                        "API",
                        "Other",
                    ],
                    key="bug_module",
                )
            with col2:
                bug_freq = st.selectbox(
                    "Frequency", ["Always", "Often", "Sometimes", "Rarely", "Once"], key="bug_freq"
                )
                bug_browser = st.text_input(
                    "Browser/OS", key="bug_browser", placeholder="Chrome/Windows 11"
                )

            bug_title = st.text_input("Bug Title", key="bug_title", placeholder="What happened?")
            bug_steps = st.text_area(
                "Steps to Reproduce",
                key="bug_steps",
                height=120,
                placeholder="1. Go to...\n2. Click on...\n3. See error...",
            )
            bug_expected = st.text_input(
                "Expected Behavior", key="bug_expected", placeholder="What should have happened?"
            )
            bug_actual = st.text_input(
                "Actual Behavior", key="bug_actual", placeholder="What actually happened?"
            )

            submitted = st.form_submit_button(
                "Submit Bug Report", type="primary", use_container_width=True
            )
            if submitted:
                if not bug_title or not bug_steps:
                    st.error("Bug title and steps to reproduce are required.")
                else:
                    ticket = {
                        "id": f"BUG-{len(st.session_state.get('support_tickets', [])) + 2001:04d}",
                        "category": "Bug Report",
                        "priority": bug_severity,
                        "subject": sanitize_text(bug_title),
                        "description": f"Module: {bug_module}\nFrequency: {bug_freq}\nBrowser: {bug_browser}\n\nSteps:\n{bug_steps}\n\nExpected: {bug_expected}\nActual: {bug_actual}",
                        "status": "open",
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    }
                    _save_support_ticket(ticket)
                    st.success(
                        f"Bug report {ticket['id']} submitted! Thank you for helping improve DataFlow."
                    )

    # ── Tab 3: Feature Request ──
    with tab3:
        st.markdown("### Request a Feature")
        with st.form("feature_form"):
            feat_title = st.text_input(
                "Feature Title", key="feat_title", placeholder="What feature would you like?"
            )
            feat_category = st.selectbox(
                "Category",
                [
                    "Dashboard",
                    "ETL",
                    "AI",
                    "Reports",
                    "Integrations",
                    "User Management",
                    "Data Sources",
                    "Other",
                ],
                key="feat_category",
            )
            feat_description = st.text_area(
                "Description",
                key="feat_description",
                height=150,
                placeholder="Describe the feature, why you need it, and how it would help your workflow...",
            )
            feat_urgency = st.selectbox(
                "Urgency",
                ["Nice to have", "Would help", "Important", "Critical"],
                key="feat_urgency",
            )

            submitted = st.form_submit_button(
                "Submit Feature Request", type="primary", use_container_width=True
            )
            if submitted:
                if not feat_title or not feat_description:
                    st.error("Title and description are required.")
                else:
                    ticket = {
                        "id": f"FR-{len(st.session_state.get('support_tickets', [])) + 3001:04d}",
                        "category": "Feature Request",
                        "priority": feat_urgency,
                        "subject": sanitize_text(feat_title),
                        "description": f"Category: {feat_category}\n\n{sanitize_text(feat_description)}",
                        "status": "open",
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    }
                    _save_support_ticket(ticket)
                    st.success(
                        f"Feature request {ticket['id']} submitted! We'll consider it for future releases."
                    )

    # ── Tab 4: System Diagnostics ──
    with tab4:
        st.markdown("### System Diagnostics")
        st.markdown("View real-time system health and platform information.")

        col1, col2, col3, col4 = st.columns(4)
        try:
            cpu = psutil.cpu_percent(interval=1)
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            with col1:
                st.metric("CPU Usage", f"{cpu:.1f}%")
            with col2:
                st.metric("Memory Usage", f"{mem.percent:.1f}%")
            with col3:
                st.metric("Disk Usage", f"{disk.percent:.1f}%")
            with col4:
                st.metric(
                    "Python Version",
                    f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                )
        except Exception:
            with col1:
                st.metric("CPU Usage", "N/A")
            with col2:
                st.metric("Memory Usage", "N/A")
            with col3:
                st.metric("Disk Usage", "N/A")
            with col4:
                st.metric("Python Version", f"{sys.version_info.major}.{sys.version_info.minor}")

        st.markdown("---")
        st.markdown("#### Platform Information")
        info = {
            "Platform": platform.platform(),
            "Python Version": sys.version.split()[0],
            "Machine": platform.machine(),
            "Processor": platform.processor() or "Unknown",
        }
        for key, val in info.items():
            st.text(f"{key}: {val}")

        st.markdown("---")
        st.markdown("#### Health Check")
        try:
            import requests

            api_url = st.session_state.get(
                "api_base_url", os.getenv("API_BASE_URL", "http://localhost:8000")
            )
            resp = requests.get(f"{api_url}/health", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                st.success(f"API Status: {data.get('status', 'unknown').title()}")
                st.json(data)
            else:
                st.warning(f"API returned status {resp.status_code}")
        except Exception as e:
            st.error(f"Cannot reach API: {e}")

    # ── Ticket History ──
    st.markdown("---")
    st.markdown("### Your Support Tickets")
    tickets = st.session_state.get("support_tickets", [])
    if tickets:
        for t in reversed(tickets):
            with st.expander(f"{t['id']} — {t['subject']} ({t['status'].title()})"):
                st.json(t)
    else:
        st.info("No support tickets yet. Submit one above to get started.")
