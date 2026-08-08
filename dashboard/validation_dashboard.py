"""Hospital Data Quality Dashboard — Streamlit rendering of validation results."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from validation.engine import ValidationResult
from validation.report_generator import ValidationReportGenerator

TRAFFIC_COLORS = {
    "green": "#28a745",
    "yellow": "#ffc107",
    "red": "#dc3545",
}

STATUS_COLORS = {
    "passed": "#28a745",
    "passed_with_warnings": "#ffc107",
    "failed": "#dc3545",
    "approved": "#28a745",
    "rejected": "#dc3545",
    "pending": "#6c757d",
}


def render_validation_dashboard(result: ValidationResult) -> None:
    """Render the full validation dashboard in Streamlit."""
    st.markdown(
        '<div class="section-header">Hospital Data Validation & Quality Dashboard</div><hr class="section-divider">',
        unsafe_allow_html=True,
    )

    # Status banner
    status_color = STATUS_COLORS.get(result.status.value, "#6c757d")
    score = result.quality_score
    tl_color = TRAFFIC_COLORS.get(score.traffic_light, "#6c757d") if score else "#6c757d"

    st.markdown(
        f"""
        <div style="background:{status_color};color:white;padding:12px;border-radius:8px;margin-bottom:16px;">
            <strong>Validation Status:</strong> {result.status.value.replace("_", " ").title()}
            &nbsp;|&nbsp;
            <strong>Quality Score:</strong> {score.overall:.1f}/100
            &nbsp;|&nbsp;
            <strong>Traffic Light:</strong>
            <span style="background:{tl_color};padding:2px 10px;border-radius:12px;color:white;">
                {score.traffic_light.upper()}
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # KPI cards row
    _render_quality_score_cards(result)
    st.markdown("---")

    # Findings summary
    _render_findings_summary(result)
    st.markdown("---")

    # Quality score dimensions
    _render_quality_dimensions(result)
    st.markdown("---")

    # Detailed findings
    _render_detailed_findings(result)
    st.markdown("---")

    # Data profile
    _render_data_profile(result)
    st.markdown("---")

    # Schema issues
    _render_schema_issues(result)
    st.markdown("---")

    # Recommendations
    _render_recommendations(result)
    st.markdown("---")

    # Export buttons
    _render_export_buttons(result)


