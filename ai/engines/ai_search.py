"""AI Search Engine â€” global intelligent search using natural language.

Users can search using natural language queries like:
- "Show all failed ETL jobs"
- "Find hospitals with declining attendance"
- "Show districts with malaria increase"
- "Find reports created last month"
"""

import json
import logging

from sqlalchemy import text
from sqlalchemy.orm import Session as DbSession

from ai.gateway import AIGateway
from ai.models import (
    AIAnomalyAlert,
    AIForecast,
    AIInsight,
    AIReportGeneration,
)
from etl.models import ETLJob, ETLPipeline

logger = logging.getLogger(__name__)


class AISearchEngine:
    """Global AI-powered search across the platform."""

    def __init__(self, db: DbSession):
        self.db = db
        self.gateway = AIGateway(db)

    def search(
        self, query: str, search_type: str | None = None, user_id: int | None = None
    ) -> dict:
        """Search the platform using natural language.

        Returns:
            Dict with results, total, ai_summary.
        """
        # Determine search type from query if not specified
        if not search_type:
            search_type = self._infer_search_type(query)

        results = []

        if search_type in ("all", "jobs"):
            results.extend(self._search_jobs(query))

        if search_type in ("all", "pipelines"):
            results.extend(self._search_pipelines(query))

        if search_type in ("all", "reports"):
            results.extend(self._search_reports(query))

        if search_type in ("all", "insights"):
            results.extend(self._search_insights(query))

        if search_type in ("all", "data"):
            results.extend(self._search_data(query))

        if search_type in ("all", "forecasts"):
            results.extend(self._search_forecasts(query))

        if search_type in ("all", "alerts"):
            results.extend(self._search_alerts(query))

        # Generate AI summary of results
        ai_summary = self._generate_summary(query, results, user_id)

        return {
            "results": results[:50],  # Limit to 50 results
            "total": len(results),
            "ai_summary": ai_summary,
        }

    def _infer_search_type(self, query: str) -> str:
        """Infer search type from the query."""
        query_lower = query.lower()
        if "job" in query_lower or "etl" in query_lower:
            return "jobs"
        if "pipeline" in query_lower:
            return "pipelines"
        if "report" in query_lower:
            return "reports"
        if "insight" in query_lower or "decision" in query_lower:
            return "insights"
        if "forecast" in query_lower or "predict" in query_lower:
            return "forecasts"
        if "alert" in query_lower or "anomaly" in query_lower:
            return "alerts"
        return "all"

    def _search_jobs(self, query: str) -> list[dict]:
        """Search ETL jobs."""
        results = []
        try:
            query_lower = query.lower()
            jobs = self.db.query(ETLJob).order_by(ETLJob.created_at.desc()).limit(100).all()

            for job in jobs:
                searchable = f"{job.job_type} {job.status} {job.trigger_type} {job.error_message or ''}".lower()
                if any(word in searchable for word in query_lower.split()):
                    results.append(
                        {
                            "type": "etl_job",
                            "id": job.id,
                            "title": f"ETL Job #{job.id} - {job.status}",
                            "description": f"Type: {job.job_type}, Status: {job.status}, Rows: {job.rows_extracted}",
                            "created_at": str(job.created_at) if job.created_at else None,
                        }
                    )
        except Exception as e:
            logger.warning("Failed to search ETL jobs: %s", e)
        return results

    def _search_pipelines(self, query: str) -> list[dict]:
        """Search ETL pipelines."""
        results = []
        try:
            pipelines = self.db.query(ETLPipeline).limit(50).all()
            for p in pipelines:
                if (
                    query.lower() in (p.name or "").lower()
                    or query.lower() in (p.description or "").lower()
                ):
                    results.append(
                        {
                            "type": "pipeline",
                            "id": p.id,
                            "title": p.name,
                            "description": p.description or "",
                            "status": p.status,
                        }
                    )
        except Exception as e:
            logger.warning("Failed to search pipelines: %s", e)
        return results

    def _search_reports(self, query: str) -> list[dict]:
        """Search AI-generated reports."""
        results = []
        try:
            reports = (
                self.db.query(AIReportGeneration)
                .order_by(AIReportGeneration.created_at.desc())
                .limit(50)
                .all()
            )
            for r in reports:
                searchable = f"{r.title} {r.report_type} {r.summary or ''}".lower()
                if any(word in searchable for word in query.lower().split()):
                    results.append(
                        {
                            "type": "report",
                            "id": r.id,
                            "title": r.title,
                            "description": r.summary or r.report_type,
                            "created_at": str(r.created_at) if r.created_at else None,
                        }
                    )
        except Exception as e:
            logger.warning("Failed to search reports: %s", e)
        return results

    def _search_insights(self, query: str) -> list[dict]:
        """Search AI insights."""
        results = []
        try:
            insights = (
                self.db.query(AIInsight)
                .filter(AIInsight.is_archived.is_(False))
                .order_by(AIInsight.created_at.desc())
                .limit(50)
                .all()
            )
            for i in insights:
                searchable = f"{i.title} {i.summary}".lower()
                if any(word in searchable for word in query.lower().split()):
                    results.append(
                        {
                            "type": "insight",
                            "id": i.id,
                            "title": i.title,
                            "description": i.summary[:200],
                            "insight_type": i.insight_type,
                            "created_at": str(i.created_at) if i.created_at else None,
                        }
                    )
        except Exception as e:
            logger.warning("Failed to search insights: %s", e)
        return results

    def _search_data(self, query: str) -> list[dict]:
        """Search sales data."""
        results = []
        try:
            # Use AI to generate a SQL query for the search
            query_lower = query.lower()
            if "sales" in query_lower or "revenue" in query_lower or "profit" in query_lower:
                result = self.db.execute(
                    text(
                        "SELECT region, SUM(sales) as sales, SUM(profit) as profit "
                        "FROM sales GROUP BY region ORDER BY sales DESC LIMIT 10"
                    )
                )
                for r in result.fetchall():
                    results.append(
                        {
                            "type": "data",
                            "title": f"Sales in {r[0]}",
                            "description": f"Sales: {float(r[1]):.2f}, Profit: {float(r[2]):.2f}",
                        }
                    )
        except Exception as e:
            logger.warning("Failed to search data: %s", e)
        return results

    def _search_forecasts(self, query: str) -> list[dict]:
        """Search forecasts."""
        results = []
        try:
            forecasts = (
                self.db.query(AIForecast).order_by(AIForecast.created_at.desc()).limit(20).all()
            )
            for f in forecasts:
                if (
                    query.lower() in f.target_column.lower()
                    or query.lower() in f.forecast_type.lower()
                ):
                    results.append(
                        {
                            "type": "forecast",
                            "id": f.id,
                            "title": f"Forecast: {f.target_column}",
                            "description": f"Method: {f.method}, Horizon: {f.horizon} periods",
                            "created_at": str(f.created_at) if f.created_at else None,
                        }
                    )
        except Exception as e:
            logger.warning("Failed to search forecasts: %s", e)
        return results

    def _search_alerts(self, query: str) -> list[dict]:
        """Search anomaly alerts."""
        results = []
        try:
            alerts = (
                self.db.query(AIAnomalyAlert)
                .filter(AIAnomalyAlert.is_resolved.is_(False))
                .order_by(AIAnomalyAlert.created_at.desc())
                .limit(50)
                .all()
            )
            for a in alerts:
                searchable = f"{a.title} {a.description} {a.metric_name or ''}".lower()
                if any(word in searchable for word in query.lower().split()):
                    results.append(
                        {
                            "type": "alert",
                            "id": a.id,
                            "title": a.title,
                            "description": a.description,
                            "severity": a.severity,
                            "created_at": str(a.created_at) if a.created_at else None,
                        }
                    )
        except Exception as e:
            logger.warning("Failed to search alerts: %s", e)
        return results

    def _generate_summary(self, query: str, results: list[dict], user_id: int | None) -> str:
        """Generate an AI summary of search results."""
        if not results:
            return "No results found."
        try:
            summary_result = self.gateway.chat(
                user_message=(
                    f"Summarize these search results for the query '{query}':\n"
                    f"{json.dumps(results[:10], default=str)}\n"
                    f"Provide a brief 1-2 sentence summary."
                ),
                assistant_type="data_copilot",
                user_id=user_id,
            )
            return summary_result["response"]
        except Exception:
            return f"Found {len(results)} results for '{query}'."
