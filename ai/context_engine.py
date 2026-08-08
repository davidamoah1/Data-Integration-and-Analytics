"""Enterprise AI Context Engine.

Aggregates all relevant context for AI requests into a single, structured object:
  - Organization & user context (role, permissions, org)
  - Dataset context (schema, profile, quality, semantic mappings)
  - Dashboard state (active filters, KPIs, charts, layout)
  - Industry knowledge (KPIs, business rules, entities)
  - Conversation history with intent tracking
  - KPI definitions from the KPI Intelligence Engine

This replaces the per-assistant context building in ContextBuilder with
a unified, dataset-agnostic approach that works with any loaded data.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field

import pandas as pd
from sqlalchemy import inspect as sqlalchemy_inspect
from sqlalchemy.orm import Session as DbSession

logger = logging.getLogger(__name__)


@dataclass
class UserContext:
    """User-related context for AI requests."""

    user_id: int | None = None
    username: str = ""
    email: str = ""
    role: str = ""
    permissions: list[str] = field(default_factory=list)
    organization_id: str = ""
    organization_name: str = ""
    department: str = ""

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "username": self.username,
            "role": self.role,
            "permissions": self.permissions,
            "organization": self.organization_name,
            "department": self.department,
        }


@dataclass
class DatasetContext:
    """Dataset-related context for AI requests."""

    dataset_id: str = ""
    name: str = ""
    industry: str = "unknown"
    row_count: int = 0
    column_count: int = 0
    columns: list[dict] = field(default_factory=list)  # [{name, type, semantic_role}]
    semantic_mappings: dict = field(default_factory=dict)
    quality_score: float = 100.0
    quality_issues: list[dict] = field(default_factory=list)
    profile_summary: dict = field(default_factory=dict)
    sample_data: list[dict] = field(default_factory=list)  # first 5 rows
    date_range: dict = field(default_factory=dict)  # {start, end, column}
    numeric_columns: list[str] = field(default_factory=list)
    categorical_columns: list[str] = field(default_factory=list)
    date_columns: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "dataset_id": self.dataset_id,
            "name": self.name,
            "industry": self.industry,
            "row_count": self.row_count,
            "column_count": self.column_count,
            "columns": self.columns[:20],  # Limit for token budget
            "semantic_mappings": self.semantic_mappings,
            "quality_score": self.quality_score,
            "quality_issues": self.quality_issues[:5],
            "profile_summary": self.profile_summary,
            "sample_data": self.sample_data,
            "date_range": self.date_range,
            "numeric_columns": self.numeric_columns,
            "categorical_columns": self.categorical_columns,
            "date_columns": self.date_columns,
        }


@dataclass
class DashboardContext:
    """Dashboard state context for AI requests."""

    dashboard_id: str = ""
    title: str = ""
    template: str = ""
    active_filters: dict = field(default_factory=dict)
    kpi_values: dict = field(default_factory=dict)
    kpi_definitions: list[dict] = field(default_factory=list)
    chart_configs: list[dict] = field(default_factory=list)
    drilldown_level: int = 0
    selected_chart: str = ""

    def to_dict(self) -> dict:
        return {
            "dashboard_id": self.dashboard_id,
            "title": self.title,
            "template": self.template,
            "active_filters": self.active_filters,
            "kpi_values": self.kpi_values,
            "kpi_definitions": self.kpi_definitions[:10],
            "chart_configs": self.chart_configs[:5],
            "drilldown_level": self.drilldown_level,
            "selected_chart": self.selected_chart,
        }


@dataclass
class IndustryContext:
    """Industry knowledge context for AI requests."""

    industry: str = "unknown"
    display_name: str = ""
    entities: list[str] = field(default_factory=list)
    kpis: list[dict] = field(default_factory=list)
    business_rules: list[str] = field(default_factory=list)
    ai_prompts: dict = field(default_factory=dict)
    recommended_charts: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "industry": self.industry,
            "display_name": self.display_name,
            "entities": self.entities,
            "kpis": self.kpis[:10] if isinstance(self.kpis, list) else self.kpis,
            "business_rules": self.business_rules,
            "ai_prompts": self.ai_prompts,
            "recommended_charts": self.recommended_charts,
        }


@dataclass
class ConversationContext:
    """Conversation history context for AI requests."""

    conversation_id: int | None = None
    message_count: int = 0
    recent_messages: list[dict] = field(default_factory=list)
    detected_intents: list[str] = field(default_factory=list)
    mentioned_metrics: list[str] = field(default_factory=list)
    mentioned_dimensions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "conversation_id": self.conversation_id,
            "message_count": self.message_count,
            "recent_messages": self.recent_messages[-6:],  # Last 3 exchanges
            "detected_intents": self.detected_intents[-5:],
            "mentioned_metrics": self.mentioned_metrics,
            "mentioned_dimensions": self.mentioned_dimensions,
        }


@dataclass
class EnterpriseAIContext:
    """Unified AI context — the single source of truth for all AI requests."""

    user: UserContext = field(default_factory=UserContext)
    dataset: DatasetContext = field(default_factory=DatasetContext)
    dashboard: DashboardContext = field(default_factory=DashboardContext)
    industry: IndustryContext = field(default_factory=IndustryContext)
    conversation: ConversationContext = field(default_factory=ConversationContext)
    extra_context: dict = field(default_factory=dict)
    assistant_type: str = "data_copilot"
    platform: str = "DataFlow Enterprise Data Intelligence Platform"

    def to_dict(self) -> dict:
        """Serialize to dict for prompt injection."""
        return {
            "platform": self.platform,
            "assistant_type": self.assistant_type,
            "user": self.user.to_dict(),
            "dataset": self.dataset.to_dict(),
            "dashboard": self.dashboard.to_dict(),
            "industry": self.industry.to_dict(),
            "conversation": self.conversation.to_dict(),
            "extra": self.extra_context,
        }

    def to_prompt_context(self, max_chars: int = 4000) -> str:
        """Serialize to a compact string for LLM prompt injection.

        Prioritizes most relevant context within token budget.
        """
        sections: list[str] = []

        # User context (always include)
        if self.user.user_id:
            sections.append(
                f"User: {self.user.username or 'Unknown'} (Role: {self.user.role or 'user'})"
            )

        # Dataset context (high priority)
        if self.dataset.dataset_id or self.dataset.columns:
            ds_parts = [f"Dataset: {self.dataset.name or 'Unknown'}"]
            ds_parts.append(f"Industry: {self.dataset.industry}")
            ds_parts.append(f"Rows: {self.dataset.row_count}, Columns: {self.dataset.column_count}")
            if self.dataset.columns:
                col_strs = [f"{c['name']}({c.get('type', '?')})" for c in self.dataset.columns[:15]]
                ds_parts.append(f"Columns: {', '.join(col_strs)}")
            if self.dataset.semantic_mappings:
                ds_parts.append(
                    f"Semantic: {json.dumps(self.dataset.semantic_mappings, default=str)[:500]}"
                )
            if self.dataset.quality_score < 100:
                ds_parts.append(f"Quality Score: {self.dataset.quality_score}/100")
            if self.dataset.date_range:
                ds_parts.append(f"Date Range: {self.dataset.date_range}")
            if self.dataset.numeric_columns:
                ds_parts.append(f"Numeric: {', '.join(self.dataset.numeric_columns[:10])}")
            if self.dataset.categorical_columns:
                ds_parts.append(f"Categorical: {', '.join(self.dataset.categorical_columns[:10])}")
            sections.append("\n".join(ds_parts))

        # Dashboard context (medium priority)
        if self.dashboard.dashboard_id:
            db_parts = [f"Dashboard: {self.dashboard.title}"]
            if self.dashboard.active_filters:
                db_parts.append(f"Filters: {json.dumps(self.dashboard.active_filters)}")
            if self.dashboard.kpi_values:
                db_parts.append(f"KPIs: {json.dumps(self.dashboard.kpi_values, default=str)[:500]}")
            if self.dashboard.selected_chart:
                db_parts.append(f"Selected Chart: {self.dashboard.selected_chart}")
            sections.append("\n".join(db_parts))

        # Industry context (medium priority)
        if self.industry.industry != "unknown":
            ind_parts = [f"Industry: {self.industry.display_name or self.industry.industry}"]
            if self.industry.kpis:
                kpis = self.industry.kpis
                if isinstance(kpis, dict):
                    kpi_names = []
                    for _category, kpi_list in kpis.items():
                        if isinstance(kpi_list, list):
                            kpi_names.extend(kpi_list[:3])
                        else:
                            kpi_names.append(str(kpi_list))
                    kpi_names = kpi_names[:5]
                elif isinstance(kpis, list):
                    kpi_names = [
                        k.get("name", k.get("label", str(k))) if isinstance(k, dict) else str(k)
                        for k in kpis[:5]
                    ]
                else:
                    kpi_names = [str(kpis)]
                ind_parts.append(f"Key KPIs: {', '.join(str(k) for k in kpi_names)}")
            if self.industry.business_rules:
                ind_parts.append(f"Business Rules: {'; '.join(self.industry.business_rules[:3])}")
            sections.append("\n".join(ind_parts))

        # Conversation context (low priority, but useful for continuity)
        if self.conversation.recent_messages:
            conv_parts = ["Recent Conversation:"]
            for msg in self.conversation.recent_messages[-4:]:
                role = msg.get("role", "user")
                content = msg.get("content", "")[:150]
                conv_parts.append(f"  {role}: {content}")
            sections.append("\n".join(conv_parts))

        # Extra context
        if self.extra_context:
            sections.append(f"Additional: {json.dumps(self.extra_context, default=str)[:500]}")

        result = "\n\n".join(sections)

        # Truncate to budget
        if len(result) > max_chars:
            result = result[:max_chars] + "\n...[context truncated]"

        return result


class EnterpriseContextEngine:
    """Builds unified AI context from all platform sources."""

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

    def __init__(self, db: DbSession | None = None):
        self.db = db

    def build(
        self,
        assistant_type: str = "data_copilot",
        user_id: int | None = None,
        dataset_id: str | None = None,
        dashboard_id: str | None = None,
        df: pd.DataFrame | None = None,
        semantic_mappings: dict | None = None,
        industry: str = "unknown",
        conversation_id: int | None = None,
        active_filters: dict | None = None,
        kpi_values: dict | None = None,
        extra_context: dict | None = None,
        user_permissions: list[str] | None = None,
        user_role: str = "",
    ) -> EnterpriseAIContext:
        """Build a complete AI context from all available sources.

        Args:
            assistant_type: Type of AI assistant.
            user_id: User ID for personalization and RBAC.
            dataset_id: Active dataset ID.
            dashboard_id: Active dashboard ID.
            df: DataFrame for the active dataset (if in-memory).
            semantic_mappings: Semantic entity-to-column mappings.
            industry: Detected industry.
            conversation_id: Active conversation ID.
            active_filters: Currently applied dashboard filters.
            kpi_values: Pre-computed KPI values.
            extra_context: Any additional context.
            user_permissions: User's permissions for RBAC.
            user_role: User's role.

        Returns:
            EnterpriseAIContext with all available context populated.
        """
        ctx = EnterpriseAIContext(assistant_type=assistant_type)

        # Build user context
        ctx.user = self._build_user_context(user_id, user_role, user_permissions or [], self.db)

        # Build dataset context
        ctx.dataset = self._build_dataset_context(
            dataset_id, df, semantic_mappings or {}, industry, self.db
        )

        # Build dashboard context
        ctx.dashboard = self._build_dashboard_context(
            dashboard_id, active_filters or {}, kpi_values or {}, self.db
        )

        # Build industry context
        ctx.industry = self._build_industry_context(industry)

        # Build conversation context
        ctx.conversation = self._build_conversation_context(conversation_id, self.db)

        # Extra context
        ctx.extra_context = extra_context or {}

        return ctx

    def build_from_dict(self, data: dict) -> EnterpriseAIContext:
        """Build context from a dictionary (e.g., from API request)."""
        ctx = EnterpriseAIContext(assistant_type=data.get("assistant_type", "data_copilot"))

        if user_data := data.get("user"):
            ctx.user = UserContext(**user_data)

        if dataset_data := data.get("dataset"):
            ctx.dataset = DatasetContext(**dataset_data)

        if dashboard_data := data.get("dashboard"):
            ctx.dashboard = DashboardContext(**dashboard_data)

        if industry_data := data.get("industry"):
            ctx.industry = IndustryContext(**industry_data)

        if conversation_data := data.get("conversation"):
            ctx.conversation = ConversationContext(**conversation_data)

        ctx.extra_context = data.get("extra", {})

        return ctx

    # ── Context Builders ─────────────────────────────────

    def _build_user_context(
        self,
        user_id: int | None,
        role: str,
        permissions: list[str],
        db: DbSession | None,
    ) -> UserContext:
        """Build user context from DB or provided info."""
        ctx = UserContext(
            user_id=user_id,
            role=role,
            permissions=permissions,
        )

        if db and user_id:
            try:
                from authentication.models import User

                user = db.query(User).filter(User.id == user_id).first()
                if user:
                    ctx.username = user.username or ""
                    ctx.email = user.email or ""
                    ctx.role = role or (user.roles[0].name if user.roles else "user")

                from organizations.models import Organization

                org = db.query(Organization).first()
                if org:
                    ctx.organization_id = str(org.id)
                    ctx.organization_name = org.name or ""
            except Exception:
                pass

        return ctx

    def _build_dataset_context(
        self,
        dataset_id: str | None,
        df: pd.DataFrame | None,
        semantic_mappings: dict,
        industry: str,
        db: DbSession | None,
    ) -> DatasetContext:
        """Build dataset context from DataFrame or DB."""
        ctx = DatasetContext(
            dataset_id=dataset_id or "",
            industry=industry,
            semantic_mappings=semantic_mappings,
        )

        if df is not None:
            ctx.row_count = len(df)
            ctx.column_count = len(df.columns)
            ctx.columns = [
                {
                    "name": col,
                    "type": str(df[col].dtype),
                    "semantic_role": semantic_mappings.get(col, ""),
                }
                for col in df.columns
            ]
            ctx.sample_data = df.head(5).to_dict("records")

            # Classify columns
            for col in df.columns:
                if pd.api.types.is_numeric_dtype(df[col]):
                    ctx.numeric_columns.append(col)
                elif pd.api.types.is_datetime64_any_dtype(df[col]):
                    ctx.date_columns.append(col)
                else:
                    ctx.categorical_columns.append(col)

            # Detect date columns (try parsing)
            for col in df.columns:
                if col not in ctx.date_columns:
                    try:
                        pd.to_datetime(df[col], errors="raise")
                        ctx.date_columns.append(col)
                    except Exception:
                        pass

            # Date range
            for col in ctx.date_columns:
                try:
                    dates = pd.to_datetime(df[col], errors="coerce").dropna()
                    if not dates.empty:
                        ctx.date_range = {
                            "column": col,
                            "start": str(dates.min().date()),
                            "end": str(dates.max().date()),
                        }
                        break
                except Exception:
                    pass

            # Profile summary
            ctx.profile_summary = {
                "numeric_stats": {
                    col: {
                        "mean": (
                            float(df[col].mean())
                            if pd.api.types.is_numeric_dtype(df[col])
                            else None
                        ),
                        "std": (
                            float(df[col].std()) if pd.api.types.is_numeric_dtype(df[col]) else None
                        ),
                        "min": (
                            float(df[col].min()) if pd.api.types.is_numeric_dtype(df[col]) else None
                        ),
                        "max": (
                            float(df[col].max()) if pd.api.types.is_numeric_dtype(df[col]) else None
                        ),
                    }
                    for col in ctx.numeric_columns[:5]
                },
                "categorical_stats": {
                    col: int(df[col].nunique()) for col in ctx.categorical_columns[:5]
                },
            }

        elif db:
            # Try to discover tables and build context from DB
            try:
                tables = self._discover_tables(db)
                if tables:
                    ctx.name = "Database"
                    ctx.columns = [
                        {"name": c["name"], "type": c["type"], "semantic_role": ""}
                        for table_cols in tables.values()
                        for c in table_cols.get("columns", [])
                    ][:20]
                    ctx.column_count = len(ctx.columns)
            except Exception:
                pass

        return ctx

    def _build_dashboard_context(
        self,
        dashboard_id: str | None,
        active_filters: dict,
        kpi_values: dict,
        db: DbSession | None,
    ) -> DashboardContext:
        """Build dashboard context."""
        ctx = DashboardContext(
            dashboard_id=dashboard_id or "",
            active_filters=active_filters,
            kpi_values=kpi_values,
        )

        if dashboard_id:
            try:
                from services.dashboard_engine import DashboardEngine

                engine = DashboardEngine()
                dashboard = engine.get(dashboard_id)
                if dashboard:
                    ctx.title = dashboard.title
                    ctx.template = dashboard.template_key
                    ctx.kpi_definitions = [k.to_dict() for k in dashboard.kpis]
                    ctx.chart_configs = [c.to_dict() for c in dashboard.charts]
            except Exception:
                pass

        return ctx

    def _build_industry_context(self, industry: str) -> IndustryContext:
        """Build industry knowledge context from semantic layer."""
        ctx = IndustryContext(industry=industry)

        try:
            from semantic.industry_knowledge import INDUSTRY_KNOWLEDGE

            knowledge = INDUSTRY_KNOWLEDGE.get(industry, {})
            if knowledge:
                ctx.display_name = knowledge.get("display_name", industry.title())
                ctx.entities = knowledge.get("entities", [])
                ctx.kpis = knowledge.get("kpis", [])
                ctx.business_rules = knowledge.get("business_rules", [])
                ctx.ai_prompts = knowledge.get("ai_prompts", {})
                ctx.recommended_charts = knowledge.get("recommended_charts", [])
        except Exception:
            pass

        return ctx

    def _build_conversation_context(
        self,
        conversation_id: int | None,
        db: DbSession | None,
    ) -> ConversationContext:
        """Build conversation context from memory."""
        ctx = ConversationContext(conversation_id=conversation_id)

        if db and conversation_id:
            try:
                from ai.memory import AIMemory

                memory = AIMemory(db)
                history = memory.get_history(conversation_id)
                ctx.message_count = len(history)
                ctx.recent_messages = history
            except Exception:
                pass

        return ctx

    def _discover_tables(self, db: DbSession) -> dict:
        """Dynamically discover user-facing tables and their columns."""
        result = {}
        try:
            inspector = sqlalchemy_inspect(db.bind)
            for table_name in inspector.get_table_names():
                if any(table_name.startswith(p) for p in self._INTERNAL_TABLE_PREFIXES):
                    continue
                columns = inspector.get_columns(table_name)
                result[table_name] = {
                    "columns": [{"name": c["name"], "type": str(c["type"])} for c in columns]
                }
        except Exception:
            pass
        return result


# ── Global instance ────────────────────────────────────

_context_engine: EnterpriseContextEngine | None = None


def get_context_engine(db: DbSession | None = None) -> EnterpriseContextEngine:
    """Get or create the global context engine instance."""
    global _context_engine
    if _context_engine is None or db is not None:
        _context_engine = EnterpriseContextEngine(db)
    return _context_engine
