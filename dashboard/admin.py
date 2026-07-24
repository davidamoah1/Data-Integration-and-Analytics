"""Administration module — organization profile, branding, user management.

Provides admin interface for:
  - Organization profile (name, description, contact, timezone, currency)
  - Logo upload & theme customization
  - User management (list, invite, roles)
  - Role management
  - Audit logs viewer
  - Activity history
"""

# ruff: noqa: F841  # Streamlit form variables are used via session state keys

from datetime import datetime

import pandas as pd
import streamlit as st


def _section_header(title: str):
    st.markdown(
        f'<div class="section-header">{title}</div><hr class="section-divider">',
        unsafe_allow_html=True,
    )


def _api_call(method: str, endpoint: str, token: str | None = None, **kwargs):
    """Make an API call with authentication."""
    import requests

    api_url = st.session_state.get("api_base_url", "http://localhost:8000")
    headers = kwargs.pop("headers", {})
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        resp = getattr(requests, method)(
            f"{api_url}{endpoint}", headers=headers, timeout=10, **kwargs
        )
        if resp.status_code == 200:
            return resp.json()
        return {"error": resp.status_code, "detail": resp.text[:200]}
    except Exception as e:
        return {"error": str(e)}


def render_admin_page():
    """Render the administration page."""
    _section_header("Organization Administration")

    token = st.session_state.get("access_token")
    roles = st.session_state.get("user_roles", [])
    is_admin = "admin" in roles or "super_admin" in roles

    if not is_admin:
        st.warning("Admin access required to view this page.")
        return

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["🏢 Organization", "🎨 Branding", "👥 Users", "🎭 Roles", "📋 Audit Logs"]
    )

    # ── Tab 1: Organization Profile ──
    with tab1:
        st.markdown("### Organization Profile")

        # Fetch current org info
        org_data = _api_call("get", "/organizations/", token=token)
        if "error" in org_data:
            st.warning(
                f"Cannot fetch organization data: {org_data.get('detail', org_data.get('error'))}"
            )
            org_data = {}

        with st.form("org_profile_form"):
            col1, col2 = st.columns(2)
            with col1:
                org_name = st.text_input(
                    "Organization Name", value=org_data.get("name", ""), key="org_name"
                )
                org_slug = st.text_input("Slug", value=org_data.get("slug", ""), key="org_slug")
                org_email = st.text_input(
                    "Contact Email", value=org_data.get("contact_email", ""), key="org_email"
                )
                org_phone = st.text_input(
                    "Contact Phone", value=org_data.get("contact_phone", ""), key="org_phone"
                )
            with col2:
                org_timezone = st.text_input(
                    "Timezone", value=org_data.get("timezone", "UTC"), key="org_timezone"
                )
                org_locale = st.text_input(
                    "Locale", value=org_data.get("locale", "en"), key="org_locale"
                )
                org_date_fmt = st.text_input(
                    "Date Format",
                    value=org_data.get("date_format", "YYYY-MM-DD"),
                    key="org_date_fmt",
                )
                org_website = st.text_input(
                    "Website URL", value=org_data.get("website_url", ""), key="org_website"
                )

            org_description = st.text_area(
                "Description",
                value=org_data.get("description", ""),
                key="org_description",
                height=80,
            )
            org_address = st.text_area(
                "Address", value=org_data.get("address", ""), key="org_address", height=60
            )

            submitted = st.form_submit_button("Save Changes", type="primary")
            if submitted:
                st.info(
                    "Organization profile updates are saved via the API. Connect to the backend to persist changes."
                )

        # Subscription info
        st.markdown("---")
        st.markdown("#### Subscription Status")
        sub_data = _api_call("get", "/platform/subscription/current", token=token)
        if "error" not in sub_data:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Plan", sub_data.get("plan", "—").title())
            with col2:
                st.metric("Status", sub_data.get("status", "—").title())
            with col3:
                trial_end = sub_data.get("trial_ends_at")
                if trial_end:
                    st.metric("Trial Ends", trial_end[:10])
                else:
                    st.metric("Max Users", sub_data.get("max_users", "—"))

            st.markdown("**Features Enabled:**")
            features = sub_data.get("features", [])
            if features:
                st.markdown(", ".join(f"`{f}`" for f in features))
            else:
                st.info("No features enabled.")
        else:
            st.info("Subscription data unavailable.")

    # ── Tab 2: Branding ──
    with tab2:
        st.markdown("### Branding & Theme")
        st.info("Customize how DataFlow looks for your organization.")

        with st.form("branding_form"):
            col1, col2 = st.columns(2)
            with col1:
                primary_color = st.color_picker("Primary Color", value="#6366f1")
                secondary_color = st.color_picker("Secondary Color", value="#a78bfa")
                accent_color = st.color_picker("Accent Color", value="#22d3ee")
                theme_mode = st.selectbox("Theme Mode", ["dark", "light"])
            with col2:
                company_name = st.text_input("Company Name (for reports)", key="brand_company")
                company_tagline = st.text_input("Company Tagline", key="brand_tagline")
                report_header = st.text_input("Report Header Text", key="brand_header")
                report_footer = st.text_input("Report Footer Text", key="brand_footer")

            logo_url = st.text_input("Logo URL", key="brand_logo", placeholder="https://...")
            custom_css = st.text_area("Custom CSS (advanced)", key="brand_css", height=80)

            submitted = st.form_submit_button("Save Branding", type="primary")
            if submitted:
                st.info(
                    "Branding updates are saved via the API. Connect to the backend to persist changes."
                )

        st.markdown("---")
        st.markdown("#### Logo Upload")
        uploaded = st.file_uploader(
            "Upload Logo (PNG/SVG, max 2MB)", type=["png", "svg", "jpg", "jpeg"]
        )
        if uploaded:
            st.image(uploaded, width=200)
            st.caption(f"Logo preview — {uploaded.name} ({uploaded.size // 1024}KB)")

    # ── Tab 3: User Management ──
    with tab3:
        st.markdown("### User Management")

        # Fetch users
        users_data = _api_call("get", "/auth/users", token=token)
        if "error" not in users_data and isinstance(users_data, list):
            df_users = pd.DataFrame(users_data)
            display_cols = [
                c
                for c in ["id", "email", "full_name", "position", "is_active", "last_login_at"]
                if c in df_users.columns
            ]
            st.dataframe(df_users[display_cols], use_container_width=True, hide_index=True)
        else:
            st.info("User list requires API connection.")

        st.markdown("---")
        st.markdown("#### Invite New User")
        with st.form("invite_user_form"):
            col1, col2 = st.columns(2)
            with col1:
                invite_email = st.text_input("Email Address", key="invite_email")
                invite_name = st.text_input("Full Name", key="invite_name")
            with col2:
                invite_role = st.selectbox(
                    "Role", ["admin", "analyst", "viewer"], key="invite_role"
                )
                invite_position = st.text_input("Position/Title", key="invite_position")

            submitted = st.form_submit_button("Send Invitation", type="primary")
            if submitted:
                if not invite_email:
                    st.error("Email is required.")
                else:
                    st.success(
                        f"Invitation would be sent to {invite_email} with role: {invite_role}"
                    )

    # ── Tab 4: Role Management ──
    with tab4:
        st.markdown("### Role Management")
        st.info("Roles control what users can do within the platform.")

        roles_data = _api_call("get", "/auth/roles", token=token)
        if "error" not in roles_data and isinstance(roles_data, list):
            df_roles = pd.DataFrame(roles_data)
            display_cols = [
                c
                for c in ["id", "name", "display_name", "description", "is_system"]
                if c in df_roles.columns
            ]
            st.dataframe(df_roles[display_cols], use_container_width=True, hide_index=True)
        else:
            # Show default roles
            st.markdown("**Default Roles:**")
            roles_info = pd.DataFrame(
                [
                    {
                        "Role": "super_admin",
                        "Description": "Full platform access including system configuration",
                        "System": True,
                    },
                    {
                        "Role": "admin",
                        "Description": "Organization admin — manage users, settings, all data",
                        "System": True,
                    },
                    {
                        "Role": "analyst",
                        "Description": "Create dashboards, run ETL, use AI Copilot, generate reports",
                        "System": True,
                    },
                    {
                        "Role": "viewer",
                        "Description": "View dashboards and export data (read-only)",
                        "System": True,
                    },
                ]
            )
            st.dataframe(roles_info, use_container_width=True, hide_index=True)

    # ── Tab 5: Audit Logs ──
    with tab5:
        st.markdown("### Audit Logs")
        st.info("Track all user actions and system events for compliance.")

        audit_data = _api_call("get", "/audit/logs?pageSize=50", token=token)
        if "error" not in audit_data:
            logs = audit_data.get("data", {}).get("logs", [])
            if logs:
                df_audit = pd.DataFrame(logs)
                display_cols = [
                    c
                    for c in [
                        "id",
                        "user_id",
                        "action",
                        "resource_type",
                        "resource_id",
                        "created_at",
                    ]
                    if c in df_audit.columns
                ]
                st.dataframe(df_audit[display_cols], use_container_width=True, hide_index=True)

                # Export
                st.download_button(
                    "Download Audit Logs (CSV)",
                    df_audit.to_csv(index=False).encode("utf-8"),
                    f"audit_logs_{datetime.now().strftime('%Y%m%d')}.csv",
                    "text/csv",
                )
            else:
                st.info("No audit logs recorded yet.")
        else:
            st.info(
                f"Audit logs require admin API access: {audit_data.get('detail', audit_data.get('error'))}"
            )
