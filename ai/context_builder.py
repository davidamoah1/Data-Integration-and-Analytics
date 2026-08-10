"""AI Context Builder — constructs platform context for AI requests.

Gathers relevant data from the platform (sales, ETL jobs, pipelines, quality
reports, organizations, etc.) and structures it as context for the AI.

DATA SOURCE POLICY:
    AI context is built ONLY from:
      - User-uploaded data (passed via extra_context)
      - Connected database tables (dynamically discovered)
      - Semantic layer metadata (entity library, industry knowledge)
      - Knowledge graph
    AI must NEVER generate answers from fake, mock, or demo datasets.
"""

import logging

from sqlalchemy import inspect as sqlalchemy_inspect
from sqlalchemy import text
from sqlalchemy.orm import Session as DbSession

from etl.models import (
    ETLDataProfile,
    ETLJob,
    ETLPipeline,
    ETLQualityReport,
)

logger = logging.getLogger(__name__)


class ContextBuilder:
    """Builds platform context for AI requests."""

    def __init__(self, db: DbSession):
        self.db = db

    def build_context(
        self, assistant_type: str, user_id: int | None = None, extra_context: dict | None = None
    ) -> dict:
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
            if semantic_dataset := extra_context.get("semantic_dataset"):
                context["semantic_dataset"] = semantic_dataset

        # Enrich with semantic context if available
        context.update(self._semantic_context())

        return context

    def _semantic_context(self) -> dict:
        """Enrich AI context with semantic intelligence from the entity library."""
        ctx = {}
        try:
            from semantic.entity_library import ENTITY_LIBRARY, get_all_industries
            from semantic.industry_knowledge import INDUSTRY_KNOWLEDGE

            ctx["semantic_layer"] = {
                "available": True,
                "total_entities": len(ENTITY_LIBRARY),
                "industries": get_all_industries(),
                "entity_keys": list(ENTITY_LIBRARY.keys())[:30],
            }
            # Add industry knowledge summaries for AI reasoning
            ctx["industry_knowledge"] = {
                ind: {
                    "display_name": k["display_name"],
                    "entities": k["entities"],
                    "kpis": k["kpis"],
                    "business_rules": k["business_rules"],
                    "ai_prompts": k["ai_prompts"],
                }
                for ind, k in INDUSTRY_KNOWLEDGE.items()
            }
        except Exception as e:
            logger.warning("Failed to build semantic layer context: %s", e)
            ctx["semantic_layer"] = {"available": False}
        return ctx

    def _data_context(self) -> dict:
        """Context for data copilot — dynamically discovered dataset summary."""
        ctx = {}
        try:
            tables = self._discover_tables()
            ctx["available_tables"] = list(tables.keys())
            ctx["table_schemas"] = tables

            # If sales table exists, include a summary as a convenience
            if "sales" in tables:
                result = self.db.execute(
                    text(
                        "SELECT COUNT(*) as total_records, "
                        "COALESCE(SUM(sales), 0) as total_sales, "
                        "COALESCE(SUM(profit), 0) as total_profit, "
                        "COUNT(DISTINCT region) as regions, "
                        "COUNT(DISTINCT category) as categories "
                        "FROM sales"
                    )
                )
                row = result.fetchone()
                if row:
                    ctx["sales_summary"] = {
                        "total_records": row[0],
                        "total_sales": float(row[1]),
                        "total_profit": float(row[2]),
                        "regions": row[3],
                        "categories": row[4],
                    }
        except Exception as e:
            logger.warning("Failed to build data context: %s", e)
            ctx["note"] = "Data not available"
        return ctx

    # Tables that are internal infrastructure, not user-facing datasets
    _INTERNAL_TABLE_PREFIXES = {
        "ai_",
        "auth_",
        "audit_",
        "etl_",
        "org_",
        "department_",
        "branch_",
        "team_",
        "analytics_",
        "alembic_",
    }

    def _discover_tables(self) -> dict:
        """Dynamically discover user-facing tables and their columns."""
        result = {}
        try:
            inspector = sqlalchemy_inspect(self.db.bind)
            for table_name in inspector.get_table_names():
                if any(table_name.startswith(p) for p in self._INTERNAL_TABLE_PREFIXES):
                    continue
                columns = inspector.get_columns(table_name)
                result[table_name] = {
                    "columns": [{"name": c["name"], "type": str(c["type"])} for c in columns]
                }
        except Exception as e:
            logger.warning("Failed to discover tables: %s", e)
        return result

    def _etl_context(self) -> dict:
        """Context for ETL copilot — pipeline and job info."""
        ctx = {}
        try:
            pipelines = (
                self.db.query(ETLPipeline).filter(ETLPipeline.status == "active").limit(10).all()
            )
            ctx["active_pipelines"] = [
                {"id": p.id, "name": p.name, "version": p.current_version} for p in pipelines
            ]

            recent_jobs = self.db.query(ETLJob).order_by(ETLJob.created_at.desc()).limit(5).all()
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

            ctx["available_connectors"] = [
                "csv",
                "excel",
                "json",
                "xml",
                "mysql",
                "postgresql",
                "sqlserver",
                "oracle",
                "mariadb",
                "sqlite",
                "api",
                "graphql",
            ]
            ctx["available_transformations"] = [
                "rename",
                "drop",
                "filter",
                "fill",
                "convert",
                "calculate",
                "split",
                "merge",
                "sort",
                "deduplicate",
                "standardize",
            ]
            ctx["load_modes"] = ["insert", "update", "upsert", "incremental", "full", "batch"]
        except Exception as e:
            logger.warning("Failed to build ETL context: %s", e)
            ctx["note"] = "ETL data not available"
        return ctx

    def _dashboard_context(self) -> dict:
        """Context for dashboard copilot."""
        data_ctx = self._data_context()
        return {
            "available_chart_types": [
                "bar",
                "line",
                "pie",
                "scatter",
                "heatmap",
                "histogram",
                "area",
                "funnel",
                "gauge",
                "treemap",
                "radar",
                "sankey",
            ],
            "available_tables": data_ctx.get("available_tables", []),
            "table_schemas": data_ctx.get("table_schemas", {}),
        }

    def _report_context(self) -> dict:
        """Context for report copilot."""
        ctx = {}
        try:
            # Get recent ETL job stats
            jobs = self.db.query(ETLJob).order_by(ETLJob.created_at.desc()).limit(20).all()
            completed = [j for j in jobs if j.status == "completed"]
            failed = [j for j in jobs if j.status == "failed"]
            ctx["etl_stats"] = {
                "total_jobs": len(jobs),
                "completed": len(completed),
                "failed": len(failed),
                "success_rate": round(len(completed) / max(len(jobs), 1) * 100, 2),
            }
        except Exception as e:
            logger.warning("Failed to build report context: %s", e)
        ctx["report_types"] = [
            "executive",
            "monthly",
            "annual",
            "department",
            "quality",
            "etl",
            "performance",
            "audit",
        ]
        return ctx

    def _decision_context(self) -> dict:
        """Context for decision copilot — dataset-agnostic trends and metrics."""
        ctx = {}
        try:
            tables = self._discover_tables()
            ctx["available_tables"] = list(tables.keys())

            # If sales table exists, include region/category breakdowns as a convenience
            if "sales" in tables:
                result = self.db.execute(
                    text(
                        "SELECT region, SUM(sales) as total_sales, SUM(profit) as total_profit "
                        "FROM sales GROUP BY region ORDER BY total_sales DESC"
                    )
                )
                rows = result.fetchall()
                ctx["sales_by_region"] = [
                    {"region": r[0], "total_sales": float(r[1]), "total_profit": float(r[2])}
                    for r in rows
                ]

                result = self.db.execute(
                    text(
                        "SELECT category, SUM(sales) as total_sales "
                        "FROM sales GROUP BY category ORDER BY total_sales DESC"
                    )
                )
                rows = result.fetchall()
                ctx["sales_by_category"] = [
                    {"category": r[0], "total_sales": float(r[1])} for r in rows
                ]
        except Exception as e:
            logger.warning("Failed to build decision context: %s", e)
            ctx["note"] = "Data not available for analysis"
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
            reports = (
                self.db.query(ETLQualityReport)
                .order_by(ETLQualityReport.created_at.desc())
                .limit(5)
                .all()
            )
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

            profiles = (
                self.db.query(ETLDataProfile)
                .order_by(ETLDataProfile.created_at.desc())
                .limit(5)
                .all()
            )
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
        except Exception as e:
            logger.warning("Failed to build quality context: %s", e)
            ctx["note"] = "Quality data not available"
        return ctx

    def _sql_context(self) -> dict:
        """Context for SQL copilot — dynamically discovered table schemas."""
        return {
            "tables": self._discover_tables(),
        }
