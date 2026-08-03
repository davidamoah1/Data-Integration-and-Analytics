"""AI Report Writer — generates professional reports from platform data.

Generates:
- Executive summaries
- Monthly/Annual reports
- Department reports
- Data quality reports
- ETL performance reports
- Audit reports
"""

import json
from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session as DbSession

from ai.gateway import AIGateway
from ai.models import AIReportGeneration
from etl.models import ETLJob, ETLQualityReport


class AIReportWriter:
    """Generates professional reports using AI."""

    def __init__(self, db: DbSession):
        self.db = db
        self.gateway = AIGateway(db)

    def generate_report(
        self,
        report_type: str,
        title: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        department: str | None = None,
        format: str = "markdown",
        user_id: int | None = None,
        organization_id: int | None = None,
    ) -> dict:
        """Generate a report of the specified type.

        Returns:
            Dict with id, report_type, title, content, summary, sections.
        """
        # Gather data for the report
        report_data = self._gather_report_data(report_type, date_from, date_to, department)

        # Generate title if not provided
        if not title:
            title = self._default_title(report_type, date_from, date_to, department)

        # Build prompt
        prompt = self._build_report_prompt(
            report_type, title, report_data, date_from, date_to, department
        )

        # Generate report via AI
        result = self.gateway.chat(
            user_message=prompt,
            assistant_type="report_copilot",
            user_id=user_id,
        )

        content = result["response"]

        # Extract summary and sections
        summary = self._extract_summary(content)
        sections = self._extract_sections(content)

        # Save to database
        report = AIReportGeneration(
            report_type=report_type,
            title=title,
            content=content,
            summary=summary,
            sections=sections,
            format=format,
            data_sources=report_data,
            user_id=user_id,
            organization_id=organization_id,
        )
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)

        return {
            "id": report.id,
            "report_type": report_type,
            "title": title,
            "content": content,
            "summary": summary,
            "sections": sections,
            "created_at": str(report.created_at) if report.created_at else None,
        }

    def _gather_report_data(
        self, report_type: str, date_from: str | None, date_to: str | None, department: str | None
    ) -> dict:
        """Gather platform data relevant to the report type."""
        data = {}

        if report_type in ("executive", "monthly", "annual"):
            try:
                result = self.db.execute(
                    text(
                        "SELECT COUNT(*) as records, COALESCE(SUM(sales), 0) as total_sales, "
                        "COALESCE(SUM(profit), 0) as total_profit, "
                        "COALESCE(AVG(sales), 0) as avg_order_value, "
                        "COUNT(DISTINCT region) as regions, COUNT(DISTINCT category) as categories "
                        "FROM sales"
                    )
                )
                row = result.fetchone()
                if row:
                    data["sales_summary"] = {
                        "total_records": row[0],
                        "total_sales": float(row[1]),
                        "total_profit": float(row[2]),
                        "avg_order_value": float(row[3]),
                        "regions": row[4],
                        "categories": row[5],
                    }

                # Sales by region
                result = self.db.execute(
                    text(
                        "SELECT region, SUM(sales) as sales, SUM(profit) as profit "
                        "FROM sales GROUP BY region ORDER BY sales DESC"
                    )
                )
                data["sales_by_region"] = [
                    {"region": r[0], "sales": float(r[1]), "profit": float(r[2])}
                    for r in result.fetchall()
                ]

                # Sales by category
                result = self.db.execute(
                    text(
                        "SELECT category, SUM(sales) as sales FROM sales GROUP BY category ORDER BY sales DESC"
                    )
                )
                data["sales_by_category"] = [
                    {"category": r[0], "sales": float(r[1])} for r in result.fetchall()
                ]
            except Exception:
                data["sales_summary"] = {"note": "Sales data not available"}

        if report_type in ("etl", "performance"):
            try:
                jobs = self.db.query(ETLJob).order_by(ETLJob.created_at.desc()).limit(50).all()
                completed = [j for j in jobs if j.status == "completed"]
                failed = [j for j in jobs if j.status == "failed"]
                data["etl_stats"] = {
                    "total_jobs": len(jobs),
                    "completed": len(completed),
                    "failed": len(failed),
                    "success_rate": round(len(completed) / max(len(jobs), 1) * 100, 2),
                    "total_rows_extracted": sum(j.rows_extracted for j in jobs),
                    "total_rows_loaded": sum(j.rows_loaded for j in jobs),
                }
            except Exception:
                data["etl_stats"] = {"note": "ETL data not available"}

        if report_type == "quality":
            try:
                reports = (
                    self.db.query(ETLQualityReport)
                    .order_by(ETLQualityReport.created_at.desc())
                    .limit(20)
                    .all()
                )
                data["quality_reports"] = [
                    {
                        "source": r.source_name,
                        "score": r.overall_score,
                        "checks_passed": r.checks_passed,
                        "checks_failed": r.checks_failed,
                    }
                    for r in reports
                ]
            except Exception:
                data["quality_reports"] = []

        return data

    def _default_title(
        self, report_type: str, date_from: str | None, date_to: str | None, department: str | None
    ) -> str:
        """Generate a default title for the report."""
        titles = {
            "executive": "Executive Summary Report",
            "monthly": f"Monthly Report - {datetime.now(timezone.utc).strftime('%B %Y')}",
            "annual": f"Annual Report - {datetime.now(timezone.utc).year}",
            "department": f"Department Report - {department or 'All'}",
            "quality": "Data Quality Report",
            "etl": "ETL Performance Report",
            "performance": "Platform Performance Report",
            "audit": "Audit Report",
        }
        return titles.get(report_type, "Report")

    def _build_report_prompt(
        self,
        report_type: str,
        title: str,
        data: dict,
        date_from: str | None,
        date_to: str | None,
        department: str | None,
    ) -> str:
        """Build the prompt for report generation."""
        return (
            f"Generate a {report_type} report titled '{title}'.\n"
            f"Date range: {date_from or 'all time'} to {date_to or 'present'}\n"
            f"Department: {department or 'all'}\n\n"
            f"Platform data:\n{json.dumps(data, default=str)}\n\n"
            f"Format the report in Markdown with clear sections, tables, and analysis. "
            f"Include an executive summary at the top and actionable recommendations at the end."
        )

    def _extract_summary(self, content: str) -> str:
        """Extract a summary from the report content."""
        # Take the first paragraph after "Executive Summary" or first 500 chars
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if "executive summary" in line.lower():
                # Return next few non-empty lines
                summary_lines = []
                for j in range(i + 1, min(i + 10, len(lines))):
                    if lines[j].strip():
                        summary_lines.append(lines[j].strip())
                    elif summary_lines:
                        break
                return " ".join(summary_lines)[:500]
        return content[:500]

    def _extract_sections(self, content: str) -> list[str]:
        """Extract section titles from markdown content."""
        sections = []
        for line in content.split("\n"):
            if line.startswith("#"):
                sections.append(line.lstrip("#").strip())
        return sections
