"""Enterprise Dataset Workflow Orchestrator.

Manages the full dataset intelligence pipeline:
  Upload → Validate → Profile → Quality Check → Semantic Analysis
  → Industry Detection → Metadata Generation → Business Knowledge
  → AI Insights → Dashboard Recommendation → Analysis Complete

Each stage:
  - Saves status
  - Logs execution time
  - Handles errors
  - Supports retries
  - Emits progress events
"""

from __future__ import annotations

import logging
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def _json_safe(obj):
    """Recursively convert numpy/pandas types to JSON-serializable Python types."""
    if isinstance(obj, dict):
        return {k: _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_safe(v) for v in obj]
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj) if not np.isnan(obj) else None
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, (pd.Timestamp,)):
        return obj.isoformat()
    if hasattr(obj, "item"):  # numpy scalar fallback
        return obj.item()
    return obj


class WorkflowStage(str, Enum):
    UPLOADED = "uploaded"
    VALIDATED = "validated"
    PROFILED = "profiled"
    QUALITY_CHECKED = "quality_checked"
    SEMANTICALLY_ANALYZED = "semantically_analyzed"
    INDUSTRY_IDENTIFIED = "industry_identified"
    METADATA_GENERATED = "metadata_generated"
    KNOWLEDGE_EXTRACTED = "knowledge_extracted"
    INSIGHTS_GENERATED = "insights_generated"
    DASHBOARD_READY = "dashboard_ready"
    ANALYSIS_COMPLETE = "analysis_complete"


class StageStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


STAGE_ORDER = [
    WorkflowStage.UPLOADED,
    WorkflowStage.VALIDATED,
    WorkflowStage.PROFILED,
    WorkflowStage.QUALITY_CHECKED,
    WorkflowStage.SEMANTICALLY_ANALYZED,
    WorkflowStage.INDUSTRY_IDENTIFIED,
    WorkflowStage.METADATA_GENERATED,
    WorkflowStage.KNOWLEDGE_EXTRACTED,
    WorkflowStage.INSIGHTS_GENERATED,
    WorkflowStage.DASHBOARD_READY,
    WorkflowStage.ANALYSIS_COMPLETE,
]


@dataclass
class StageResult:
    """Result of a single workflow stage."""

    stage: WorkflowStage
    status: StageStatus
    started_at: str = ""
    completed_at: str = ""
    duration_seconds: float = 0.0
    result: dict = field(default_factory=dict)
    error: str | None = None
    retries: int = 0

    def to_dict(self) -> dict:
        return _json_safe({
            "stage": self.stage.value,
            "status": self.status.value,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration_seconds": round(self.duration_seconds, 3),
            "result": self.result,
            "error": self.error,
            "retries": self.retries,
        })


@dataclass
class WorkflowState:
    """Full state of a dataset workflow run."""

    workflow_id: str
    dataset_name: str
    created_by: int | None = None
    organization_id: int | None = None
    current_stage: WorkflowStage = WorkflowStage.UPLOADED
    stages: dict[WorkflowStage, StageResult] = field(default_factory=dict)
    context: dict = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    is_complete: bool = False
    has_errors: bool = False

    def to_dict(self) -> dict:
        return {
            "workflow_id": self.workflow_id,
            "dataset_name": self.dataset_name,
            "created_by": self.created_by,
            "organization_id": self.organization_id,
            "current_stage": self.current_stage.value,
            "stages": {s.value: r.to_dict() for s, r in self.stages.items()},
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "is_complete": self.is_complete,
            "has_errors": self.has_errors,
        }


