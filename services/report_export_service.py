"""Report export service.

Exports AI-generated reports to csv, xlsx, or pdf using the persisted
`data_sources` JSON for tabular data and markdown `content` for PDF.
"""

from __future__ import annotations

import csv
import io
from typing import Any

import pandas as pd
from fpdf import FPDF

SUPPORTED_FORMATS = {"csv", "excel", "xlsx", "pdf"}


def _sanitize_pdf_text(text: str) -> str:
    """Replace characters not supported by fpdf's latin-1 encoding."""
    if not text:
        return text
    replacements = {
        "\u2014": "-",   # em dash
        "\u2013": "-",   # en dash
        "\u2018": "'",   # left single quote
        "\u2019": "'",   # right single quote
        "\u201c": '"',   # left double quote
        "\u201d": '"',   # right double quote
        "\u2026": "...", # ellipsis
        "\u00a0": " ",   # non-breaking space
        "\u2022": "*",   # bullet
        "\u2013": "-",   # en dash
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    # Remove any remaining non-latin-1 characters
    return text.encode("latin-1", errors="replace").decode("latin-1")


def _list_sources(data_sources: dict | None) -> list[tuple[str, list[dict]]]:
    sources: list[tuple[str, list[dict]]] = []
    if isinstance(data_sources, dict):
        for name, value in data_sources.items():
            if isinstance(value, list) and value and all(isinstance(v, dict) for v in value):
                sources.append((name, value))
    return sources


class ReportExportService:
    """Export an AI report to CSV, Excel, or PDF."""

    def export(self, report: Any, format: str) -> tuple[bytes, str, str]:
        fmt = format.lower().strip()
        if fmt == "xlsx":
            fmt = "excel"
        if fmt not in SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported format: {format}")

        title = getattr(report, "title", "Report") or "Report"
        content = getattr(report, "content", "") or ""
        summary = getattr(report, "summary", "") or ""
        report_type = getattr(report, "report_type", "report") or "report"
        created_at = getattr(report, "created_at", "") or ""
        sections = getattr(report, "sections", None) or []
        data_sources = getattr(report, "data_sources", None) or {}

        if fmt == "csv":
            return self._to_csv(title, report_type, content, summary, created_at, data_sources)
        if fmt == "excel":
            return self._to_excel(title, report_type, content, summary, sections, created_at, data_sources)
        return self._to_pdf(title, report_type, content, summary, sections, created_at, data_sources)

    def _to_csv(
        self, title: str, report_type: str, content: str, summary: str, created_at: str, data_sources: dict
    ) -> tuple[bytes, str, str]:
        sources = _list_sources(data_sources)
        if sources:
            _, records = max(sources, key=lambda s: len(s[1]))
            df = pd.DataFrame(records)
        else:
            df = pd.DataFrame(
                [
                    {"field": "title", "value": title},
                    {"field": "type", "value": report_type},
                    {"field": "created_at", "value": created_at},
                    {"field": "summary", "value": summary},
                    {"field": "content", "value": content},
                ]
            )
        buffer = io.StringIO()
        df.to_csv(buffer, index=False, quoting=csv.QUOTE_MINIMAL)
        return buffer.getvalue().encode("utf-8-sig"), "text/csv; charset=utf-8", "csv"

    def _to_excel(
        self,
        title: str,
        report_type: str,
        content: str,
        summary: str,
        sections: list[str],
        created_at: str,
        data_sources: dict,
    ) -> tuple[bytes, str, str]:
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            overview = pd.DataFrame(
                [
                    {"Field": "Title", "Value": title},
                    {"Field": "Type", "Value": report_type},
                    {"Field": "Created", "Value": created_at},
                    {"Field": "Summary", "Value": summary},
                    {"Field": "Sections", "Value": ", ".join(sections) if sections else ""},
                    {"Field": "Content", "Value": content},
                ]
            )
            overview.to_excel(writer, sheet_name="Report", index=False)
            for name, records in _list_sources(data_sources):
                pd.DataFrame(records).to_excel(writer, sheet_name=name[:31], index=False)
        buffer.seek(0)
        return buffer.read(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "xlsx"

    def _to_pdf(
        self,
        title: str,
        report_type: str,
        content: str,
        summary: str,
        sections: list[str],
        created_at: str,
        data_sources: dict,
    ) -> tuple[bytes, str, str]:
        title = _sanitize_pdf_text(title)
        report_type = _sanitize_pdf_text(report_type)
        content = _sanitize_pdf_text(content)
        summary = _sanitize_pdf_text(summary)
        sections = [_sanitize_pdf_text(s) for s in sections]
        created_at = _sanitize_pdf_text(str(created_at))

        pdf = FPDF(format="A4")
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 6, f"Type: {report_type}  |  Created: {created_at}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

        page_width = pdf.w - pdf.l_margin - pdf.r_margin

        if summary:
            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(0, 8, "Summary", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(page_width, 5, summary)
            pdf.ln(4)

        if sections:
            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(0, 8, "Sections", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 10)
            for section in sections:
                pdf.cell(0, 5, f"- {section}", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(4)

        for name, records in _list_sources(data_sources):
            if not records:
                continue
            pdf.add_page()
            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(0, 8, _sanitize_pdf_text(name.replace("_", " ").title()), new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 9)
            cols = list(records[0].keys())
            width = 180 / max(len(cols), 1)
            for col in cols:
                pdf.cell(width, 6, _sanitize_pdf_text(str(col))[:18], border=1)
            pdf.ln()
            for row in records[:60]:
                for col in cols:
                    pdf.cell(width, 6, _sanitize_pdf_text(str(row.get(col, "")))[:18], border=1)
                pdf.ln()

        if content:
            pdf.add_page()
            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(0, 8, "Report Content", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 10)
            for line in content.splitlines():
                if not line.strip():
                    pdf.ln(3)
                    continue
                pdf.multi_cell(page_width, 5, line)

        return bytes(pdf.output()), "application/pdf", "pdf"


def export_report(report: Any, format: str) -> tuple[bytes, str, str]:
    """Convenience wrapper for ReportExportService.export."""
    return ReportExportService().export(report, format)