def _render_quality_score_cards(result: ValidationResult):
    score = result.quality_score
    if not score:
        st.warning("No quality score available.")
        return

    cols = st.columns(4)
    cards = [
        ("Overall Score", f"{score.overall:.1f}", score.traffic_light),
        ("Errors", str(result.total_errors), "red" if result.total_errors > 0 else "green"),
        (
            "Warnings",
            str(result.total_warnings),
            "yellow" if result.total_warnings > 0 else "green",
        ),
        ("Info", str(result.total_info), "green"),
    ]
    for col, (label, value, color) in zip(cols, cards, strict=False):
        bg = TRAFFIC_COLORS.get(color, "#6c757d")
        col.markdown(
            f"""
            <div style="background:#f8f9fa;border-left:4px solid {bg};padding:12px;border-radius:4px;">
                <div style="font-size:0.8em;color:#6c757d;">{label}</div>
                <div style="font-size:1.8em;font-weight:bold;color:{bg};">{value}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    cols2 = st.columns(3)
    cards2 = [
        ("Rows", f"{result.profile.row_count:,}"),
        ("Columns", f"{result.profile.column_count}"),
        ("Completeness", f"{result.profile.overall_completeness:.1f}%"),
    ]
    for col, (label, value) in zip(cols2, cards2, strict=False):
        col.markdown(
            f"""
            <div style="background:#f8f9fa;padding:10px;border-radius:4px;">
                <div style="font-size:0.8em;color:#6c757d;">{label}</div>
                <div style="font-size:1.4em;font-weight:bold;">{value}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _render_findings_summary(result: ValidationResult):
    st.markdown("### Findings Summary")

    findings = result.all_findings
    if not findings:
        st.success("No findings — all checks passed!")
        return

    # By severity
    sev_counts = {"error": 0, "warning": 0, "info": 0}
    for f in findings:
        sev = f.get("severity", "info")
        sev_counts[sev] = sev_counts.get(sev, 0) + 1

    # By category
    cat_counts = {}
    for f in findings:
        cat = f.get("category", "unknown")
        cat_counts[cat] = cat_counts.get(cat, 0) + 1

    col1, col2 = st.columns(2)

    with col1:
        fig = go.Figure(
            data=[
                go.Bar(
                    x=list(sev_counts.keys()),
                    y=list(sev_counts.values()),
                    marker_color=[
                        TRAFFIC_COLORS["red"],
                        TRAFFIC_COLORS["yellow"],
                        TRAFFIC_COLORS["green"],
                    ],
                )
            ]
        )
        fig.update_layout(
            title="Findings by Severity", xaxis_title="Severity", yaxis_title="Count", height=300
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig2 = go.Figure(
            data=[
                go.Bar(
                    x=list(cat_counts.keys()),
                    y=list(cat_counts.values()),
                    marker_color="#007bff",
                )
            ]
        )
        fig2.update_layout(
            title="Findings by Category", xaxis_title="Category", yaxis_title="Count", height=300
        )
        st.plotly_chart(fig2, use_container_width=True)


def _render_quality_dimensions(result: ValidationResult):
    st.markdown("### Quality Score Dimensions")
    score = result.quality_score
    if not score:
        return

    dimensions = {
        "Completeness": score.completeness,
        "Accuracy": score.accuracy,
        "Consistency": score.consistency,
        "Validity": score.validity,
        "Uniqueness": score.uniqueness,
        "Integrity": score.integrity,
    }

    fig = go.Figure(
        data=go.Bar(
            x=list(dimensions.keys()),
            y=list(dimensions.values()),
            marker_color=[
                (
                    TRAFFIC_COLORS["green"]
                    if v >= 85
                    else TRAFFIC_COLORS["yellow"] if v >= 60 else TRAFFIC_COLORS["red"]
                )
                for v in dimensions.values()
            ],
        )
    )
    fig.update_layout(
        title="Quality Score by Dimension",
        xaxis_title="Dimension",
        yaxis_title="Score (0-100)",
        yaxis=dict(range=[0, 100]),
        height=350,
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_detailed_findings(result: ValidationResult):
    st.markdown("### Detailed Findings")
    findings = result.all_findings
    if not findings:
        st.success("No findings to display.")
        return

    # Filter by severity
    severity_filter = st.multiselect(
        "Filter by severity",
        options=["error", "warning", "info"],
        default=["error", "warning"],
        key="validation_severity_filter",
    )

    filtered = (
        [f for f in findings if f.get("severity") in severity_filter]
        if severity_filter
        else findings
    )

    rows = []
    for f in filtered:
        rows.append(
            {
                "Rule": f.get("rule_name", ""),
                "Category": f.get("category", ""),
                "Severity": f.get("severity", "").upper(),
                "Column": f.get("column", ""),
                "Affected Rows": f.get("affected_rows", 0),
                "Message": f.get("message", ""),
                "Suggested Fix": f.get("suggested_fix", ""),
            }
        )

    df_findings = pd.DataFrame(rows)
    st.dataframe(df_findings, use_container_width=True, height=400)


def _render_data_profile(result: ValidationResult):
    st.markdown("### Data Profile")
    profile = result.profile

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Rows", f"{profile.row_count:,}")
    col2.metric("Total Columns", profile.column_count)
    col3.metric("Duplicate %", f"{profile.duplicate_percentage:.1f}%")

    # Column profiles table
    col_data = []
    for cp in profile.column_profiles:
        col_data.append(
            {
                "Column": cp.name,
                "Type": cp.dtype,
                "Null %": f"{cp.null_percentage:.1f}%",
                "Unique": cp.unique_count,
                "Min": f"{cp.min_value:.2f}" if cp.min_value is not None else "-",
                "Max": f"{cp.max_value:.2f}" if cp.max_value is not None else "-",
                "Mean": f"{cp.mean_value:.2f}" if cp.mean_value is not None else "-",
            }
        )

    st.dataframe(pd.DataFrame(col_data), use_container_width=True)


def _render_schema_issues(result: ValidationResult):
    schema = result.schema_result
    if not schema.issues:
        st.markdown("### Schema Validation")
        st.success("Schema validation passed — no issues found.")
        return

    st.markdown("### Schema Validation Issues")
    rows = []
    for issue in schema.issues:
        rows.append(
            {
                "Rule": issue.rule_name,
                "Severity": issue.severity.upper(),
                "Column": issue.column or "-",
                "Message": issue.message,
                "Fix": issue.suggested_fix or "-",
            }
        )
    st.dataframe(pd.DataFrame(rows), use_container_width=True)


def _render_recommendations(result: ValidationResult):
    st.markdown("### Recommendations")
    recs = []
    for f in result.all_findings:
        fix = f.get("suggested_fix")
        if fix:
            recs.append(
                {
                    "Rule": f.get("rule_name", ""),
                    "Severity": f.get("severity", "").upper(),
                    "Recommendation": fix,
                    "Affected Rows": f.get("affected_rows", 0),
                }
            )

    if not recs:
        st.info("No recommendations — all checks passed.")
        return

    for rec in recs[:20]:
        sev = rec["Severity"]
        color = TRAFFIC_COLORS.get(
            "red" if sev == "ERROR" else "yellow" if sev == "WARNING" else "green", "#6c757d"
        )
        st.markdown(
            f"""
            <div style="border-left:3px solid {color};padding:8px 12px;margin-bottom:6px;background:#f8f9fa;">
                <strong>[{sev}] {rec['Rule']}</strong>: {rec['Recommendation']}
                <em style="color:#6c757d;"> ({rec['Affected Rows']} rows affected)</em>
            </div>
            """,
            unsafe_allow_html=True,
        )
    if len(recs) > 20:
        st.info(f"... and {len(recs) - 20} more recommendations.")


def _render_export_buttons(result: ValidationResult):
    st.markdown("### Export Report")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Export CSV", key="export_csv"):
            csv_content = ValidationReportGenerator.export_csv(result)
            st.download_button(
                label="Download CSV",
                data=csv_content,
                file_name=f"validation_report_{result.dataset_name}.csv",
                mime="text/csv",
            )

    with col2:
        if st.button("Export Excel", key="export_excel"):
            import os
            import tempfile

            with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
                ValidationReportGenerator.export_excel(result, tmp.name)
                with open(tmp.name, "rb") as f:
                    data = f.read()
                os.unlink(tmp.name)
            st.download_button(
                label="Download Excel",
                data=data,
                file_name=f"validation_report_{result.dataset_name}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

    with col3:
        if st.button("Export PDF", key="export_pdf"):
            import os
            import tempfile

            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                ValidationReportGenerator.export_pdf(result, tmp.name)
                with open(tmp.name, "rb") as f:
                    data = f.read()
                os.unlink(tmp.name)
            st.download_button(
                label="Download PDF",
                data=data,
                file_name=f"validation_report_{result.dataset_name}.pdf",
                mime="application/pdf",
            )


def render_approval_section(
    result: ValidationResult, session_key: str = "validation_result"
) -> bool:
    """Render the approval workflow section. Returns True if approved."""
    if result.can_proceed_to_etl:
        st.success(f"Validation {result.status.value.replace('_', ' ')} — ETL can proceed.")
        return True

    st.warning(
        f"Validation {result.status.value} with {result.total_errors} errors. "
        f"ETL is blocked. An authorized user must approve to proceed."
    )

    with st.expander("Approval Workflow", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            approver = st.text_input("Approver Name", key=f"{session_key}_approver")
            role = st.selectbox(
                "Role",
                options=["reviewer", "supervisor", "data_manager", "statistician", "administrator"],
                key=f"{session_key}_role",
            )
            comments = st.text_area("Comments", key=f"{session_key}_comments")

        with col2:
            st.markdown("**Validation Summary**")
            st.write(f"Status: {result.status.value}")
            st.write(f"Errors: {result.total_errors}")
            st.write(f"Warnings: {result.total_warnings}")
            if result.quality_score:
                st.write(
                    f"Quality Score: {result.quality_score.overall:.1f} ({result.quality_score.traffic_light})"
                )

        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("Approve & Proceed to ETL", type="primary", key=f"{session_key}_approve"):
                if not approver:
                    st.error("Please enter approver name.")
                    return False
                from validation.approval import ApprovalWorkflow

                ApprovalWorkflow.approve(result, approver, role, comments)
                st.success("Validation approved! ETL can now proceed.")
                st.rerun()
                return True

        with col_btn2:
            if st.button("Reject", key=f"{session_key}_reject"):
                if not approver:
                    st.error("Please enter approver name.")
                    return False
                from validation.approval import ApprovalWorkflow

                ApprovalWorkflow.reject(result, approver, role, comments)
                st.error("Validation rejected. ETL remains blocked.")
                st.rerun()

    return False
