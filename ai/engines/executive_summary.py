"""Enterprise Executive Summary Engine.

Generates executive-ready summaries containing:
  - Business overview
  - KPI highlights with period-over-period changes
  - Growth and decline drivers
  - Risks with severity and evidence
  - Opportunities
  - Recommended actions with priority and feasibility
  - Confidence level with methodology

Uses the DataGatherer for semantic-aware data gathering and the
PromptOrchestrator for structured prompt pipelines.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

import pandas as pd
from sqlalchemy.orm import Session as DbSession

from ai.context_engine import EnterpriseAIContext, EnterpriseContextEngine
from ai.data_gatherer import DataGatherer
from ai.gateway import AIGateway
from ai.models import AIInsight
from ai.prompt_orchestrator import PromptOrchestrator, PromptTaskType

logger = logging.getLogger(__name__)


class ExecutiveSummaryEngine:
    """Generates executive summaries from any dataset."""

    def __init__(self, db: DbSession | None = None):
        self.db = db
        self.gateway = AIGateway(db) if db else None
        self.context_engine = EnterpriseContextEngine(db)
        self.orchestrator = PromptOrchestrator()

    def generate(
        self,
        user_message: str = "What happened this month?",
        df: pd.DataFrame | None = None,
        semantic_mappings: dict | None = None,
        industry: str = "unknown",
        user_id: int | None = None,
        context: EnterpriseAIContext | None = None,
        additional_data: dict | None = None,
    ) -> dict:
        """Generate an executive summary.

        Args:
            user_message: The user's question (e.g., "What happened this month?").
            df: DataFrame with the dataset.
            semantic_mappings: Semantic entity-to-column mappings.
            industry: Detected industry.
            user_id: User ID for personalization.
            context: Pre-built EnterpriseAIContext (if available).
            additional_data: Pre-computed analysis data.

        Returns:
            Dict with title, executive_summary, kpi_highlights, main_drivers,
            risks, opportunities, forecast, recommended_actions, confidence.
        """
        # Build context if not provided
        if context is None:
            context = self.context_engine.build(
                assistant_type="decision_copilot",
                user_id=user_id,
                df=df,
                semantic_mappings=semantic_mappings,
                industry=industry,
            )

        # Gather data
        gatherer = DataGatherer(df, context)
        analysis_data = additional_data or gatherer.gather_for_summary()

        # Build prompt messages
        messages = self.orchestrator.build_messages(
            task_type=PromptTaskType.EXECUTIVE_SUMMARY,
            user_message=user_message,
            context=context,
            additional_data=analysis_data,
        )

        # Generate via AI gateway
        if self.gateway:
            result = self.gateway.chat(
                user_message=user_message,
                assistant_type="decision_copilot",
                user_id=user_id,
                context=context.to_dict(),
            )
            response_text = result["response"]
        else:
            # Fallback: generate a structured summary from data alone
            response_text = self._generate_from_data(analysis_data, context)

        # Parse the response
        parsed = self._parse_summary(response_text)

        # Enrich with computed data
        parsed = self._enrich_summary(parsed, analysis_data, context)

        # Save to database
        if self.db:
            try:
                insight = AIInsight(
                    insight_type="executive_summary",
                    title=parsed.get("title", "Executive Summary"),
                    summary=parsed.get("executive_summary", ""),
                    details=parsed,
                    key_findings=parsed.get("kpi_highlights", []),
                    recommendations=[r.get("action", str(r)) if isinstance(r, dict) else str(r) for r in parsed.get("recommended_actions", [])],
                    risks=[r.get("risk", str(r)) if isinstance(r, dict) else str(r) for r in parsed.get("risks", [])],
                    opportunities=parsed.get("opportunities", []),
                    confidence_score=parsed.get("confidence", {}).get("score") if isinstance(parsed.get("confidence"), dict) else parsed.get("confidence"),
                    data_sources=analysis_data.get("data_sources", []),
                    user_id=user_id,
                )
                self.db.add(insight)
                self.db.commit()
                self.db.refresh(insight)
                parsed["id"] = insight.id
            except Exception as e:
                logger.warning(f"Failed to save insight: {e}")

        return parsed

    def _parse_summary(self, response: str) -> dict:
        """Parse the AI response into structured summary."""
        try:
            json_match = re.search(r'\{.*"executive_summary".*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except (json.JSONDecodeError, AttributeError):
            pass

        # Fallback: return the raw response as summary
        return {
            "title": "Executive Summary",
            "executive_summary": response[:500],
            "kpi_highlights": [],
            "main_drivers": [],
            "risks": [],
            "opportunities": [],
            "forecast": {},
            "recommended_actions": [],
            "confidence": {"score": 0.5, "methodology": "Unable to parse structured response"},
        }

    def _enrich_summary(self, parsed: dict, data: dict, context: EnterpriseAIContext) -> dict:
        """Enrich the parsed summary with computed data."""
        # Add data sources
        if "data_sources" not in parsed:
            parsed["data_sources"] = data.get("data_sources", [])

        # Add industry context
        if context.industry.industry != "unknown":
            parsed["industry"] = context.industry.display_name or context.industry.industry

        # Add dataset info
        if context.dataset.dataset_id:
            parsed["dataset"] = context.dataset.name or context.dataset.dataset_id

        return parsed

    def _generate_from_data(self, data: dict, context: EnterpriseAIContext) -> str:
        """Generate a basic summary from data alone (no LLM)."""
        overall = data.get("overall", {})
        period_comparison = data.get("period_comparison", {})

        summary_parts = []

        if period_comparison:
            current = period_comparison.get("current_value", 0)
            previous = period_comparison.get("previous_value", 0)
            pct = period_comparison.get("percentage_change", 0)
            direction = "increased" if pct > 0 else "decreased"
            summary_parts.append(
                f"Key metric {direction} by {abs(pct):.1f}% "
                f"({previous:.2f} to {current:.2f})."
            )

        if data.get("top_contributors"):
            for key, items in list(data["top_contributors"].items())[:1]:
                if items:
                    top = items[0]
                    for k, v in top.items():
                        if k != "share":
                            summary_parts.append(f"Top contributor: {k}={v}")
                    if "share" in top:
                        summary_parts.append(f"Share: {top['share']}%")

        summary_text = " ".join(summary_parts) if summary_parts else "Summary generated from available data."

        return json.dumps({
            "title": "Executive Summary",
            "executive_summary": summary_text,
            "kpi_highlights": [],
            "main_drivers": [],
            "risks": [],
            "opportunities": [],
            "forecast": {},
            "recommended_actions": [],
            "confidence": {"score": 0.6, "methodology": "Data-driven summary without LLM"},
        })
