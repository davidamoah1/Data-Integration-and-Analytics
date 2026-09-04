"""Workflow Report PDF Generator for Data-to-Decision Pipeline.

Generates a clean, publication-grade, professional PDF report containing:
- Executive Summary & Key Highlights
- Data Hygiene & Quality Assessment (with audit of cleaning transformations)
- Key Performance Indicators (KPI cards in strict grid)
- Visualizations & Data Patterns (with rendered horizontal bar charts)
- Statistical Insights & Anomalies (with color-coded badges)
- Actionable Strategic Recommendations (numbered and sanitized)
using fpdf2.
"""

from __future__ import annotations

import io
from datetime import datetime, timezone
from typing import Any
from fpdf import FPDF


def _sanitize(text: Any) -> str:
    """Sanitize text for standard Latin-1 FPDF fonts and eliminate all mojibake."""
    if text is None:
        return ""
    s = str(text)

    # 1. Clean legacy mojibake sequences first
    mojibake_map = {
        "â€”": " - ",
        "âEUR\"": " - ",
        "âEUR": " - ",
        "â€“": " - ",
        "â€¦": "...",
        "â€¢": "* ",
        "â€˜": "'",
        "â€™": "'",
        "â€œ": '"',
        "â€ ": '"',
        "âš ï¸ ": "[!] ",
        "âš ": "[!] ",
        "âœ…": "[OK] ",
        "â†’": " -> ",
        "â†": " <- ",
        "â”‚": "|",
        "â”€": "-",
        "â–¼": "v",
    }
    for old, new in mojibake_map.items():
        s = s.replace(old, new)

    # 2. Standard Unicode punctuation & symbols mapping to Latin-1
    unicode_map = {
        "\u2014": " - ",  # em dash
        "\u2013": " - ",  # en dash
        "\u2018": "'",    # left single quote
        "\u2019": "'",    # right single quote
        "\u201c": '"',    # left double quote
        "\u201d": '"',    # right double quote
        "\u2026": "...",  # ellipsis
        "\u00a0": " ",    # non-breaking space
        "\u2022": "* ",   # bullet
        "\u25cf": "* ",
        "\u2713": "[OK]", # checkmark
        "\u2714": "[OK]",
        "\u2192": "->",
        "\u2190": "<-",
        "\u20ac": "EUR",  # only converted after mojibake cleaned
        "\u00a3": "GBP",
        "\u00a5": "JPY",
    }
    for old, new in unicode_map.items():
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
            self.cell(120, 6, f"DataFlow Intelligence  |  {self.doc_title[:50]}", border=0)
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
        self.cell(120, 5, "DataFlow Intelligence Platform  |  Confidential Decision Report", border=0)
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
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(pw - 12, 7, _sanitize(title), border=0, new_x="LMARGIN", new_y="NEXT")

    pdf.set_xy(pdf.l_margin + 6, pdf.get_y() + 1)
    pdf.set_font("Helvetica", "", 9.5)
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
        pdf.set_font("Helvetica", "", 7.5)
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

        # Dimensions row (clean separated cards, no overlapping text!)
        if isinstance(quality.get("score"), dict):
            q_score = quality["score"]
            dims = [
                ("Completeness", q_score.get("completeness", 0)),
                ("Validity", q_score.get("validity", 0)),
                ("Uniqueness", q_score.get("uniqueness", 0)),
                ("Consistency", q_score.get("consistency", 0)),
                ("Timeliness", q_score.get("timeliness", 0)),
            ]
            dim_gap = 3
            dim_w = (pw - (len(dims) - 1) * dim_gap) / len(dims)
            d_y = pdf.get_y()
            dim_h = 16

            for i, (d_lbl, d_val) in enumerate(dims):
                dx = pdf.l_margin + i * (dim_w + dim_gap)

                # Background card
                pdf.set_fill_color(248, 250, 252)
                pdf.set_draw_color(226, 232, 240)
                pdf.set_line_width(0.3)
                pdf.rect(dx, d_y, dim_w, dim_h, style="FD")

                # Top label
                pdf.set_xy(dx, d_y + 2.2)
                pdf.set_font("Helvetica", "", 7.5)
                pdf.set_text_color(100, 116, 139)
                pdf.cell(dim_w, 4, _sanitize(d_lbl), align="C", border=0)

                # Value (properly separated on Y!)
                pdf.set_xy(dx, d_y + 7.5)
                pdf.set_font("Helvetica", "B", 11)
                if d_val >= 80:
                    pdf.set_text_color(22, 101, 52)   # Emerald-700
                elif d_val >= 60:
                    pdf.set_text_color(180, 83, 9)    # Amber-700
                else:
                    pdf.set_text_color(185, 28, 28)   # Red-700
                pdf.cell(dim_w, 6, f"{d_val:.0f}%", align="C", border=0)

            pdf.set_xy(pdf.l_margin, d_y + dim_h + 5)

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
    cards_per_row = 3
    card_gap = 3
    card_w = (pw - (cards_per_row - 1) * card_gap) / cards_per_row
    card_h = 19
    start_y = pdf.get_y()

    # Precise mathematical grid placement (no staggered / jagged heights!)
    for i, kpi in enumerate(kpi_list[:6]):
        row_idx = i // cards_per_row
        col_idx = i % cards_per_row
        cx = pdf.l_margin + col_idx * (card_w + card_gap)
        cy = start_y + row_idx * (card_h + card_gap)

        pdf.set_fill_color(248, 250, 252)
        pdf.set_draw_color(226, 232, 240)
        pdf.set_line_width(0.3)
        pdf.rect(cx, cy, card_w, card_h, style="FD")

        # Top Accent indicator (subtle 1.2mm navy stripe)
        pdf.set_fill_color(15, 52, 96)
        pdf.rect(cx, cy, card_w, 1.2, style="F")

        # Label
        pdf.set_xy(cx + 3, cy + 2.5)
        pdf.set_font("Helvetica", "", 7.5)
        pdf.set_text_color(100, 116, 139)
        pdf.cell(card_w - 6, 4, _sanitize(kpi.get("label", "Metric")), border=0)

        # Value
        pdf.set_xy(cx + 3, cy + 7.5)
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(15, 52, 96)
        val_str = f"{kpi.get('value', 0)}{kpi.get('unit', '')}"
        pdf.cell(card_w - 6, 6, _sanitize(val_str), border=0)

        # Comparison / sub-label
        if kpi.get("comparison_label"):
            pdf.set_xy(cx + 3, cy + 14)
            pdf.set_font("Helvetica", "", 7)
            pdf.set_text_color(100, 116, 139)
            pdf.cell(card_w - 6, 3.5, _sanitize(kpi.get("comparison_label")), border=0)

    num_rows = (len(kpi_list[:6]) + cards_per_row - 1) // cards_per_row
    pdf.set_xy(pdf.l_margin, start_y + num_rows * (card_h + card_gap) + 5)

    # --- SECTION 4: VISUALIZATIONS & CHARTS (WITH RENDERED VECTOR BAR CHARTS) ---
    if report_config.get("include_visualizations", True):
        charts = auto_dash.get("charts") or dashboard.get("recommended_charts") or []
        if charts:
            _render_section_title(pdf, pw, "4. Key Visualizations & Analytics")

            for c in charts[:4]:
                c_title = c.get("title") or "Chart Analysis"
                c_type = (c.get("chart_type") or c.get("type") or "Chart").replace("_", " ").upper()
                c_reason = c.get("reason") or c.get("reasoning") or ""
                data_items = c.get("data") or []

                has_plot_data = isinstance(data_items, list) and len(data_items) > 0
                plot_items = data_items[:5] if has_plot_data else []
                card_h = 56 if plot_items else 24

                # Strictly check page break before drawing card so it never splits across pages!
                if pdf.get_y() + card_h > pdf.h - pdf.b_margin - 8:
                    pdf.add_page()

                card_y = pdf.get_y()

                # Card container
                pdf.set_fill_color(255, 255, 255)
                pdf.set_draw_color(226, 232, 240)
                pdf.set_line_width(0.3)
                pdf.rect(pdf.l_margin, card_y, pw, card_h, style="FD")

                # Card Header Bar
                pdf.set_fill_color(248, 250, 252)
                pdf.rect(pdf.l_margin, card_y, pw, 8, style="FD")

                # Badge
                badge_text = f" {c_type} "
                pdf.set_font("Helvetica", "B", 7)
                badge_w = pdf.get_string_width(badge_text) + 2
                pdf.set_fill_color(15, 52, 96)
                pdf.rect(pdf.l_margin + 3, card_y + 1.8, badge_w, 4.4, style="F")
                pdf.set_xy(pdf.l_margin + 3, card_y + 1.8)
                pdf.set_text_color(255, 255, 255)
                pdf.cell(badge_w, 4.4, badge_text, align="C")

                # Title
                pdf.set_xy(pdf.l_margin + badge_w + 6, card_y + 1.5)
                pdf.set_font("Helvetica", "B", 9)
                pdf.set_text_color(15, 23, 42)
                pdf.cell(pw - badge_w - 10, 5, _sanitize(c_title[:60]), border=0)

                # Draw crisp vector bars if data is available
                if plot_items:
                    numeric_vals = []
                    for item in plot_items:
                        val = item.get("y") if item.get("y") is not None else item.get("value", 0)
                        try:
                            numeric_vals.append(float(val))
                        except (ValueError, TypeError):
                            numeric_vals.append(0.0)

                    max_val = max(numeric_vals) if numeric_vals and max(numeric_vals) > 0 else 1.0

                    bar_start_y = card_y + 10
                    bar_label_w = 42
                    bar_area_w = pw - bar_label_w - 28
                    bar_h_item = 4.0
                    bar_gap = 1.8

                    # Axis baseline
                    pdf.set_draw_color(203, 213, 225)
                    pdf.set_line_width(0.3)
                    pdf.line(
                        pdf.l_margin + bar_label_w + 2,
                        bar_start_y,
                        pdf.l_margin + bar_label_w + 2,
                        bar_start_y + len(plot_items) * (bar_h_item + bar_gap),
                    )

                    for idx, item in enumerate(plot_items):
                        raw_label = (
                            item.get("x")
                            if item.get("x") is not None
                            else item.get("category") or item.get("name") or f"Item {idx + 1}"
                        )
                        label_str = _sanitize(str(raw_label))[:18]
                        val_num = numeric_vals[idx]
                        cur_by = bar_start_y + idx * (bar_h_item + bar_gap)

                        # Category Label (aligned right)
                        pdf.set_xy(pdf.l_margin + 2, cur_by)
                        pdf.set_font("Helvetica", "", 7.5)
                        pdf.set_text_color(71, 85, 105)
                        pdf.cell(bar_label_w, bar_h_item, label_str, align="R", border=0)

                        # Bar rect
                        bar_len = max(1.5, (val_num / max_val) * bar_area_w)
                        pdf.set_fill_color(37, 99, 235)  # Tech Blue #2563EB
                        pdf.rect(pdf.l_margin + bar_label_w + 3, cur_by + 0.5, bar_len, bar_h_item - 1.0, style="F")

                        # Value text
                        pdf.set_xy(pdf.l_margin + bar_label_w + 4 + bar_len, cur_by)
                        pdf.set_font("Helvetica", "B", 7)
                        pdf.set_text_color(15, 23, 42)
                        val_display = f"{val_num:,.1f}" if val_num % 1 != 0 else f"{int(val_num):,}"
                        pdf.cell(20, bar_h_item, val_display, border=0)

                    # Subtle divider
                    divider_y = bar_start_y + len(plot_items) * (bar_h_item + bar_gap) + 1.5
                    pdf.set_draw_color(241, 245, 249)
                    pdf.line(pdf.l_margin + 4, divider_y, pdf.l_margin + pw - 4, divider_y)

                    # Insight Note at the bottom of the card with multi_cell wrapping
                    pdf.set_xy(pdf.l_margin + 4, divider_y + 1.2)
                    pdf.set_font("Helvetica", "I", 7.5)
                    pdf.set_text_color(100, 116, 139)
                    insight_snip = f"Insight: {c_reason}" if c_reason else f"Visual distribution across top categories for {c_title}."
                    pdf.multi_cell(pw - 8, 3.6, _sanitize(insight_snip))
                else:
                    pdf.set_xy(pdf.l_margin + 4, card_y + 10)
                    pdf.set_font("Helvetica", "", 8)
                    pdf.set_text_color(71, 85, 105)
                    pdf.multi_cell(pw - 8, 4.5, _sanitize(f"Insight & Justification: {c_reason}"))

                pdf.set_xy(pdf.l_margin, card_y + card_h + 4)
            pdf.ln(2)

    # --- SECTION 5: STATISTICAL INSIGHTS ---
    insights = insights_data.get("insights") or auto_dash.get("insights") or []
    if insights:
        if pdf.get_y() + 30 > pdf.h - pdf.b_margin - 8:
            pdf.add_page()
        _render_section_title(pdf, pw, "5. Automated Statistical Insights")

        for ins in insights[:5]:
            if pdf.get_y() + 16 > pdf.h - pdf.b_margin - 8:
                pdf.add_page()

            i_title = ins.get("title") or "Finding"
            i_desc = ins.get("description") or ""
            i_type = (ins.get("type") or ins.get("insight_type") or "Info").upper()

            # Accent color
            if "ANOMALY" in i_type or "OUTLIER" in i_type:
                badge_bg = (185, 28, 28)  # Red
            elif "QUALITY" in i_type or "WARNING" in i_type:
                badge_bg = (217, 119, 6)   # Amber
            else:
                badge_bg = (15, 52, 96)   # Navy

            cur_iy = pdf.get_y()
            pdf.set_fill_color(*badge_bg)
            pdf.rect(pdf.l_margin, cur_iy + 0.5, 1.5, 4.5, style="F")

            pdf.set_xy(pdf.l_margin + 3, cur_iy)
            pdf.set_font("Helvetica", "B", 8.5)
            pdf.set_text_color(15, 23, 42)
            pdf.cell(0, 5, _sanitize(f"[{i_type}] {i_title}"), new_x="LMARGIN", new_y="NEXT")

            if i_desc:
                pdf.set_font("Helvetica", "", 8)
                pdf.set_text_color(71, 85, 105)
                pdf.set_x(pdf.l_margin + 3)
                pdf.multi_cell(pw - 3, 4, _sanitize(i_desc))
            pdf.ln(2)
        pdf.ln(2)

    # --- SECTION 6: RECOMMENDATIONS ---
    if report_config.get("include_recommendations", True):
        recs = quality.get("recommendations") or auto_dash.get("recommendations") or []
        if recs:
            if pdf.get_y() + 30 > pdf.h - pdf.b_margin - 8:
                pdf.add_page()
            _render_section_title(pdf, pw, "6. Strategic Recommendations")

            for i, rec in enumerate(recs[:6]):
                if pdf.get_y() + 15 > pdf.h - pdf.b_margin - 8:
                    pdf.add_page()

                clean_rec = _sanitize(str(rec))
                rec_y = pdf.get_y()

                # Number badge indicator
                pdf.set_fill_color(241, 245, 249)
                pdf.set_draw_color(203, 213, 225)
                pdf.set_line_width(0.3)
                pdf.rect(pdf.l_margin, rec_y + 0.5, 5, 5, style="FD")
                pdf.set_xy(pdf.l_margin, rec_y + 0.5)
                pdf.set_font("Helvetica", "B", 7.5)
                pdf.set_text_color(15, 52, 96)
                pdf.cell(5, 5, str(i + 1), align="C")

                # Recommendation content
                pdf.set_xy(pdf.l_margin + 7, rec_y)
                pdf.set_font("Helvetica", "", 8.5)
                pdf.set_text_color(51, 65, 85)
                pdf.multi_cell(pw - 7, 4.5, clean_rec)
                pdf.ln(2)

    return bytes(pdf.output())


def _render_section_title(pdf: FPDF, pw: float, title: str) -> None:
    """Helper to render uniform section dividers with page break protection."""
    if pdf.get_y() > pdf.h - 45:
        pdf.add_page()

    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(15, 52, 96)  # Navy
    pdf.cell(0, 7, _sanitize(title), new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(15, 52, 96)
    pdf.set_line_width(0.4)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.l_margin + pw, pdf.get_y())
    pdf.ln(3)
