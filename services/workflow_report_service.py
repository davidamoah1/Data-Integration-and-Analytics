"""Workflow Report PDF Generator for Data-to-Decision Pipeline.

Generates a clean, publication-grade, professional PDF report containing:
- Executive Summary & Key Highlights
- Data Hygiene & Quality Assessment (with audit of cleaning transformations)
- Key Performance Indicators (KPI cards)
- Visualizations & Data Patterns
- Statistical Insights & Anomalies
- Actionable Strategic Recommendations
using fpdf2.
"""

from __future__ import annotations

import io
from datetime import datetime, timezone
from typing import Any
from fpdf import FPDF


def _sanitize(text: Any) -> str:
    """Sanitize text for standard Latin-1 FPDF fonts."""
    if text is None:
        return ""
    s = str(text)
    replacements = {
        "\u2014": "-",  # em dash
        "\u2013": "-",  # en dash
        "\u2018": "'",  # left single quote
        "\u2019": "'",  # right single quote
        "\u201c": '"',  # left double quote
        "\u201d": '"',  # right double quote
        "\u2026": "...",  # ellipsis
        "\u00a0": " ",  # non-breaking space
        "\u2022": "*",  # bullet
        "\u2713": "[v]",  # checkmark
        "\u2714": "[v]",
        "\u2192": "->",
        "\u25cf": "*",
        "\u20ac": "EUR",
        "\u00a3": "GBP",
    }
    for old, new in replacements.items():
        s = s.replace(old, new)
    return s.encode("latin-1", errors="replace").decode("latin-1")


