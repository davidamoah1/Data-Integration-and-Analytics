"""Approved Certificate Analytics PDF Report Generator.

Produces a clean, professional, publication-grade PDF report containing
executive KPIs, data quality metrics, and vector bar charts for all breakdowns
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
    }
    for old, new in replacements.items():
        s = s.replace(old, new)
    return s.encode("latin-1", errors="replace").decode("latin-1")


class ApprovedAnalyticsPDF(FPDF):
    """Custom FPDF document with running header and footer."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.doc_title = "Approved Certificate Analytics Report"
        self.gen_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    def header(self) -> None:
        if self.page_no() > 1:
            self.set_font("Helvetica", "B", 8)
            self.set_text_color(100, 116, 139)  # Slate-500
            self.cell(0, 6, "DataFlow Intelligence  |  Approved Certificate Analytics Report", border=0)
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
        self.cell(0, 5, "Official Verification & Audit Report  |  Confidential", border=0)
        page_str = f"Page {self.page_no()} of {{nb}}"
        self.cell(0, 5, page_str, border=0, align="R")


def generate_approved_analytics_pdf(
    summary_data: Any,
    filters: dict[str, Any] | None = None,
    current_user_name: str | None = None,
) -> bytes:
    """Generate a clean, professional, unredundant PDF report with vector bar charts."""
    pdf = ApprovedAnalyticsPDF(orientation="P", unit="mm", format="A4")
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=14)
    pdf.set_margins(14, 14, 14)
    pdf.add_page()

    pw = pdf.w - pdf.l_margin - pdf.r_margin  # 182 mm
    kpis = getattr(summary_data, "kpis", None)
    dq = getattr(summary_data, "data_quality", None)
    total = getattr(summary_data, "total", 0) or (kpis.total_approved if kpis else 0)

    by_name = getattr(summary_data, "by_name", {}) or {}
    by_type = getattr(summary_data, "by_type", {}) or {}
    by_issuer = getattr(summary_data, "by_issuer", {}) or {}
    by_course = getattr(summary_data, "by_course", {}) or {}
    trends = getattr(summary_data, "trends", {}) or {}
    certs_per_person = getattr(summary_data, "certs_per_person", {}) or {}
    recipients = getattr(summary_data, "recipients", []) or []
    insights = getattr(summary_data, "insights", []) or []
    records = getattr(summary_data, "records", []) or []

    # ── Page 1: Header Banner ────────────────────────────────────────────────
    pdf.set_fill_color(30, 41, 59)  # Slate-800
    pdf.rect(pdf.l_margin, pdf.get_y(), pw, 26, "F")

    pdf.set_xy(pdf.l_margin + 6, pdf.get_y() + 4)
    pdf.set_font("Helvetica", "B", 15)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(pw - 50, 7, "Approved Certificate Analytics Report", border=0)

    # Scope badge on top-right of banner
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_fill_color(5, 150, 105)  # Emerald-600
    pdf.cell(38, 6, "  VERIFIED APPROVED", border=0, align="C", fill=True)

    pdf.set_xy(pdf.l_margin + 6, pdf.get_y() + 8)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(203, 213, 225)  # Slate-300
    gen_str = datetime.now(timezone.utc).strftime("%B %d, %Y - %H:%M UTC")
    pdf.cell(pw - 12, 5, f"DataFlow Enterprise Intelligence  |  Audit Date: {gen_str}", border=0)

    pdf.set_y(pdf.get_y() + 16)
    pdf.ln(3)

    # ── Filters Pill Box ──────────────────────────────────────────────────────
    filter_items = []
    if filters:
        for k, v in filters.items():
            if v is not None and v != "":
                clean_k = k.replace("_", " ").title()
                filter_items.append(f"{clean_k}: {v}")

    filter_text = " | ".join(filter_items) if filter_items else "All Approved Certificates (Full Unfiltered Scope)"
    pdf.set_fill_color(248, 250, 252)  # Slate-50
    pdf.set_draw_color(226, 232, 240)  # Slate-200
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(100, 116, 139)
    pdf.rect(pdf.l_margin, pdf.get_y(), pw, 8, "DF")
    pdf.set_xy(pdf.l_margin + 3, pdf.get_y() + 1.5)
    pdf.cell(0, 5, _sanitize(f"Active Scope Filters:  {filter_text}"), border=0)
    pdf.set_y(pdf.get_y() + 9)

    # ── Executive KPI Scorecard ───────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 7, "Executive Performance Scorecard", border=0, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)

    kpi_list = [
        ("Total Approved", f"{total:,}", "100% verified"),
        ("Unique Recipients", f"{getattr(kpis, 'unique_recipients', 0):,}", "Distinct holders"),
        ("Certificate Titles", f"{getattr(kpis, 'certificate_names', 0):,}", "Unique designations"),
        ("Issuing Bodies", f"{getattr(kpis, 'issuing_organizations', 0):,}", "Accredited institutions"),
        ("Courses / Tracks", f"{getattr(kpis, 'courses', 0):,}", "Curriculum programs"),
        ("Avg Certs / Person", f"{getattr(kpis, 'avg_certs_per_person', 0):.2f}", "Credential depth"),
        ("Completed This Year", f"{getattr(kpis, 'completed_this_year', 0):,}", "Year-to-date completions"),
        ("Completed This Month", f"{getattr(kpis, 'completed_this_month', 0):,}", "Current velocity"),
    ]

    card_w = (pw - 9) / 4  # 4 cards per row
    card_h = 17
    curr_y = pdf.get_y()

    for idx, (label, val, sub) in enumerate(kpi_list):
        col = idx % 4
        row = idx // 4
        x = pdf.l_margin + col * (card_w + 3)
        y = curr_y + row * (card_h + 3)

        pdf.set_fill_color(255, 255, 255)
        pdf.set_draw_color(226, 232, 240)
        pdf.rect(x, y, card_w, card_h, "DF")

        # Top indicator bar
        accent_color = (79, 70, 229) if idx in (0, 1) else (37, 99, 235) if idx in (2, 3) else (5, 150, 105) if idx in (4, 5) else (217, 119, 6)
        pdf.set_fill_color(*accent_color)
        pdf.rect(x, y, card_w, 1.2, "F")

        pdf.set_xy(x + 2.5, y + 2.5)
        pdf.set_font("Helvetica", "B", 7)
        pdf.set_text_color(100, 116, 139)
        pdf.cell(card_w - 5, 3.5, label.upper(), border=0)

        pdf.set_xy(x + 2.5, y + 6.5)
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(card_w - 5, 6, val, border=0)

        pdf.set_xy(x + 2.5, y + 12.5)
        pdf.set_font("Helvetica", "", 6.5)
        pdf.set_text_color(148, 163, 184)
        pdf.cell(card_w - 5, 3, sub, border=0)

    pdf.set_y(curr_y + 2 * (card_h + 3) + 2)

    # ── Key Insights ─────────────────────────────────────────────────────────
    if insights:
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(0, 6, "Strategic Analytics Insights", border=0, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)

        for ins in insights[:4]:
            text = ins if isinstance(ins, str) else ins.get("text", "")
            title = ins.get("title", "Observation") if isinstance(ins, dict) else "Finding"
            pdf.set_fill_color(248, 250, 252)
            pdf.set_draw_color(203, 213, 225)
            y_box = pdf.get_y()
            pdf.rect(pdf.l_margin, y_box, pw, 9.5, "DF")

            # Left accent pill
            pdf.set_fill_color(79, 70, 229)
            pdf.rect(pdf.l_margin, y_box, 1.8, 9.5, "F")

            pdf.set_xy(pdf.l_margin + 4, y_box + 1.2)
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_text_color(15, 23, 42)
            pdf.cell(35, 4, _sanitize(title) + ":", border=0)

            pdf.set_font("Helvetica", "", 8)
            pdf.set_text_color(51, 65, 85)
            pdf.cell(pw - 42, 4, _sanitize(text)[:105], border=0)
            pdf.set_y(y_box + 11)

        pdf.ln(1)

    # ── Data Quality & Integrity Audit ────────────────────────────────────────
    if dq:
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(0, 6, "Data Integrity & Verification Completeness", border=0, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)

        dq_total = getattr(dq, "total", total) or 1
        fields = [
            ("Recipient Name", getattr(dq, "recipient_identified", 0)),
            ("Certificate Title", getattr(dq, "certificate_name_identified", 0)),
            ("Completion Date", getattr(dq, "completion_date_identified", 0)),
            ("Issuing Institution", getattr(dq, "institution_identified", 0)),
            ("Certificate Number", getattr(dq, "certificate_number_identified", 0)),
            ("Course / Program", getattr(dq, "course_identified", 0)),
        ]

        col_w = (pw - 5) / 2
        curr_y = pdf.get_y()
        for idx, (lbl, val) in enumerate(fields):
            pct = min(round((val / dq_total) * 100), 100) if dq_total else 0
            cx = pdf.l_margin + (idx % 2) * (col_w + 5)
            cy = curr_y + (idx // 2) * 8

            pdf.set_xy(cx, cy)
            pdf.set_font("Helvetica", "", 8)
            pdf.set_text_color(71, 85, 105)
            pdf.cell(42, 4, _sanitize(lbl), border=0)

            pdf.set_xy(cx + 43, cy)
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_text_color(15, 23, 42)
            pdf.cell(20, 4, f"{pct}%", border=0)

            # Progress bar
            bar_w = col_w - 65
            pdf.set_fill_color(226, 232, 240)
            pdf.rect(cx + 65, cy + 1, bar_w, 3, "F")
            bar_color = (5, 150, 105) if pct >= 90 else (217, 119, 6)
            pdf.set_fill_color(*bar_color)
            pdf.rect(cx + 65, cy + 1, max(bar_w * (pct / 100), 1), 3, "F")

        pdf.set_y(curr_y + 3 * 8 + 3)

    # ── Helper for Vector Bar Chart Sections ──────────────────────────────────
    def render_section_with_bar_chart(
        title: str,
        subtitle: str,
        data: dict[str, int],
        bar_color: tuple[int, int, int] = (79, 70, 229),
        max_items: int = 8,
    ) -> None:
        """Renders a section with an inline vector bar chart and data table."""
        # Clean data
        entries = [(k, v) for k, v in data.items() if k not in ("Not specified", "N/A", "Unknown", "")]
        if not entries:
            entries = list(data.items())
        entries = sorted(entries, key=lambda x: x[1], reverse=True)[:max_items]

        # Check page height needed
        needed_height = 20 + len(entries) * 7 + 10
        if pdf.get_y() + needed_height > pdf.h - 20:
            pdf.add_page()

        # Section Title with pill
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(0, 6, _sanitize(title), border=0, new_x="LMARGIN", new_y="NEXT")

        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(100, 116, 139)
        pdf.cell(0, 4, _sanitize(subtitle), border=0, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

        if not entries:
            pdf.set_font("Helvetica", "I", 8.5)
            pdf.set_text_color(148, 163, 184)
            pdf.cell(0, 6, "No breakdown data available for this category", border=0, new_x="LMARGIN", new_y="NEXT")
            pdf.ln(4)
            return

        max_v = max([v for _, v in entries] or [1])
        track_w = 70.0  # width of the bar in mm
        label_w = 68.0  # label column width
        val_w = 32.0    # value + pct width

        # Table header
        pdf.set_fill_color(241, 245, 249)
        pdf.set_font("Helvetica", "B", 7.5)
        pdf.set_text_color(71, 85, 105)
        pdf.cell(8, 5, "#", border=0, align="C", fill=True)
        pdf.cell(label_w, 5, "Classification / Title", border=0, fill=True)
        pdf.cell(track_w, 5, "Distribution Relative Share", border=0, fill=True)
        pdf.cell(val_w, 5, "Count (Share)", border=0, align="R", fill=True, new_x="LMARGIN", new_y="NEXT")

        # Rows with bars
        for idx, (k, v) in enumerate(entries):
            fill_w = max((v / max_v) * track_w, 1.5)
            pct = (v / total * 100) if total else 0
            y_row = pdf.get_y()

            # Zebra shading
            if idx % 2 == 1:
                pdf.set_fill_color(248, 250, 252)
                pdf.rect(pdf.l_margin, y_row, pw, 5.5, "F")

            # Rank
            pdf.set_xy(pdf.l_margin, y_row)
            pdf.set_font("Helvetica", "", 7.5)
            pdf.set_text_color(100, 116, 139)
            pdf.cell(8, 5.5, str(idx + 1), border=0, align="C")

            # Label
            pdf.set_xy(pdf.l_margin + 8, y_row)
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_text_color(30, 41, 59)
            pdf.cell(label_w, 5.5, _sanitize(k)[:40], border=0)

            # Vector Bar (Track + Fill)
            bar_x = pdf.l_margin + 8 + label_w
            bar_y = y_row + 1.2
            pdf.set_fill_color(241, 245, 249)  # track
            pdf.rect(bar_x, bar_y, track_w, 3.2, "F")
            pdf.set_fill_color(*bar_color)     # active fill
            pdf.rect(bar_x, bar_y, fill_w, 3.2, "F")

            # Value & percentage
            pdf.set_xy(bar_x + track_w, y_row)
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_text_color(15, 23, 42)
            pdf.cell(val_w, 5.5, f"{v:,} ({pct:.1f}%)", border=0, align="R", new_x="LMARGIN", new_y="NEXT")

        pdf.ln(4)

    # ── Page 2: Distribution Analytics ───────────────────────────────────────
    pdf.add_page()

    render_section_with_bar_chart(
        title="1. Certificate Title Distribution",
        subtitle="Distribution across specific certificate designations and professional accreditations",
        data=by_name,
        bar_color=(79, 70, 229),  # Indigo
        max_items=10,
    )

    render_section_with_bar_chart(
        title="2. Certificate Classification by Type",
        subtitle="Breakdown by credential type (Professional, Technical, Academic, Compliance)",
        data=by_type,
        bar_color=(5, 150, 105),  # Emerald
        max_items=8,
    )

    # ── Page 3: Organization & Curriculum Analytics ───────────────────────────
    pdf.add_page()

    render_section_with_bar_chart(
        title="3. Issuing Organizations & Accreditation Bodies",
        subtitle="Institutions, universities, and enterprise vendors issuing verified credentials",
        data=by_issuer,
        bar_color=(37, 99, 235),  # Blue
        max_items=10,
    )

    render_section_with_bar_chart(
        title="4. Courses & Curriculum Programs",
        subtitle="Curriculum pathways and specific training tracks tied to approved certificates",
        data=by_course,
        bar_color=(124, 58, 237),  # Purple
        max_items=10,
    )

    # ── Page 4: Longitudinal Trends & Recipient Intelligence ──────────────────
    pdf.add_page()

    render_section_with_bar_chart(
        title="5. Annual Completion Trends & Trajectory",
        subtitle="Historical certificate completion velocity by calendar year",
        data=trends,
        bar_color=(30, 41, 59),  # Slate
        max_items=8,
    )

    render_section_with_bar_chart(
        title="6. Multi-Certification Depth (Certificates Per Person)",
        subtitle="Workforce credential distribution and multi-certification breadth",
        data=certs_per_person,
        bar_color=(217, 119, 6),  # Amber
        max_items=6,
    )

    # Top Recipients Table
    if recipients:
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(0, 6, "7. Top Credential Holders (Leaderboard)", border=0, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(100, 116, 139)
        pdf.cell(0, 4, "Individuals with the highest volume of verified certificates", border=0, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

        pdf.set_fill_color(241, 245, 249)
        pdf.set_font("Helvetica", "B", 7.5)
        pdf.set_text_color(71, 85, 105)
        pdf.cell(12, 5, "Rank", border=0, align="C", fill=True)
        pdf.cell(90, 5, "Recipient Full Name", border=0, fill=True)
        pdf.cell(40, 5, "Verified Certificates", border=0, align="C", fill=True)
        pdf.cell(40, 5, "Status", border=0, align="C", fill=True, new_x="LMARGIN", new_y="NEXT")

        for idx, r in enumerate(recipients[:10]):
            y_r = pdf.get_y()
            if idx % 2 == 1:
                pdf.set_fill_color(248, 250, 252)
                pdf.rect(pdf.l_margin, y_r, pw, 5.5, "F")

            r_name = r.get("name", "") if isinstance(r, dict) else str(r)
            r_cnt = r.get("approved_certificates", 0) if isinstance(r, dict) else 0

            pdf.set_xy(pdf.l_margin, y_r)
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_text_color(79, 70, 229)
            pdf.cell(12, 5.5, f"#{idx + 1}", border=0, align="C")

            pdf.set_font("Helvetica", "B", 8)
            pdf.set_text_color(15, 23, 42)
            pdf.cell(90, 5.5, _sanitize(r_name)[:45], border=0)

            pdf.set_font("Helvetica", "", 8)
            pdf.cell(40, 5.5, f"{r_cnt} certificate{'s' if r_cnt != 1 else ''}", border=0, align="C")

            pdf.set_font("Helvetica", "B", 7)
            pdf.set_text_color(5, 150, 105)
            pdf.cell(40, 5.5, "VERIFIED", border=0, align="C", new_x="LMARGIN", new_y="NEXT")

        pdf.ln(4)

    # ── Page 5+: Approved Certificate Master Registry ─────────────────────────
    if records:
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(0, 6, "8. Approved Certificate Registry", border=0, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(100, 116, 139)
        pdf.cell(
            0,
            4,
            f"Detailed record log of approved credentials (Showing {min(len(records), 150)} of {len(records)} records)",
            border=0,
            new_x="LMARGIN",
            new_y="NEXT",
        )
        pdf.ln(2)

        # Columns configuration
        cols = [
            ("#", 8, "C"),
            ("Recipient", 38, "L"),
            ("Certificate Title", 48, "L"),
            ("Type", 26, "L"),
            ("Issuing Organization", 38, "L"),
            ("Date", 24, "C"),
        ]

        def print_registry_header():
            pdf.set_fill_color(30, 41, 59)
            pdf.set_font("Helvetica", "B", 7.5)
            pdf.set_text_color(255, 255, 255)
            for h_text, h_w, h_align in cols:
                pdf.cell(h_w, 5.5, h_text, border=0, align=h_align, fill=True)
            pdf.ln()

        print_registry_header()

        for idx, rec in enumerate(records[:150]):
            # Check page break
            if pdf.get_y() > pdf.h - 18:
                pdf.add_page()
                print_registry_header()

            y_pos = pdf.get_y()
            if idx % 2 == 1:
                pdf.set_fill_color(248, 250, 252)
                pdf.rect(pdf.l_margin, y_pos, pw, 5.2, "F")

            r_name = rec.get("recipient", "")
            c_name = rec.get("certificate_name", "")
            c_type = rec.get("certificate_type", "")
            c_org = rec.get("issuing_organization", "")
            c_date = rec.get("completion_date", "")

            pdf.set_xy(pdf.l_margin, y_pos)
            pdf.set_font("Helvetica", "", 7)
            pdf.set_text_color(100, 116, 139)
            pdf.cell(cols[0][1], 5.2, str(idx + 1), border=0, align="C")

            pdf.set_font("Helvetica", "B", 7.5)
            pdf.set_text_color(15, 23, 42)
            pdf.cell(cols[1][1], 5.2, _sanitize(r_name)[:22], border=0)

            pdf.set_font("Helvetica", "", 7.5)
            pdf.set_text_color(51, 65, 85)
            pdf.cell(cols[2][1], 5.2, _sanitize(c_name)[:28], border=0)
            pdf.cell(cols[3][1], 5.2, _sanitize(c_type)[:15], border=0)
            pdf.cell(cols[4][1], 5.2, _sanitize(c_org)[:22], border=0)

            pdf.set_font("Helvetica", "", 7)
            pdf.cell(cols[5][1], 5.2, _sanitize(c_date)[:10], border=0, align="C", new_x="LMARGIN", new_y="NEXT")

    return bytes(pdf.output())
