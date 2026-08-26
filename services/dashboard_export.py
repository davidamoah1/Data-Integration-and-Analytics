"""Dashboard Export Service.

Exports dashboards to multiple formats:
  - PDF (with branding and metadata)
  - Excel (multi-sheet with KPIs, charts data, filters)
  - CSV (flat data export)
  - PNG (chart snapshots â€” requires frontend rendering)
  - Print-friendly view (HTML)

Includes branding and metadata where appropriate.
"""

from __future__ import annotations

import csv
import io
import logging
from datetime import datetime, timezone

import pandas as pd

from services.dashboard_engine import DashboardMetadata

logger = logging.getLogger(__name__)


class DashboardExportService:
    """Export dashboards to multiple formats."""

    SUPPORTED_FORMATS = ("pdf", "excel", "csv", "png", "print")

    @staticmethod
    def _strip_emoji(text: str) -> str:
        """Remove emoji and non-latin-1 characters for PDF compatibility."""
        return "".join(
            c
            for c in text
            if ord(c) <= 0xFFFF and c.isprintable() and ord(c) < 256 or c in " -_:.()[]/"
        )

    def __init__(self, brand_name: str = "ETL Platform", brand_color: str = "#667eea"):
        self.brand_name = brand_name
        self.brand_color = brand_color

    def export(
        self,
        dashboard: DashboardMetadata,
        df: pd.DataFrame | None = None,
        fmt: str = "pdf",
        kpi_values: dict | None = None,
    ) -> tuple[bytes, str, str]:
        """Export a dashboard to the specified format.

        Args:
            dashboard: Dashboard metadata.
            df: Optional DataFrame with the source data.
            fmt: Export format (pdf, excel, csv, png, print).
            kpi_values: Optional pre-computed KPI values.

        Returns:
            Tuple of (content_bytes, filename, content_type).
        """
        fmt = fmt.lower().strip()
        if fmt not in self.SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported format: {fmt}. Supported: {self.SUPPORTED_FORMATS}")

        if fmt == "pdf":
            return self._export_pdf(dashboard, df, kpi_values)
        elif fmt == "excel":
            return self._export_excel(dashboard, df, kpi_values)
        elif fmt == "csv":
            return self._export_csv(dashboard, df)
        elif fmt == "png":
            return self._export_png(dashboard)
        elif fmt == "print":
            return self._export_print(dashboard, df, kpi_values)

    def _export_pdf(
        self,
        dashboard: DashboardMetadata,
        df: pd.DataFrame | None,
        kpi_values: dict | None,
    ) -> tuple[bytes, str, str]:
        """Export dashboard as PDF with branding."""
        from fpdf import FPDF

        pdf = FPDF(orientation="L", unit="mm", format="A4")
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)

        # Header with branding
        pdf.set_fill_color(102, 126, 234)  # brand_color as RGB
        pdf.rect(0, 0, 297, 20, "F")
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, f"  {self.brand_name} - Dashboard Report", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(5)

        # Title
        pdf.set_text_color(30, 30, 30)
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, dashboard.title, new_x="LMARGIN", new_y="NEXT")
        if dashboard.subtitle:
            pdf.set_font("Helvetica", "I", 10)
            pdf.set_text_color(100, 100, 100)
            pdf.cell(0, 6, dashboard.subtitle, new_x="LMARGIN", new_y="NEXT")

        # Metadata
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(120, 120, 120)
        pdf.cell(
            0,
            5,
            f"Industry: {dashboard.industry.title()}  |  Version: {dashboard.version}  |  Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
            new_x="LMARGIN",
            new_y="NEXT",
        )
        pdf.ln(5)

        # KPIs section
        if dashboard.kpis:
            pdf.set_font("Helvetica", "B", 12)
            pdf.set_text_color(30, 30, 30)
            pdf.cell(0, 8, "Key Performance Indicators", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)

            for kpi in dashboard.kpis:
                value_str = ""
                if kpi_values and kpi.key in kpi_values:
                    value_str = str(kpi_values[kpi.key])
                else:
                    value_str = "N/A"

                pdf.set_font("Helvetica", "B", 10)
                pdf.set_text_color(50, 50, 50)
                icon = self._strip_emoji(kpi.icon)
                pdf.cell(60, 6, f"  {icon} {kpi.label}:", border=0)
                pdf.set_font("Helvetica", "", 10)
                pdf.set_text_color(80, 80, 80)
                pdf.cell(40, 6, value_str, border=0)
                pdf.set_font("Helvetica", "I", 8)
                pdf.set_text_color(150, 150, 150)
                pdf.cell(0, 6, kpi.description, border=0, new_x="LMARGIN", new_y="NEXT")

            pdf.ln(5)

        # Charts section
        if dashboard.charts:
            pdf.set_font("Helvetica", "B", 12)
            pdf.set_text_color(30, 30, 30)
            pdf.cell(0, 8, "Recommended Charts", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)

            for chart in dashboard.charts:
                pdf.set_font("Helvetica", "B", 10)
                pdf.set_text_color(50, 50, 50)
                pdf.cell(
                    0,
                    6,
                    f"  - {chart.title} ({chart.chart_type.replace('_', ' ').title()})",
                    new_x="LMARGIN",
                    new_y="NEXT",
                )
                pdf.set_font("Helvetica", "I", 8)
                pdf.set_text_color(120, 120, 120)
                pdf.cell(0, 5, f"    {chart.reasoning}", new_x="LMARGIN", new_y="NEXT")
                if chart.x_axis or chart.y_axis:
                    axes = []
                    if chart.x_axis:
                        axes.append(f"X: {chart.x_axis}")
                    if chart.y_axis:
                        axes.append(f"Y: {chart.y_axis}")
                    pdf.set_font("Helvetica", "", 8)
                    pdf.set_text_color(100, 100, 100)
                    pdf.cell(
                        0,
                        5,
                        f"    Axes: {', '.join(axes)}  |  Aggregation: {chart.aggregation}",
                        new_x="LMARGIN",
                        new_y="NEXT",
                    )
                pdf.ln(2)

            pdf.ln(5)

        # Filters section
        if dashboard.filters:
            pdf.set_font("Helvetica", "B", 12)
            pdf.set_text_color(30, 30, 30)
            pdf.cell(0, 8, "Filters", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)
            for f in dashboard.filters:
                pdf.set_font("Helvetica", "", 10)
                pdf.set_text_color(60, 60, 60)
                pdf.cell(
                    0,
                    6,
                    f"  - {f.label} ({f.filter_type.replace('_', ' ').title()}) - Column: {f.column}",
                    new_x="LMARGIN",
                    new_y="NEXT",
                )
            pdf.ln(5)

        # AI Insights
        if dashboard.ai_insights:
            pdf.set_font("Helvetica", "B", 12)
            pdf.set_text_color(30, 30, 30)
            pdf.cell(0, 8, "AI Insights", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)
            for insight in dashboard.ai_insights:
                pdf.set_font("Helvetica", "", 10)
                pdf.set_text_color(60, 60, 60)
                pdf.multi_cell(0, 6, f"  - {insight}")
            pdf.ln(5)

        # Data table (if provided)
        if df is not None and not df.empty:
            pdf.add_page()
            pdf.set_font("Helvetica", "B", 12)
            pdf.set_text_color(30, 30, 30)
            pdf.cell(0, 8, "Data Preview (first 50 rows)", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)

            preview = df.head(50)
            cols = list(preview.columns[:8])  # Max 8 columns
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_fill_color(240, 240, 250)
            for col in cols:
                pdf.cell(30, 6, str(col)[:15], border=1, fill=True)
            pdf.ln()

            pdf.set_font("Helvetica", "", 7)
            pdf.set_text_color(60, 60, 60)
            for _, row in preview.iterrows():
                for col in cols:
                    val = str(row.get(col, ""))[:15]
                    pdf.cell(30, 5, val, border=1)
                pdf.ln()

        # Footer
        pdf.set_y(-15)
        pdf.set_font("Helvetica", "I", 7)
        pdf.set_text_color(150, 150, 150)
        pdf.cell(0, 5, f"{self.brand_name} - Page {pdf.page_no()}", align="C")

        content = pdf.output()
        filename = f"dashboard_{dashboard.dashboard_id[:8]}.pdf"
        return content, filename, "application/pdf"

    def _export_excel(
        self,
        dashboard: DashboardMetadata,
        df: pd.DataFrame | None,
        kpi_values: dict | None,
    ) -> tuple[bytes, str, str]:
        """Export dashboard as Excel with multiple sheets."""
        output = io.BytesIO()

        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            # Sheet 1: KPIs
            kpi_data = []
            for kpi in dashboard.kpis:
                kpi_data.append(
                    {
                        "KPI": kpi.label,
                        "Value": kpi_values.get(kpi.key, "N/A") if kpi_values else "N/A",
                        "Category": kpi.category,
                        "Formula": kpi.formula,
                        "Confidence": kpi.confidence,
                        "Description": kpi.description,
                    }
                )
            if kpi_data:
                pd.DataFrame(kpi_data).to_excel(writer, sheet_name="KPIs", index=False)

            # Sheet 2: Charts
            chart_data = []
            for chart in dashboard.charts:
                chart_data.append(
                    {
                        "Title": chart.title,
                        "Type": chart.chart_type,
                        "X Axis": chart.x_axis or "",
                        "Y Axis": chart.y_axis or "",
                        "Group By": chart.group_by or "",
                        "Aggregation": chart.aggregation,
                        "Confidence": chart.confidence,
                        "Reasoning": chart.reasoning,
                    }
                )
            if chart_data:
                pd.DataFrame(chart_data).to_excel(writer, sheet_name="Charts", index=False)

            # Sheet 3: Filters
            filter_data = []
            for f in dashboard.filters:
                filter_data.append(
                    {
                        "Label": f.label,
                        "Type": f.filter_type,
                        "Column": f.column,
                        "Entity": f.entity or "",
                    }
                )
            if filter_data:
                pd.DataFrame(filter_data).to_excel(writer, sheet_name="Filters", index=False)

            # Sheet 4: AI Insights
            if dashboard.ai_insights:
                pd.DataFrame({"Insights": dashboard.ai_insights}).to_excel(
                    writer, sheet_name="AI Insights", index=False
                )

            # Sheet 5: Data
            if df is not None and not df.empty:
                df.to_excel(writer, sheet_name="Data", index=False)

            # Sheet 6: Metadata
            meta_data = {
                "Field": [
                    "Dashboard ID",
                    "Title",
                    "Industry",
                    "Version",
                    "Created",
                    "Updated",
                    "Template",
                ],
                "Value": [
                    dashboard.dashboard_id,
                    dashboard.title,
                    dashboard.industry,
                    dashboard.version,
                    dashboard.created_at,
                    dashboard.updated_at,
                    dashboard.template_key,
                ],
            }
            pd.DataFrame(meta_data).to_excel(writer, sheet_name="Metadata", index=False)

        content = output.getvalue()
        filename = f"dashboard_{dashboard.dashboard_id[:8]}.xlsx"
        return (
            content,
            filename,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    def _export_csv(
        self,
        dashboard: DashboardMetadata,
        df: pd.DataFrame | None,
    ) -> tuple[bytes, str, str]:
        """Export dashboard data as CSV."""
        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([f"# {self.brand_name} â€” Dashboard Export"])
        writer.writerow([f"# Title: {dashboard.title}"])
        writer.writerow([f"# Industry: {dashboard.industry}"])
        writer.writerow([f"# Generated: {datetime.now(timezone.utc).isoformat()}"])
        writer.writerow([])

        # KPIs
        writer.writerow(["=== KPIs ==="])
        writer.writerow(["Label", "Category", "Formula", "Confidence", "Description"])
        for kpi in dashboard.kpis:
            writer.writerow([kpi.label, kpi.category, kpi.formula, kpi.confidence, kpi.description])
        writer.writerow([])

        # Charts
        writer.writerow(["=== Charts ==="])
        writer.writerow(["Title", "Type", "X Axis", "Y Axis", "Aggregation", "Confidence"])
        for chart in dashboard.charts:
            writer.writerow(
                [
                    chart.title,
                    chart.chart_type,
                    chart.x_axis,
                    chart.y_axis,
                    chart.aggregation,
                    chart.confidence,
                ]
            )
        writer.writerow([])

        # Data
        if df is not None and not df.empty:
            writer.writerow(["=== Data ==="])
            writer.writerow(df.columns.tolist())
            for _, row in df.iterrows():
                writer.writerow(row.tolist())

        content = output.getvalue().encode("utf-8")
        filename = f"dashboard_{dashboard.dashboard_id[:8]}.csv"
        return content, filename, "text/csv"

    def _export_png(self, dashboard: DashboardMetadata) -> tuple[bytes, str, str]:
        """Export dashboard as PNG placeholder.

        Note: Actual PNG rendering requires frontend chart capture.
        This returns a metadata stub that the frontend can use.
        """
        import json

        metadata = {
            "format": "png",
            "dashboard_id": dashboard.dashboard_id,
            "title": dashboard.title,
            "charts": [c.to_dict() for c in dashboard.charts],
            "message": "PNG export requires frontend chart rendering. Use the frontend capture endpoint.",
        }
        content = json.dumps(metadata, indent=2).encode("utf-8")
        filename = f"dashboard_{dashboard.dashboard_id[:8]}_metadata.json"
        return content, filename, "application/json"

    def _export_print(
        self,
        dashboard: DashboardMetadata,
        df: pd.DataFrame | None,
        kpi_values: dict | None,
    ) -> tuple[bytes, str, str]:
        """Export dashboard as print-friendly HTML."""
        html_parts: list[str] = [
            "<!DOCTYPE html>",
            '<html lang="en">',
            "<head>",
            '<meta charset="UTF-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
            f"<title>{dashboard.title} â€” Print View</title>",
            "<style>",
            "body { font-family: 'Segoe UI', Arial, sans-serif; margin: 20px; color: #333; }",
            ".header { background: #667eea; color: white; padding: 15px 20px; border-radius: 8px; margin-bottom: 20px; }",
            ".header h1 { margin: 0; font-size: 20px; }",
            ".header p { margin: 5px 0 0 0; font-size: 12px; opacity: 0.9; }",
            ".section { margin-bottom: 25px; }",
            ".section h2 { font-size: 16px; border-bottom: 2px solid #667eea; padding-bottom: 5px; }",
            ".kpi-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 10px; }",
            ".kpi-card { border: 1px solid #e0e0e0; border-radius: 6px; padding: 12px; }",
            ".kpi-card .label { font-size: 11px; color: #888; }",
            ".kpi-card .value { font-size: 20px; font-weight: bold; color: #333; }",
            ".chart-item { border: 1px solid #e0e0e0; border-radius: 6px; padding: 10px; margin-bottom: 8px; }",
            ".chart-item .title { font-weight: bold; font-size: 13px; }",
            ".chart-item .meta { font-size: 11px; color: #888; }",
            ".filter-item { font-size: 12px; padding: 4px 0; }",
            ".insight-item { font-size: 12px; padding: 4px 0; }",
            ".footer { margin-top: 30px; border-top: 1px solid #e0e0e0; padding-top: 10px; font-size: 10px; color: #aaa; text-align: center; }",
            "@media print { .no-print { display: none; } }",
            "</style>",
            "</head>",
            "<body>",
            '<div class="header">',
            f"<h1>{dashboard.title}</h1>",
            f"<p>{dashboard.subtitle} | Industry: {dashboard.industry.title()} | Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}</p>",
            "</div>",
        ]

        # KPIs
        if dashboard.kpis:
            html_parts.append(
                '<div class="section"><h2>Key Performance Indicators</h2><div class="kpi-grid">'
            )
            for kpi in dashboard.kpis:
                value = ""
                if kpi_values and kpi.key in kpi_values:
                    value = str(kpi_values[kpi.key])
                html_parts.append(
                    f'<div class="kpi-card">'
                    f'<div class="label">{kpi.icon} {kpi.label}</div>'
                    f'<div class="value">{value or "N/A"}</div>'
                    f"</div>"
                )
            html_parts.append("</div></div>")

        # Charts
        if dashboard.charts:
            html_parts.append('<div class="section"><h2>Charts</h2>')
            for chart in dashboard.charts:
                html_parts.append(
                    f'<div class="chart-item">'
                    f'<div class="title">{chart.title}</div>'
                    f'<div class="meta">Type: {chart.chart_type.replace("_", " ").title()} | '
                    f'X: {chart.x_axis or "N/A"} | Y: {chart.y_axis or "N/A"} | '
                    f"Aggregation: {chart.aggregation}</div>"
                    f'<div class="meta">{chart.reasoning}</div>'
                    f"</div>"
                )
            html_parts.append("</div>")

        # Filters
        if dashboard.filters:
            html_parts.append('<div class="section"><h2>Filters</h2>')
            for f in dashboard.filters:
                html_parts.append(
                    f'<div class="filter-item">â€¢ {f.label} ({f.filter_type.replace("_", " ").title()}) â€” Column: {f.column}</div>'
                )
            html_parts.append("</div>")

        # AI Insights
        if dashboard.ai_insights:
            html_parts.append('<div class="section"><h2>AI Insights</h2>')
            for insight in dashboard.ai_insights:
                html_parts.append(f'<div class="insight-item">â€¢ {insight}</div>')
            html_parts.append("</div>")

        # Footer
        html_parts.append(
            f'<div class="footer">{self.brand_name} â€” Dashboard Export | {dashboard.dashboard_id}</div>'
        )
        html_parts.append("</body></html>")

        content = "\n".join(html_parts).encode("utf-8")
        filename = f"dashboard_{dashboard.dashboard_id[:8]}.html"
        return content, filename, "text/html"
