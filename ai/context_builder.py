"""AI Context Builder — constructs platform context for AI requests.

Gathers relevant data from the platform (sales, ETL jobs, pipelines, quality
reports, organizations, etc.) and structures it as context for the AI.
"""

import json
from typing import Optional
from sqlalchemy.orm import Session as DbSession
from sqlalchemy import text

from ai.models import (
    AIConversation,
)
from etl.models import (
    ETLPipeline, ETLJob, ETLDataProfile, ETLQualityReport,
    ETLPipelineVersion, ETLDataLineage,
)


class ContextBuilder:
    """Builds platform context for AI requests."""

    def __init__(self, db: DbSession):
        self.db = db

    def build_context(self, assistant_type: str, user_id: Optional[int] = None,
                      extra_context: Optional[dict] = None) -> dict:
        """Build context based on assistant type and user.

        Returns a dict of platform data relevant to the request.
        """
        context = {
            "platform": "DataFlow Enterprise Data Intelligence Platform",
            "assistant_type": assistant_type,
        }

        # Add user info
        if user_id:
            context["user_id"] = user_id

        # Add assistant-specific context
        if assistant_type == "data_copilot":
            context.update(self._data_context())
        elif assistant_type == "etl_copilot":
            context.update(self._etl_context())
        elif assistant_type == "dashboard_copilot":
            context.update(self._dashboard_context())
        elif assistant_type == "report_copilot":
            context.update(self._report_context())
        elif assistant_type == "decision_copilot":
            context.update(self._decision_context())
        elif assistant_type == "forecast_copilot":
            context.update(self._forecast_context())
        elif assistant_type == "quality_copilot":
            context.update(self._quality_context())
        elif assistant_type == "sql_copilot":
            context.update(self._sql_context())

        # Merge extra context
        if extra_context:
            context["user_context"] = extra_context

        return context

    def _data_context(self) -> dict:
        """Context for data copilot — sales data summary."""
        ctx = {}
        try:
            # Get sales summary
            result = self.db.execute(text(
                "SELECT COUNT(*) as total_records, "
                "COALESCE(SUM(sales), 0) as total_sales, "
                "COALESCE(SUM(profit), 0) as total_profit, "
                "COUNT(DISTINCT region) as regions, "
                "COUNT(DISTINCT category) as categories "
                "FROM sales"
            ))
            row = result.fetchone()
            if row:
                ctx["sales_summary"] = {
                    "total_records": row[0],
                    "total_sales": float(row[1]),
                    "total_profit": float(row[2]),
                    "regions": row[3],
                    "categories": row[4],
                }

            # Get column info
            ctx["sales_columns"] = [
                "order_id", "order_date", "ship_date", "customer_name",
                "segment", "region", "category", "sub_category",
                "product_name", "sales", "quantity", "discount", "profit",
            ]
        except Exception:
            ctx["sales_summary"] = {"note": "Sales data not available"}
        return ctx

    def _etl_context(self) -> dict:
        """Context for ETL copilot — pipeline and job info."""
        ctx = {}
        try:
            pipelines = self.db.query(ETLPipeline).filter(
                ETLPipeline.status == "active"
            ).limit(10).all()
            ctx["active_pipelines"] = [
                {"id": p.id, "name": p.name, "version": p.current_version}
                for p in pipelines
            ]

            recent_jobs = self.db.query(ETLJob).order_by(
                ETLJob.created_at.desc()
            ).limit(5).all()
            ctx["recent_jobs"] = [
                {
                    "id": j.id,
                    "type": j.job_type,
                    "status": j.status,
                    "rows_extracted": j.rows_extracted,
                    "rows_loaded": j.rows_loaded,
                }
                for j in recent_jobs
            ]

            ctx["available_connectors"] = ["csv", "excel", "json", "xml", "mysql", "api"]
            ctx["available_transformations"] = [
                "rename", "drop", "filter", "fill", "convert", "calculate",
                "split", "merge", "sort", "deduplicate", "standardize",
            ]
            ctx["load_modes"] = ["insert", "update", "upsert", "incremental", "full", "batch"]
        except Exception:
            ctx["note"] = "ETL data not available"
        return ctx

    def _dashboard_context(self) -> dict:
        """Context for dashboard copilot."""
        return {
            "available_chart_types": [
                "bar", "line", "pie", "scatter", "heatmap", "histogram",
                "area", "funnel", "gauge",
            ],
            "data_columns": self._data_context().get("sales_columns", []),
        }

    def _report_context(self) -> dict:
        """Context for report copilot."""
        ctx = {}
        try:
            # Get recent ETL job stats
            jobs = self.db.query(ETLJob).order_by(
                ETLJob.created_at.desc()
            ).limit(20).all()
            completed = [j for j in jobs if j.status == "completed"]
            failed = [j for j in jobs if j.status == "failed"]
            ctx["etl_stats"] = {
                "total_jobs": len(jobs),
                "completed": len(completed),
                "failed": len(failed),
                "success_rate": round(len(completed) / max(len(jobs), 1) * 100, 2),
            }
        except Exception:
            pass
        ctx["report_types"] = [
            "executive", "monthly", "annual", "department",
            "quality", "etl", "performance", "audit",
        ]
        return ctx

    def _decision_context(self) -> dict:
        """Context for decision copilot — sales trends and metrics."""
        ctx = {}
        try:
            result = self.db.execute(text(
                "SELECT region, SUM(sales) as total_sales, SUM(profit) as total_profit "
                "FROM sales GROUP BY region ORDER BY total_sales DESC"
            ))
            rows = result.fetchall()
            ctx["sales_by_region"] = [
                {"region": r[0], "total_sales": float(r[1]), "total_profit": float(r[2])}
                for r in rows
            ]

            result = self.db.execute(text(
                "SELECT category, SUM(sales) as total_sales "
                "FROM sales GROUP BY category ORDER BY total_sales DESC"
            ))
            rows = result.fetchall()
            ctx["sales_by_category"] = [
                {"category": r[0], "total_sales": float(r[1])}
                for r in rows
            ]
        except Exception:
            ctx["note"] = "Sales data not available for analysis"
        return ctx

    def _forecast_context(self) -> dict:
        """Context for forecast copilot."""
        return {
            "available_methods": ["linear", "exponential", "moving_average", "seasonal", "arima"],
            "max_horizon": 365,
            "confidence_levels": [0.80, 0.90, 0.95, 0.99],
        }

    def _quality_context(self) -> dict:
        """Context for quality copilot — recent quality reports."""
        ctx = {}
        try:
            reports = self.db.query(ETLQualityReport).order_by(
                ETLQualityReport.created_at.desc()
            ).limit(5).all()
            ctx["recent_quality_reports"] = [
                {
                    "id": r.id,
                    "source_name": r.source_name,
                    "overall_score": r.overall_score,
                    "checks_passed": r.checks_passed,
                    "checks_failed": r.checks_failed,
                }
                for r in reports
            ]

            profiles = self.db.query(ETLDataProfile).order_by(
                ETLDataProfile.created_at.desc()
            ).limit(5).all()
            ctx["recent_profiles"] = [
                {
                    "id": p.id,
                    "source_name": p.source_name,
                    "row_count": p.row_count,
                    "column_count": p.column_count,
                    "quality_score": p.quality_score,
                }
                for p in profiles
            ]
        except Exception:
            ctx["note"] = "Quality data not available"
        return ctx

    def _sql_context(self) -> dict:
        """Context for SQL copilot — table schemas."""
        return {
            "tables": {
                "sales": {
                    "columns": [
                        {"name": "order_id", "type": "VARCHAR(50)"},
                        {"name": "order_date", "type": "DATE"},
                        {"name": "ship_date", "type": "DATE"},
                        {"name": "customer_name", "type": "VARCHAR(255)"},
                        {"name": "segment", "type": "VARCHAR(100)"},
                        {"name": "region", "type": "VARCHAR(100)"},
                        {"name": "category", "type": "VARCHAR(100)"},
                        {"name": "sub_category", "type": "VARCHAR(100)"},
                        {"name": "product_name", "type": "VARCHAR(500)"},
                        {"name": "sales", "type": "FLOAT"},
                        {"name": "quantity", "type": "INTEGER"},
                        {"name": "discount", "type": "FLOAT"},
                        {"name": "profit", "type": "FLOAT"},
                    ],
                },
                "pipeline_runs": {
                    "columns": [
                        {"name": "run_id", "type": "VARCHAR(50)"},
                        {"name": "started_at", "type": "TIMESTAMP"},
                        {"name": "completed_at", "type": "TIMESTAMP"},
                        {"name": "status", "type": "VARCHAR(20)"},
                        {"name": "rows_extracted", "type": "INTEGER"},
                        {"name": "rows_transformed", "type": "INTEGER"},
                        {"name": "rows_loaded", "type": "INTEGER"},
                        {"name": "error_message", "type": "VARCHAR(1000)"},
                    ],
                },
            },
        }
