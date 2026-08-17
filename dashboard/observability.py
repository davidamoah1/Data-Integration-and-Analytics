"""Observability module — admin dashboards for system monitoring.

Tracks:
  - Login activity
  - API performance
  - ETL execution
  - Dashboard usage
  - AI usage
  - Errors
  - Background jobs
"""

import os
from datetime import datetime, timezone

import pandas as pd
import plotly.express as px
import streamlit as st

from dashboard.styles import CHART_LAYOUT


def _section_header(title: str):
    st.markdown(
        f'<div class="section-header">{title}</div><hr class="section-divider">',
        unsafe_allow_html=True,
    )


def _kpi_card(value: str, label: str, icon: str, css_class: str):
    st.markdown(
        f'<div class="kpi-card {css_class}"><span class="kpi-icon">{icon}</span>'
        f'<div class="kpi-value">{value}</div>'
        f'<div class="kpi-label">{label}</div></div>',
        unsafe_allow_html=True,
    )


def render_observability_page():
    """Render the admin observability dashboard."""
    _section_header("System Observability")

    # Fetch data from API
    api_url = st.session_state.get(
        "api_base_url", os.getenv("API_BASE_URL", "http://localhost:8000")
    )
    token = st.session_state.get("access_token")

    headers = {"Authorization": f"Bearer {token}"} if token else {}

    # ── KPI Overview ──
    col1, col2, col3, col4 = st.columns(4)

    try:
        import requests

        # Health check
        health_resp = requests.get(f"{api_url}/health", timeout=5)
        health = health_resp.json() if health_resp.status_code == 200 else {}

        # Readiness
        ready_resp = requests.get(f"{api_url}/ready", timeout=5)
        readiness = ready_resp.json() if ready_resp.status_code == 200 else {}

        with col1:
            status = health.get("status", "unknown")
            icon = "✅" if status == "healthy" else "⚠️"
            _kpi_card(status.title(), "API Status", icon, "kpi-card-sales")

        with col2:
            count = health.get("record_count", 0)
            _kpi_card(f"{count:,}", "Records in DB", "📦", "kpi-card-orders")

        with col3:
            checks = readiness.get("checks", {})
            all_ok = all(c.get("status") == "ok" for c in checks.values()) if checks else False
            _kpi_card(
                "All Operational" if all_ok else "Degraded", "Subsystems", "🔧", "kpi-card-profit"
            )

        with col4:
            now = datetime.now(timezone.utc).strftime("%H:%M UTC")
            _kpi_card(now, "Last Checked", "🕐", "kpi-card-avg")

    except Exception as e:
        st.warning(f"Cannot connect to API for live metrics: {e}")
        with col1:
            _kpi_card("Offline", "API Status", "❌", "kpi-card-sales")
        with col2:
            _kpi_card("—", "Records in DB", "📦", "kpi-card-orders")
        with col3:
            _kpi_card("—", "Subsystems", "🔧", "kpi-card-profit")
        with col4:
            _kpi_card("—", "Last Checked", "🕐", "kpi-card-avg")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Subsystem Health ──
    _section_header("Subsystem Health")
    try:
        if readiness.get("checks"):
            checks = readiness["checks"]
            check_data = []
            for name, info in checks.items():
                check_data.append(
                    {
                        "Subsystem": name.title(),
                        "Status": info.get("status", "unknown").title(),
                        "Detail": info.get("detail", ""),
                    }
                )
            df_checks = pd.DataFrame(check_data)
            st.dataframe(df_checks, use_container_width=True, hide_index=True)
        else:
            st.info("No subsystem checks available.")
    except Exception:
        st.info("Subsystem health data unavailable.")

    # ── Login Activity ──
    _section_header("Login Activity")
    try:
        import requests

        login_resp = requests.get(
            f"{api_url}/audit/logs?action=login&pageSize=100", headers=headers, timeout=5
        )
        if login_resp.status_code == 200:
            login_data = login_resp.json()
            logs = login_data.get("data", {}).get("logs", [])
            if logs:
                df_logins = pd.DataFrame(logs)
                if "created_at" in df_logins.columns:
                    df_logins["created_at"] = pd.to_datetime(
                        df_logins["created_at"], errors="coerce"
                    )
                    df_logins["date"] = df_logins["created_at"].dt.date
                    daily = df_logins.groupby("date").size().reset_index(name="Logins")
                    fig = px.bar(
                        daily,
                        x="date",
                        y="Logins",
                        color_discrete_sequence=["#667eea"],
                        template="none",
                    )
                    fig.update_layout(**CHART_LAYOUT, height=280)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Login data available but missing timestamps.")
            else:
                st.info("No login activity recorded yet.")
        else:
            st.info(f"Login logs require authentication (status {login_resp.status_code}).")
    except Exception as e:
        st.info(f"Login activity monitoring unavailable: {e}")

    # ── Audit Logs ──
    _section_header("Recent Audit Activity")
    try:
        import requests

        audit_resp = requests.get(f"{api_url}/audit/logs?pageSize=20", headers=headers, timeout=5)
        if audit_resp.status_code == 200:
            audit_data = audit_resp.json()
            logs = audit_data.get("data", {}).get("logs", [])
            if logs:
                df_audit = pd.DataFrame(logs)
                display_cols = [
                    c
                    for c in ["id", "user_id", "action", "resource_type", "created_at"]
                    if c in df_audit.columns
                ]
                st.dataframe(df_audit[display_cols], use_container_width=True, hide_index=True)
            else:
                st.info("No audit logs recorded yet.")
        else:
            st.info(f"Audit logs require admin authentication (status {audit_resp.status_code}).")
    except Exception as e:
        st.info(f"Audit log monitoring unavailable: {e}")

    # ── Security Events ──
    _section_header("Security Events")
    try:
        import requests

        sec_resp = requests.get(
            f"{api_url}/audit/security-logs?pageSize=20", headers=headers, timeout=5
        )
        if sec_resp.status_code == 200:
            sec_data = sec_resp.json()
            logs = sec_data.get("data", {}).get("logs", [])
            if logs:
                df_sec = pd.DataFrame(logs)
                display_cols = [
                    c
                    for c in ["id", "event_type", "severity", "ip_address", "created_at"]
                    if c in df_sec.columns
                ]
                st.dataframe(df_sec[display_cols], use_container_width=True, hide_index=True)
            else:
                st.info("No security events recorded.")
        else:
            st.info(f"Security logs require admin authentication (status {sec_resp.status_code}).")
    except Exception as e:
        st.info(f"Security event monitoring unavailable: {e}")

    # ── System Logs ──
    _section_header("System Logs")
    try:
        import requests

        sys_resp = requests.get(
            f"{api_url}/audit/system-logs?pageSize=20", headers=headers, timeout=5
        )
        if sys_resp.status_code == 200:
            sys_data = sys_resp.json()
            logs = sys_data.get("data", {}).get("logs", [])
            if logs:
                df_sys = pd.DataFrame(logs)
                display_cols = [
                    c
                    for c in ["id", "level", "source", "message", "created_at"]
                    if c in df_sys.columns
                ]
                st.dataframe(df_sys[display_cols], use_container_width=True, hide_index=True)
            else:
                st.info("No system logs recorded.")
        else:
            st.info(f"System logs require admin authentication (status {sys_resp.status_code}).")
    except Exception as e:
        st.info(f"System log monitoring unavailable: {e}")