class WorkflowReportPDF(FPDF):
    """Custom FPDF document with running header and footer for workflow reports."""

    def __init__(self, doc_title: str = "Data-to-Decision Intelligence Report", *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.doc_title = _sanitize(doc_title)
        self.gen_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    def header(self) -> None:
        if self.page_no() > 1:
            self.set_font("Helvetica", "B", 8)
            self.set_text_color(100, 116, 139)  # Slate-500
            self.cell(0, 6, f"DataFlow Intelligence  |  {self.doc_title[:60]}", border=0)
            self.set_font("Helvetica", "", 8)
            self.cell(0, 6, self.gen_time, border=0, align="R", new_x="LMARGIN", new_y="NEXT")
            self.set_draw_color(226, 232, 240)  # Slate-200
            self.set_line_width(0.3)
            self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
            self.ln(4)

    def footer(self) -> None:
        self.set_y(-12)
        self.set_draw_color(226, 232, 240)
        self.set_line_width(0.3)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(2)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(148, 163, 184)  # Slate-400
        self.cell(0, 5, "DataFlow Intelligence Platform  |  Confidential Decision Report", border=0)
        page_str = f"Page {self.page_no()} of {{nb}}"
        self.cell(0, 5, page_str, border=0, align="R")


def generate_workflow_pdf_report(
    workflow_state_dict: dict[str, Any],
    report_config: dict[str, Any],
    current_user_name: str = "Administrator",
) -> bytes:
    """Generate a clean, publication-grade executive report for a dataset workflow."""
    title = report_config.get("title") or f"{workflow_state_dict.get('dataset_name', 'Dataset')} Analysis Report"
    pdf = WorkflowReportPDF(doc_title=title, orientation="P", unit="mm", format="A4")
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=14)
    pdf.set_margins(14, 14, 14)
    pdf.add_page()

    pw = pdf.w - pdf.l_margin - pdf.r_margin  # 182 mm

    # Extract workflow stages
    stages = workflow_state_dict.get("stages", {})
    profile = stages.get("profiled", {}).get("result") or {}
    quality = stages.get("quality_checked", {}).get("result") or {}
    industry_data = stages.get("industry_identified", {}).get("result") or {}
    insights_data = stages.get("insights_generated", {}).get("result") or {}
    dashboard = stages.get("dashboard_ready", {}).get("result") or {}
    auto_dash = dashboard.get("auto_dashboard") or {}
    transformations = workflow_state_dict.get("transformations", [])

    dataset_name = workflow_state_dict.get("dataset_name", "Uploaded Dataset")
    industry_name = (industry_data.get("industry") or "General").capitalize()
    quality_score = quality.get("score", {}).get("overall") if isinstance(quality.get("score"), dict) else profile.get("overall_quality_score", 0)
    quality_grade = quality.get("score", {}).get("grade", "A") if isinstance(quality.get("score"), dict) else "N/A"

    # --- COVER / HEADER BANNER ---
    pdf.set_fill_color(15, 52, 96)  # Deep Navy #0F3460
    pdf.rect(pdf.l_margin, pdf.get_y(), pw, 32, style="F")

    curr_y = pdf.get_y()
    pdf.set_xy(pdf.l_margin + 6, curr_y + 4)
    pdf.set_font("Helvetica", "B", 17)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(pw - 12, 7, _sanitize(title), border=0, new_x="LMARGIN", new_y="NEXT")

    pdf.set_xy(pdf.l_margin + 6, pdf.get_y() + 1)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(203, 213, 225)  # Slate-300
    sub_text = f"Dataset: {dataset_name}   |   Industry: {industry_name}   |   Generated: {datetime.now(timezone.utc).strftime('%B %d, %Y')}"
    pdf.cell(pw - 12, 6, _sanitize(sub_text), border=0)

    pdf.set_xy(pdf.l_margin, curr_y + 36)
    pdf.set_text_color(30, 41, 59)

    # --- METADATA STRIP ---
    pdf.set_fill_color(248, 250, 252)  # Slate-50
    pdf.set_draw_color(226, 232, 240)  # Slate-200
    pdf.set_line_width(0.3)
    meta_h = 16
    pdf.rect(pdf.l_margin, pdf.get_y(), pw, meta_h, style="FD")

    col_w = pw / 4
    meta_items = [
        ("Total Rows", f"{profile.get('row_count', 0):,}"),
        ("Columns", str(profile.get("column_count", 0))),
        ("Data Quality", f"{quality_score:.0f}/100 ({quality_grade})"),
        ("Prepared For", report_config.get("organization") or "Executive Review"),
    ]

    m_y = pdf.get_y()
    for i, (m_lbl, m_val) in enumerate(meta_items):
        bx = pdf.l_margin + i * col_w
        pdf.set_xy(bx, m_y + 2.5)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(100, 116, 139)
        pdf.cell(col_w, 4, _sanitize(m_lbl), align="C")
        pdf.set_xy(bx, m_y + 7.5)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(col_w, 5, _sanitize(m_val), align="C")

    pdf.set_xy(pdf.l_margin, m_y + meta_h + 6)

    # --- SECTION 1: EXECUTIVE SUMMARY ---
    if report_config.get("include_executive_summary", True):
        _render_section_title(pdf, pw, "1. Executive Summary")
        pdf.set_font("Helvetica", "", 9.5)
        pdf.set_text_color(51, 65, 85)

        exec_summary = (
            insights_data.get("executive_summary")
            or quality.get("summary")
            or f"This report synthesizes the end-to-end intelligence evaluation of {dataset_name}. "
               f"The dataset comprises {profile.get('row_count', 0):,} records across {profile.get('column_count', 0)} attributes "
               f"in the {industry_name} sector, achieving an overall hygiene and validity rating of {quality_score:.0f}/100."
        )
        pdf.multi_cell(pw, 5, _sanitize(exec_summary))
        pdf.ln(4)

    # --- SECTION 2: DATA HYGIENE & CLEANING AUDIT ---
    if report_config.get("include_data_quality", True):
        _render_section_title(pdf, pw, "2. Data Quality & Cleaning Audit")

        # Dimensions row
        if isinstance(quality.get("score"), dict):
            q_score = quality["score"]
            dims = [
                ("Completeness", q_score.get("completeness", 0)),
                ("Validity", q_score.get("validity", 0)),
                ("Uniqueness", q_score.get("uniqueness", 0)),
                ("Consistency", q_score.get("consistency", 0)),
                ("Timeliness", q_score.get("timeliness", 0)),
            ]
            dim_w = pw / len(dims)
            d_y = pdf.get_y()
            pdf.set_fill_color(241, 245, 249)
            pdf.rect(pdf.l_margin, d_y, pw, 14, style="F")

            for i, (d_lbl, d_val) in enumerate(dims):
                dx = pdf.l_margin + i * dim_w
                pdf.set_xy(dx, d_y + 1.5)
                pdf.set_font("Helvetica", "", 7.5)
                pdf.set_text_color(100, 116, 139)
                pdf.cell(dim_w, 4, _sanitize(d_lbl), align="C")
                if d_val >= 80:
                    pdf.set_text_color(22, 101, 52)
                elif d_val >= 60:
                    pdf.set_text_color(180, 83, 9)
                else:
                    pdf.set_text_color(185, 28, 28)
                pdf.cell(dim_w, 5, f"{d_val:.0f}%", align="C")

            pdf.set_xy(pdf.l_margin, d_y + 18)

        # Cleaning actions audit
        active_transformations = [t for t in transformations if not t.get("undone")]
        if active_transformations:
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(15, 23, 42)
            pdf.cell(0, 5, f"Applied Cleaning Transformations ({len(active_transformations)})", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(1)

            pdf.set_font("Helvetica", "B", 8)
            pdf.set_fill_color(226, 232, 240)
            pdf.cell(40, 5, "Action", border=1, fill=True)
            pdf.cell(30, 5, "Column", border=1, fill=True)
            pdf.cell(85, 5, "Description", border=1, fill=True)
            pdf.cell(27, 5, "Rows Affected", border=1, fill=True, align="R", new_x="LMARGIN", new_y="NEXT")

            pdf.set_font("Helvetica", "", 8)
            for t in active_transformations[:8]:
                pdf.cell(40, 5, _sanitize(t.get("action", "")), border=1)
                pdf.cell(30, 5, _sanitize(t.get("column") or "-"), border=1)
                pdf.cell(85, 5, _sanitize(t.get("description", "")[:50]), border=1)
                pdf.cell(27, 5, f"{t.get('affected_rows', 0):,}", border=1, align="R", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(4)
        else:
            pdf.set_font("Helvetica", "I", 8.5)
            pdf.set_text_color(100, 116, 139)
            pdf.cell(0, 5, "No manual cleaning transformations were required for this dataset.", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(3)

    # --- SECTION 3: KEY PERFORMANCE INDICATORS ---
    kpi_list = auto_dash.get("kpis") or []
    if not kpi_list:
        # Fallback to basic metrics from profile
        kpi_list = [
            {"label": "Record Volume", "value": f"{profile.get('row_count', 0):,}", "unit": " rows"},
            {"label": "Data Density", "value": f"{100 - profile.get('missing_percentage', 0):.1f}", "unit": "%"},
            {"label": "Unique Ratio", "value": f"{100 - profile.get('duplicate_percentage', 0):.1f}", "unit": "%"},
            {"label": "Total Columns", "value": str(profile.get("column_count", 0)), "unit": " fields"},
        ]

    _render_section_title(pdf, pw, "3. Key Performance Indicators")
    card_w = (pw - 6) / 3
    card_h = 18

    for i, kpi in enumerate(kpi_list[:6]):
        if i > 0 and i % 3 == 0:
            pdf.ln(card_h + 3)

        row_idx = i // 3
        col_idx = i % 3
        cx = pdf.l_margin + col_idx * (card_w + 3)
        cy = pdf.get_y()

        pdf.set_fill_color(248, 250, 252)
        pdf.set_draw_color(203, 213, 225)
        pdf.rect(cx, cy, card_w, card_h, style="FD")

        pdf.set_xy(cx + 3, cy + 2)
        pdf.set_font("Helvetica", "", 7.5)
        pdf.set_text_color(100, 116, 139)
        pdf.cell(card_w - 6, 4, _sanitize(kpi.get("label", "Metric")), border=0)

        pdf.set_xy(cx + 3, cy + 7)
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(15, 52, 96)
        val_str = f"{kpi.get('value', 0)}{kpi.get('unit', '')}"
        pdf.cell(card_w - 6, 6, _sanitize(val_str), border=0)

        if kpi.get("comparison_label"):
            pdf.set_xy(cx + 3, cy + 13)
            pdf.set_font("Helvetica", "", 7)
            pdf.set_text_color(100, 116, 139)
            pdf.cell(card_w - 6, 3, _sanitize(kpi.get("comparison_label")), border=0)

    pdf.ln(card_h + 6)

    # --- SECTION 4: VISUALIZATIONS & CHARTS ---
    if report_config.get("include_visualizations", True):
        charts = auto_dash.get("charts") or dashboard.get("recommended_charts") or []
        if charts:
            _render_section_title(pdf, pw, "4. Key Visualizations & Analytics")
            for c in charts[:4]:
                c_title = c.get("title") or "Chart Analysis"
                c_type = (c.get("chart_type") or c.get("type") or "Chart").replace("_", " ").title()
                c_reason = c.get("reason") or c.get("reasoning") or ""

                pdf.set_font("Helvetica", "B", 9)
                pdf.set_text_color(15, 52, 96)
                pdf.cell(0, 5, _sanitize(f"[{c_type}] {c_title}"), new_x="LMARGIN", new_y="NEXT")

                if c_reason:
                    pdf.set_font("Helvetica", "", 8.5)
                    pdf.set_text_color(71, 85, 105)
                    pdf.multi_cell(pw, 4.5, _sanitize(f"Insight & Justification: {c_reason}"))
                pdf.ln(2)
            pdf.ln(2)

    # --- SECTION 5: STATISTICAL INSIGHTS ---
    insights = insights_data.get("insights") or auto_dash.get("insights") or []
    if insights:
        _render_section_title(pdf, pw, "5. Automated Statistical Insights")
        for ins in insights[:5]:
            i_title = ins.get("title") or "Finding"
            i_desc = ins.get("description") or ""
            i_type = (ins.get("type") or ins.get("insight_type") or "Info").upper()

            pdf.set_font("Helvetica", "B", 8.5)
            pdf.set_text_color(15, 23, 42)
            pdf.cell(0, 4.5, _sanitize(f"* [{i_type}] {i_title}"), new_x="LMARGIN", new_y="NEXT")

            if i_desc:
                pdf.set_font("Helvetica", "", 8)
                pdf.set_text_color(71, 85, 105)
                pdf.multi_cell(pw, 4, _sanitize(f"   {i_desc}"))
            pdf.ln(1.5)
        pdf.ln(3)

    # --- SECTION 6: RECOMMENDATIONS ---
    if report_config.get("include_recommendations", True):
        recs = quality.get("recommendations") or auto_dash.get("recommendations") or []
        if recs:
            _render_section_title(pdf, pw, "6. Strategic Recommendations")
            pdf.set_font("Helvetica", "", 8.5)
            pdf.set_text_color(51, 65, 85)
            for i, rec in enumerate(recs[:6]):
                pdf.multi_cell(pw, 4.5, _sanitize(f"{i + 1}. {rec}"))
                pdf.ln(1)
            pdf.ln(3)

    return bytes(pdf.output())


def _render_section_title(pdf: FPDF, pw: float, title: str) -> None:
    """Helper to render uniform section dividers."""
    if pdf.get_y() > pdf.h - 40:
        pdf.add_page()

    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(15, 52, 96)  # Navy
    pdf.cell(0, 7, _sanitize(title), new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(15, 52, 96)
    pdf.set_line_width(0.4)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.l_margin + pw, pdf.get_y())
    pdf.ln(3)