class DatasetWorkflowOrchestrator:
    """Orchestrates the full dataset intelligence workflow.

    Usage:
        orchestrator = DatasetWorkflowOrchestrator()
        state = orchestrator.start(df, dataset_name="sales_data.csv")
        # state.to_dict() → JSON-serializable progress
    """

    MAX_RETRIES = 2

    def __init__(self, max_retries: int | None = None):
        self.max_retries = max_retries or self.MAX_RETRIES
        self._progress_callbacks: list[Callable[[WorkflowState], None]] = []
        # In-process lookup for active workflow states. Every stage
        # transition is also durably persisted to the dataset_workflow_runs
        # table via _persist_workflow_state (registered as a progress
        # callback in dataset_workflow_routes.py), so status/results
        # survive restarts and are visible to other worker processes.
        self._workflows: dict[str, WorkflowState] = {}
        # Cache for completed workflows by dataset hash
        self._cache: dict[str, WorkflowState] = {}

    def on_progress(self, callback: Callable[[WorkflowState], None]) -> None:
        """Register a progress callback."""
        self._progress_callbacks.append(callback)

    def _emit_progress(self, state: WorkflowState) -> None:
        """Emit progress to all callbacks."""
        for cb in self._progress_callbacks:
            try:
                cb(state)
            except Exception as e:
                logger.warning(f"Progress callback error: {e}")

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def start(
        self,
        df: pd.DataFrame,
        dataset_name: str = "uploaded_dataset",
        admin_confirmed: bool = False,
        overrides: dict | None = None,
        created_by: int | None = None,
        organization_id: int | None = None,
    ) -> WorkflowState:
        """Start a new dataset workflow.

        Args:
            df: The uploaded DataFrame.
            dataset_name: Name of the dataset.
            admin_confirmed: Whether admin has confirmed industry detection.
            overrides: Optional column-to-entity overrides.
            created_by: User id that initiated the workflow.
            organization_id: Organization the workflow belongs to.

        Returns:
            WorkflowState after all stages complete (or fail).
        """
        # Check cache for identical dataset
        dataset_hash = self._compute_hash(df, dataset_name)
        cached_state = self._check_cache(dataset_hash)
        if cached_state:
            logger.info(f"Cache hit for dataset hash {dataset_hash[:8]}")
            # The cache is keyed only by dataset content + name, not by
            # caller, so re-attribute ownership to the CURRENT caller rather
            # than leaving whichever created_by/organization_id the dataset
            # was originally cached under. Without this, a second
            # organization uploading content-identical data (e.g. the same
            # sample file) would get back a workflow attributed to the
            # first organization - a cross-tenant data attribution bug.
            cached_state.created_by = created_by
            cached_state.organization_id = organization_id
            cached_state.context["admin_confirmed"] = admin_confirmed
            cached_state.context["overrides"] = overrides or {}
            # Register the cache-hit workflow under its own (new) workflow_id
            # and emit progress for it, same as a freshly-run workflow, so
            # get_state() and any persistence callbacks (see
            # services/dataset_workflow_routes.py) work for cache hits too -
            # without this, a cache-hit workflow_id would be returned to the
            # caller but any later status lookup for it would 404.
            self._workflows[cached_state.workflow_id] = cached_state
            self._emit_progress(cached_state)
            return cached_state

        workflow_id = str(uuid.uuid4())
        state = WorkflowState(
            workflow_id=workflow_id,
            dataset_name=dataset_name,
            created_by=created_by,
            organization_id=organization_id,
        )
        state.context["df"] = df
        state.context["admin_confirmed"] = admin_confirmed
        state.context["overrides"] = overrides or {}
        self._workflows[workflow_id] = state

        # Initialize all stages as pending
        for stage in STAGE_ORDER:
            state.stages[stage] = StageResult(stage=stage, status=StageStatus.PENDING)

        # Stage 1: Uploaded
        self._run_stage(state, WorkflowStage.UPLOADED, self._stage_uploaded)

        # Stage 2: Validated
        self._run_stage(state, WorkflowStage.VALIDATED, self._stage_validated)

        # Stage 3: Profiled
        self._run_stage(state, WorkflowStage.PROFILED, self._stage_profiled)

        # Stage 4: Quality Checked
        self._run_stage(state, WorkflowStage.QUALITY_CHECKED, self._stage_quality_checked)

        # Stage 5: Semantically Analyzed
        self._run_stage(
            state, WorkflowStage.SEMANTICALLY_ANALYZED, self._stage_semantically_analyzed
        )

        # Stage 6: Industry Identified
        self._run_stage(state, WorkflowStage.INDUSTRY_IDENTIFIED, self._stage_industry_identified)

        # Stage 7: Metadata Generated
        self._run_stage(state, WorkflowStage.METADATA_GENERATED, self._stage_metadata_generated)

        # Stage 8: Knowledge Extracted
        self._run_stage(state, WorkflowStage.KNOWLEDGE_EXTRACTED, self._stage_knowledge_extracted)

        # Stage 9: Insights Generated
        self._run_stage(state, WorkflowStage.INSIGHTS_GENERATED, self._stage_insights_generated)

        # Stage 10: Dashboard Ready
        self._run_stage(state, WorkflowStage.DASHBOARD_READY, self._stage_dashboard_ready)

        # Stage 11: Analysis Complete
        self._run_stage(state, WorkflowStage.ANALYSIS_COMPLETE, self._stage_analysis_complete)

        state.is_complete = not state.has_errors
        state.updated_at = self._now()
        # Cache the completed workflow
        if state.is_complete:
            self._save_cache(dataset_hash, state)
        self._emit_progress(state)
        return state

    def retry_stage(self, workflow_id: str, stage: WorkflowStage) -> WorkflowState | None:
        """Retry a failed stage and all subsequent stages."""
        state = self._workflows.get(workflow_id)
        if not state:
            return None

        stage_idx = STAGE_ORDER.index(stage)
        for s in STAGE_ORDER[stage_idx:]:
            handler = self._stage_handlers().get(s)
            if handler:
                self._run_stage(state, s, handler)

        state.is_complete = not state.has_errors
        state.updated_at = self._now()
        self._emit_progress(state)
        return state

    def get_state(self, workflow_id: str) -> WorkflowState | None:
        """Get the current state of a workflow."""
        return self._workflows.get(workflow_id)

    def _run_stage(
        self,
        state: WorkflowState,
        stage: WorkflowStage,
        handler: Callable[[WorkflowState], dict],
    ) -> None:
        """Run a single stage with retries."""
        result = state.stages[stage]
        result.status = StageStatus.RUNNING
        result.started_at = self._now()
        state.current_stage = stage
        state.updated_at = self._now()
        self._emit_progress(state)

        start_time = time.time()
        retries = 0
        last_error = None

        while retries <= self.max_retries:
            try:
                stage_result = handler(state)
                result.result = stage_result
                result.status = StageStatus.COMPLETED
                result.completed_at = self._now()
                result.duration_seconds = time.time() - start_time
                result.retries = retries
                state.updated_at = self._now()
                self._emit_progress(state)
                return
            except Exception as e:
                last_error = str(e)
                retries += 1
                if retries <= self.max_retries:
                    logger.warning(
                        f"Stage {stage.value} failed (attempt {retries}): {e}. Retrying..."
                    )
                    time.sleep(0.5 * retries)
                else:
                    logger.error(f"Stage {stage.value} failed after {retries} attempts: {e}")

        result.status = StageStatus.FAILED
        result.error = last_error
        result.completed_at = self._now()
        result.duration_seconds = time.time() - start_time
        result.retries = retries - 1
        state.has_errors = True
        state.updated_at = self._now()
        self._emit_progress(state)

    # ─── Stage Handlers ─────────────────────────────────────────

    def _stage_handlers(self) -> dict[WorkflowStage, Callable]:
        return {
            WorkflowStage.UPLOADED: self._stage_uploaded,
            WorkflowStage.VALIDATED: self._stage_validated,
            WorkflowStage.PROFILED: self._stage_profiled,
            WorkflowStage.QUALITY_CHECKED: self._stage_quality_checked,
            WorkflowStage.SEMANTICALLY_ANALYZED: self._stage_semantically_analyzed,
            WorkflowStage.INDUSTRY_IDENTIFIED: self._stage_industry_identified,
            WorkflowStage.METADATA_GENERATED: self._stage_metadata_generated,
            WorkflowStage.KNOWLEDGE_EXTRACTED: self._stage_knowledge_extracted,
            WorkflowStage.INSIGHTS_GENERATED: self._stage_insights_generated,
            WorkflowStage.DASHBOARD_READY: self._stage_dashboard_ready,
            WorkflowStage.ANALYSIS_COMPLETE: self._stage_analysis_complete,
        }

    def _stage_uploaded(self, state: WorkflowState) -> dict:
        """Stage 1: Record upload metadata."""
        df = state.context["df"]
        return {
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": list(df.columns),
            "memory_mb": round(df.memory_usage(deep=True).sum() / 1024 / 1024, 2),
        }

    def _stage_validated(self, state: WorkflowState) -> dict:
        """Stage 2: Validate file structure and basic data integrity."""
        df = state.context["df"]
        issues = []

        if df.empty:
            raise ValueError("Dataset is empty")
        if len(df.columns) == 0:
            raise ValueError("Dataset has no columns")

        # Check for completely empty columns
        empty_cols = [c for c in df.columns if df[c].isna().all()]
        if empty_cols:
            issues.append({"severity": "warning", "issue": "Empty columns", "columns": empty_cols})

        # Check for duplicate column names
        dup_cols = df.columns[df.columns.duplicated()].tolist()
        if dup_cols:
            issues.append(
                {"severity": "error", "issue": "Duplicate column names", "columns": dup_cols}
            )

        state.context["validation_issues"] = issues
        return {
            "is_valid": len([i for i in issues if i["severity"] == "error"]) == 0,
            "issues": issues,
        }

    def _stage_profiled(self, state: WorkflowState) -> dict:
        """Stage 3: Generate comprehensive data profile."""
        from services.enterprise_profiler import EnterpriseDataProfiler

        df = state.context["df"]
        profiler = EnterpriseDataProfiler()
        profile = profiler.profile(df, source_name=state.dataset_name)
        state.context["profile"] = profile
        return profile

    def _stage_quality_checked(self, state: WorkflowState) -> dict:
        """Stage 4: Run AI data quality assessment."""
        from data_quality.quality_engine import QualityEngine

        df = state.context["df"]
        engine = QualityEngine()
        result = engine.run(df)
        quality_dict = result.to_dict()
        state.context["quality_report"] = quality_dict
        return quality_dict

    def _stage_semantically_analyzed(self, state: WorkflowState) -> dict:
        """Stage 5: Run semantic analysis (column-to-entity mapping)."""
        from semantic.mapping_engine import SemanticMappingEngine

        df = state.context["df"]
        overrides = state.context.get("overrides", {})
        mapping_result = SemanticMappingEngine.analyze(df, state.dataset_name, overrides)
        semantic_dict = mapping_result.semantic_result.to_dict()
        state.context["mapping_result"] = mapping_result
        state.context["semantic_result"] = semantic_dict
        return semantic_dict

    def _stage_industry_identified(self, state: WorkflowState) -> dict:
        """Stage 6: Detect industry with confidence and evidence."""
        mapping_result = state.context.get("mapping_result")
        if not mapping_result:
            raise ValueError("Semantic analysis not completed")

        industry = mapping_result.industry
        confidence = mapping_result.industry_confidence
        entities = mapping_result.business_entities

        # Get alternative candidates from value signals
        alternatives = []
        if hasattr(mapping_result, "value_signals") and mapping_result.value_signals:
            industry_votes: dict[str, float] = {}
            for signal in mapping_result.value_signals:
                ind = signal.get("industry", "unknown")
                industry_votes[ind] = industry_votes.get(ind, 0) + signal.get("weight", 1.0)
            alternatives = [
                {"industry": k, "votes": v}
                for k, v in sorted(industry_votes.items(), key=lambda x: -x[1])
                if k != industry
            ][:3]

        result = {
            "industry": industry,
            "confidence": round(confidence, 2),
            "detected_entities": entities,
            "alternative_candidates": alternatives,
            "needs_confirmation": confidence < 70.0
            and not state.context.get("admin_confirmed", False),
        }
        state.context["industry_result"] = result
        return result

    def _stage_metadata_generated(self, state: WorkflowState) -> dict:
        """Stage 7: Generate business metadata."""
        from semantic.metadata_extractor import MetadataExtractor

        df = state.context["df"]
        metadata = MetadataExtractor.extract(df, state.dataset_name)
        metadata_dict = metadata.to_dict()
        state.context["metadata"] = metadata_dict
        return metadata_dict

    def _stage_knowledge_extracted(self, state: WorkflowState) -> dict:
        """Stage 8: Extract business knowledge (entities, relationships, KPIs)."""
        mapping_result = state.context.get("mapping_result")
        if not mapping_result:
            raise ValueError("Semantic mapping not available")

        from semantic.knowledge_graph import KnowledgeGraphBuilder
        from semantic.kpi_generator import KPIGenerator

        df = state.context["df"]
        knowledge_graph = KnowledgeGraphBuilder.build(mapping_result)
        kpi_result = KPIGenerator.generate(df, mapping_result)

        result = {
            "knowledge_graph": knowledge_graph.to_dict(),
            "kpis": kpi_result.to_dict(),
            "business_entities": mapping_result.business_entities,
            "business_concepts": mapping_result.business_concepts,
            "recommendations": mapping_result.recommendations,
        }
        state.context["business_knowledge"] = result
        return result

    def _stage_insights_generated(self, state: WorkflowState) -> dict:
        """Stage 9: Generate AI insights."""
        from ai_copilot.insight_generator import InsightGenerator

        df = state.context["df"]
        mapping_result = state.context.get("mapping_result")
        col_mapping = {}
        if mapping_result and hasattr(mapping_result, "semantic_result"):
            for m in mapping_result.semantic_result.mappings:
                col_mapping[m.column_name] = m.entity_key

        insights = InsightGenerator.generate(df, col_mapping=col_mapping)
        insights_dict = [i.to_dict() for i in insights]

        # Generate executive summary
        executive_summary = self._generate_executive_summary(insights_dict, state)

        result = {
            "insights": insights_dict,
            "executive_summary": executive_summary,
            "total_insights": len(insights_dict),
        }
        state.context["insights"] = result
        return result

    def _stage_dashboard_ready(self, state: WorkflowState) -> dict:
        """Stage 10: Generate dashboard recommendations."""
        from services.dashboard_recommender import DashboardRecommendationEngine

        df = state.context["df"]
        mapping_result = state.context.get("mapping_result")
        admin_confirmed = state.context.get("admin_confirmed", False)

        engine = DashboardRecommendationEngine()
        recommendations = engine.recommend(df, mapping_result, admin_confirmed=admin_confirmed)
        state.context["dashboard_recommendations"] = recommendations
        return recommendations

    def _stage_analysis_complete(self, state: WorkflowState) -> dict:
        """Stage 11: Finalize and produce summary."""
        profile = state.context.get("profile", {})
        quality = state.context.get("quality_report", {})
        industry = state.context.get("industry_result", {})
        insights = state.context.get("insights", {})
        dashboard = state.context.get("dashboard_recommendations", {})

        return {
            "dataset_name": state.dataset_name,
            "row_count": profile.get("row_count", 0),
            "column_count": profile.get("column_count", 0),
            "quality_score": (
                quality.get("score", {}).get("overall", 0)
                if isinstance(quality.get("score"), dict)
                else 0
            ),
            "industry": industry.get("industry", "unknown"),
            "industry_confidence": industry.get("confidence", 0),
            "total_insights": insights.get("total_insights", 0),
            "dashboard_recommended": dashboard.get("recommended", False),
            "dashboard_title": dashboard.get("title", ""),
        }

    def _generate_executive_summary(self, insights: list[dict], state: WorkflowState) -> str:
        """Generate a brief executive summary from insights."""
        profile = state.context.get("profile", {})
        industry = state.context.get("industry_result", {})
        quality = state.context.get("quality_report", {})

        row_count = profile.get("row_count", 0)
        col_count = profile.get("column_count", 0)
        industry_name = industry.get("industry", "unknown")
        quality_score = 0
        if isinstance(quality.get("score"), dict):
            quality_score = quality["score"].get("overall", 0)

        critical_count = sum(1 for i in insights if i.get("severity") == "critical")
        positive_count = sum(1 for i in insights if i.get("severity") == "positive")

        summary_parts = [
            f"Dataset contains {row_count:,} records across {col_count} columns.",
            f"Industry detected as '{industry_name.title()}' with {industry.get('confidence', 0):.0f}% confidence.",
            f"Data quality score: {quality_score:.0f}/100.",
        ]
        if critical_count:
            summary_parts.append(f"{critical_count} critical issue(s) detected.")
        if positive_count:
            summary_parts.append(f"{positive_count} positive trend(s) identified.")
        if not insights:
            summary_parts.append("No significant insights detected.")

        return " ".join(summary_parts)

    # ─── Caching ─────────────────────────────────────────

    def _compute_hash(self, df: pd.DataFrame, name: str) -> str:
        """Compute a hash for a dataset to use as cache key."""
        import hashlib as hl

        # Hash: shape + first/last rows + column names + name
        parts = [
            name,
            str(df.shape),
            ",".join(str(c) for c in df.columns),
            df.head(5).to_csv(index=False),
            df.tail(5).to_csv(index=False),
        ]
        return hl.sha256("|".join(parts).encode()).hexdigest()

    def _check_cache(self, dataset_hash: str) -> WorkflowState | None:
        """Check if a workflow result is cached for this dataset hash."""
        cache_key = f"workflow:{dataset_hash}"
        cached = self._cache.get(cache_key)
        if cached:
            # Return a copy with a new workflow ID
            import copy

            state = copy.deepcopy(cached)
            state.workflow_id = str(uuid.uuid4())
            state.context.pop("df", None)  # Don't return the DataFrame
            return state
        return None

    def _save_cache(self, dataset_hash: str, state: WorkflowState) -> None:
        """Save a completed workflow to cache."""
        cache_key = f"workflow:{dataset_hash}"
        # Store without the DataFrame to save memory
        import copy

        to_cache = copy.deepcopy(state)
        to_cache.context.pop("df", None)
        self._cache[cache_key] = to_cache
