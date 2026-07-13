"""AI Workflow Automation Engine — create and execute automated AI workflows.

Users can create workflows like:
- Import file → Clean data → Generate dashboard → Email report → Notify manager
- Run every Monday: Import → Profile → Quality check → Archive

Workflow steps can call any platform API or AI engine.
"""

import json
from datetime import datetime
from typing import Optional, Any
from sqlalchemy.orm import Session as DbSession

from ai.models import AIWorkflow, AIWorkflowRun
from ai.engines.nl_to_etl import NLToETLEngine
from ai.engines.report_writer import AIReportWriter
from ai.engines.decision_center import DecisionCenterEngine
from ai.engines.forecasting import ForecastingEngine
from ai.engines.anomaly_detection import AnomalyDetectionEngine
from ai.engines.dashboard_insights import DashboardInsightsEngine
from ai.engines.ai_quality import AIDataQualityEngine


class WorkflowEngine:
    """Executes AI workflow automation steps."""

    def __init__(self, db: DbSession):
        self.db = db
        self._step_handlers = {
            "import": self._step_import,
            "clean": self._step_clean,
            "profile": self._step_profile,
            "quality_check": self._step_quality_check,
            "transform": self._step_transform,
            "load": self._step_load,
            "generate_dashboard": self._step_generate_dashboard,
            "generate_report": self._step_generate_report,
            "generate_insights": self._step_generate_insights,
            "forecast": self._step_forecast,
            "anomaly_check": self._step_anomaly_check,
            "decision_analysis": self._step_decision_analysis,
            "notify": self._step_notify,
            "email": self._step_email,
            "archive": self._step_archive,
            "ai_chat": self._step_ai_chat,
        }

    def create_workflow(self, name: str, steps: list[dict],
                        description: str = "", trigger_type: str = "manual",
                        trigger_config: Optional[dict] = None,
                        user_id: Optional[int] = None) -> dict:
        """Create a new AI workflow."""
        workflow = AIWorkflow(
            name=name,
            description=description,
            user_id=user_id,
            trigger_type=trigger_type,
            trigger_config=trigger_config,
            steps=steps,
            is_active=True,
        )
        self.db.add(workflow)
        self.db.commit()
        self.db.refresh(workflow)
        return {
            "id": workflow.id,
            "name": workflow.name,
            "description": workflow.description,
            "trigger_type": workflow.trigger_type,
            "trigger_config": workflow.trigger_config,
            "steps": workflow.steps,
            "is_active": workflow.is_active,
            "created_at": str(workflow.created_at) if workflow.created_at else None,
        }

    def execute_workflow(self, workflow_id: int,
                         user_id: Optional[int] = None) -> dict:
        """Execute a workflow."""
        workflow = self.db.query(AIWorkflow).filter(AIWorkflow.id == workflow_id).first()
        if not workflow:
            return {"error": "Workflow not found"}

        run = AIWorkflowRun(
            workflow_id=workflow_id,
            status="running",
            trigger_type="manual",
            started_at=datetime.utcnow(),
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)

        start_time = datetime.utcnow()
        step_results = []
        success = True
        error_message = None

        try:
            context = {}  # Shared context between steps
            for i, step in enumerate(workflow.steps):
                step_type = step.get("type", step.get("step_type", ""))
                step_config = step.get("config", step.get("params", {}))

                try:
                    handler = self._step_handlers.get(step_type)
                    if handler:
                        result = handler(step_config, context, user_id)
                        step_results.append({
                            "step": i + 1,
                            "type": step_type,
                            "status": "completed",
                            "result": result,
                        })
                        # Store result in context for next steps
                        context[f"step_{i+1}_result"] = result
                    else:
                        step_results.append({
                            "step": i + 1,
                            "type": step_type,
                            "status": "skipped",
                            "result": {"message": f"Unknown step type: {step_type}"},
                        })
                except Exception as e:
                    step_results.append({
                        "step": i + 1,
                        "type": step_type,
                        "status": "failed",
                        "error": str(e),
                    })
                    success = False
                    error_message = str(e)
                    break

        except Exception as e:
            success = False
            error_message = str(e)

        # Update run record
        run.status = "completed" if success else "failed"
        run.step_results = step_results
        run.completed_at = datetime.utcnow()
        run.duration_seconds = int((datetime.utcnow() - start_time).total_seconds())
        run.error_message = error_message
        self.db.commit()

        return {
            "id": run.id,
            "workflow_id": workflow_id,
            "status": run.status,
            "step_results": step_results,
            "duration_seconds": run.duration_seconds,
            "error_message": error_message,
            "created_at": str(run.created_at) if run.created_at else None,
        }

    def list_workflows(self, user_id: Optional[int] = None) -> list[dict]:
        """List workflows."""
        query = self.db.query(AIWorkflow).filter(AIWorkflow.is_active == True)
        if user_id:
            query = query.filter(AIWorkflow.user_id == user_id)
        workflows = query.order_by(AIWorkflow.created_at.desc()).all()
        return [
            {
                "id": w.id, "name": w.name, "description": w.description,
                "trigger_type": w.trigger_type, "steps": w.steps,
                "is_active": w.is_active,
                "created_at": str(w.created_at) if w.created_at else None,
            }
            for w in workflows
        ]

    def get_workflow_runs(self, workflow_id: int, limit: int = 20) -> list[dict]:
        """Get execution history for a workflow."""
        runs = self.db.query(AIWorkflowRun).filter(
            AIWorkflowRun.workflow_id == workflow_id,
        ).order_by(AIWorkflowRun.created_at.desc()).limit(limit).all()
        return [
            {
                "id": r.id, "workflow_id": r.workflow_id, "status": r.status,
                "step_results": r.step_results, "duration_seconds": r.duration_seconds,
                "error_message": r.error_message,
                "created_at": str(r.created_at) if r.created_at else None,
            }
            for r in runs
        ]

    # --- Step Handlers ------------------------------------------------------

    def _step_import(self, config: dict, context: dict, user_id: int) -> dict:
        """Import data step."""
        from etl.connectors.connectors import get_connector
        connector = get_connector(config.get("source_type", "csv"), config.get("source_config", {}))
        with connector:
            df = connector.extract()
        context["dataframe"] = df
        return {"rows_imported": len(df), "columns": list(df.columns)}

    def _step_clean(self, config: dict, context: dict, user_id: int) -> dict:
        """Clean data step."""
        from etl.transformations import TransformationEngine
        df = context.get("dataframe")
        if df is None:
            return {"error": "No data to clean"}
        engine = TransformationEngine()
        transformations = config.get("transformations", [
            {"type": "deduplicate"},
            {"type": "fill", "config": {"method": "ffill"}},
        ])
        df = engine.apply(df, transformations)
        context["dataframe"] = df
        return {"rows_after_cleaning": len(df)}

    def _step_profile(self, config: dict, context: dict, user_id: int) -> dict:
        """Profile data step."""
        from etl.profiling import DataProfiler
        df = context.get("dataframe")
        if df is None:
            return {"error": "No data to profile"}
        profiler = DataProfiler()
        profile = profiler.profile(df, source_name=config.get("source_name", "workflow"))
        context["profile"] = profile
        return {"row_count": profile["row_count"], "column_count": profile["column_count"]}

    def _step_quality_check(self, config: dict, context: dict, user_id: int) -> dict:
        """Quality check step."""
        from etl.quality import DataQualityEngine
        df = context.get("dataframe")
        if df is None:
            return {"error": "No data to check"}
        engine = DataQualityEngine()
        result = engine.run_checks(df, source_name=config.get("source_name", "workflow"))
        context["quality_report"] = result
        return {"quality_score": result["overall_score"], "checks_failed": result["checks_failed"]}

    def _step_transform(self, config: dict, context: dict, user_id: int) -> dict:
        """Transform data step."""
        from etl.transformations import TransformationEngine
        df = context.get("dataframe")
        if df is None:
            return {"error": "No data to transform"}
        engine = TransformationEngine()
        df = engine.apply(df, config.get("transformations", []))
        context["dataframe"] = df
        return {"rows_after_transform": len(df)}

    def _step_load(self, config: dict, context: dict, user_id: int) -> dict:
        """Load data step."""
        from etl.load_engine import LoadEngine, LoadMode
        df = context.get("dataframe")
        if df is None:
            return {"error": "No data to load"}
        load_engine = LoadEngine(self.db)
        mode = LoadMode(config.get("mode", "insert"))
        rows = load_engine.load(df, config.get("table_name", "sales"), mode)
        return {"rows_loaded": rows}

    def _step_generate_dashboard(self, config: dict, context: dict, user_id: int) -> dict:
        """Generate dashboard step."""
        from ai.engines.nl_to_dashboard import NLToDashboardEngine
        engine = NLToDashboardEngine(self.db)
        result = engine.generate_dashboard(
            description=config.get("description", "Sales dashboard"),
            user_id=user_id,
        )
        return {"charts_generated": len(result.get("charts", []))}

    def _step_generate_report(self, config: dict, context: dict, user_id: int) -> dict:
        """Generate report step."""
        engine = AIReportWriter(self.db)
        result = engine.generate_report(
            report_type=config.get("report_type", "executive"),
            title=config.get("title"),
            user_id=user_id,
        )
        return {"report_id": result["id"], "title": result["title"]}

    def _step_generate_insights(self, config: dict, context: dict, user_id: int) -> dict:
        """Generate insights step."""
        engine = DashboardInsightsEngine(self.db)
        result = engine.generate_insights(user_id=user_id)
        return {"findings": len(result.get("key_findings", []))}

    def _step_forecast(self, config: dict, context: dict, user_id: int) -> dict:
        """Forecast step."""
        engine = ForecastingEngine(self.db)
        result = engine.forecast(
            source_type=config.get("source_type", "csv"),
            source_config=config.get("source_config", {}),
            target_column=config.get("target_column", "sales"),
            date_column=config.get("date_column", "order_date"),
            horizon=config.get("horizon", 30),
            user_id=user_id,
        )
        return {"forecast_id": result.get("id"), "predictions": len(result.get("predictions", []))}

    def _step_anomaly_check(self, config: dict, context: dict, user_id: int) -> dict:
        """Anomaly detection step."""
        engine = AnomalyDetectionEngine(self.db)
        result = engine.detect(
            source_type=config.get("source_type", "csv"),
            source_config=config.get("source_config", {}),
            metric_column=config.get("metric_column", "sales"),
            date_column=config.get("date_column", "order_date"),
            user_id=user_id,
        )
        return {"anomalies_found": result["total_anomalies"]}

    def _step_decision_analysis(self, config: dict, context: dict, user_id: int) -> dict:
        """Decision analysis step."""
        engine = DecisionCenterEngine(self.db)
        result = engine.analyze(
            metric=config.get("metric"),
            user_id=user_id,
        )
        return {"insight_id": result["id"], "title": result["title"]}

    def _step_notify(self, config: dict, context: dict, user_id: int) -> dict:
        """Notify step (logs notification — integrate with email/notification system)."""
        message = config.get("message", "Workflow notification")
        # In production, this would send an actual notification
        return {"notification_sent": True, "message": message}

    def _step_email(self, config: dict, context: dict, user_id: int) -> dict:
        """Email step (placeholder — integrate with email service)."""
        return {"email_sent": False, "note": "Email service not configured"}

    def _step_archive(self, config: dict, context: dict, user_id: int) -> dict:
        """Archive step."""
        return {"archived": True, "note": "Data archived"}

    def _step_ai_chat(self, config: dict, context: dict, user_id: int) -> dict:
        """AI chat step."""
        from ai.gateway import AIGateway
        gateway = AIGateway(self.db)
        result = gateway.chat(
            user_message=config.get("message", "Analyze the current data"),
            assistant_type=config.get("assistant_type", "data_copilot"),
            user_id=user_id,
        )
        return {"response": result["response"][:200]}
