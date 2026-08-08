"""Root Cause Analysis Engine.

Performs structured root cause analysis:
  1. State the observation and its magnitude
  2. Identify potential root causes with supporting evidence
  3. Quantify each cause's contribution
  4. Rule out alternative explanations
  5. Conclude with the most likely root cause(s)
  6. Recommend actions to address the root cause

Uses contribution analysis, correlation detection, period comparison,
and segment decomposition to support AI-generated explanations.
"""

from __future__ import annotations

import json
import logging
import re

import pandas as pd
from sqlalchemy.orm import Session as DbSession

from ai.context_engine import EnterpriseAIContext, EnterpriseContextEngine
from ai.data_gatherer import DataGatherer
from ai.gateway import AIGateway
from ai.models import AIInsight
from ai.prompt_orchestrator import PromptOrchestrator, PromptTaskType

logger = logging.getLogger(__name__)


class RootCauseAnalysisEngine:
    """Performs structured root cause analysis on any dataset."""

    def __init__(self, db: DbSession | None = None):
        self.db = db
        self.gateway = AIGateway(db) if db else None
        self.context_engine = EnterpriseContextEngine(db)
        self.orchestrator = PromptOrchestrator()

    def analyze(
        self,
        question: str,
        df: pd.DataFrame | None = None,
        semantic_mappings: dict | None = None,
        industry: str = "unknown",
        user_id: int | None = None,
        context: EnterpriseAIContext | None = None,
    ) -> dict:
        """Perform root cause analysis.

        Args:
            question: The user's question (e.g., "Why did revenue decrease?").
            df: DataFrame with the dataset.
            semantic_mappings: Semantic entity-to-column mappings.
            industry: Detected industry.
            user_id: User ID for personalization.
            context: Pre-built EnterpriseAIContext.

        Returns:
            Dict with observation, magnitude, root_causes, ruled_out,
            conclusion, recommended_actions, overall_confidence.
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

        # Detect the metric and direction from the question
        metric, direction = self._detect_metric_and_direction(question, context)

        # Gather data for root cause analysis
        gatherer = DataGatherer(df, context)
        analysis_data = gatherer.gather_for_root_cause(metric, direction)

        # Add the question to the data
        analysis_data["question"] = question

        # Build prompt messages
        self.orchestrator.build_messages(
            task_type=PromptTaskType.ROOT_CAUSE_ANALYSIS,
            user_message=question,
            context=context,
            additional_data=analysis_data,
        )

        # Generate via AI gateway
        if self.gateway:
            result = self.gateway.chat(
                user_message=question,
                assistant_type="decision_copilot",
                user_id=user_id,
                context=context.to_dict(),
            )
            response_text = result["response"]
        else:
            response_text = self._generate_from_data(analysis_data, metric, direction)

        # Parse the response
        parsed = self._parse_analysis(response_text)

        # Enrich with computed data
        parsed = self._enrich_analysis(parsed, analysis_data, context)

        # Save to database
        if self.db:
            try:
                insight = AIInsight(
                    insight_type="root_cause",
                    title=f"Root Cause Analysis: {parsed.get('observation', question[:100])}",
                    summary=parsed.get("conclusion", ""),
                    details=parsed,
                    key_findings=parsed.get("root_causes", []),
                    recommendations=[
                        r if isinstance(r, str) else r.get("action", str(r))
                        for r in parsed.get("recommended_actions", [])
                    ],
                    risks=[],
                    opportunities=[],
                    confidence_score=parsed.get("overall_confidence"),
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

    def _detect_metric_and_direction(
        self, question: str, context: EnterpriseAIContext
    ) -> tuple[str, str]:
        """Detect the metric and direction from the user's question."""
        question_lower = question.lower()

        # Detect direction
        if any(
            kw in question_lower
            for kw in ["decrease", "decline", "drop", "fall", "reduce", "lower", "went down"]
        ):
            direction = "decrease"
        elif any(
            kw in question_lower
            for kw in ["increase", "grow", "rise", "improve", "higher", "went up", "surge"]
        ):
            direction = "increase"
        else:
            direction = "change"

        # Detect metric
        metric = "revenue"  # default
        if context.dataset.numeric_columns:
            # Try to find the metric in the question
            for col in context.dataset.numeric_columns:
                if col.lower() in question_lower:
                    metric = col
                    break
            else:
                # Use first numeric column
                metric = context.dataset.numeric_columns[0]

        # Check common metric names
        metric_keywords = {
            "revenue": ["revenue", "sales", "income"],
            "profit": ["profit", "margin", "earnings"],
            "cost": ["cost", "expense", "spending"],
            "attendance": ["attendance", "visits", "traffic"],
            "billing_amount": ["billing", "charges", "amount"],
        }
        for metric_name, keywords in metric_keywords.items():
            if any(kw in question_lower for kw in keywords):
                metric = metric_name
                break

        return metric, direction

    def _parse_analysis(self, response: str) -> dict:
        """Parse the AI response into structured root cause analysis."""
        try:
            json_match = re.search(r'\{.*"root_causes".*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except (json.JSONDecodeError, AttributeError):
            pass

        return {
            "observation": "Change detected in metric",
            "magnitude": "Unknown",
            "root_causes": [],
            "ruled_out": [],
            "conclusion": response[:500],
            "recommended_actions": [],
            "overall_confidence": 0.5,
        }

    def _enrich_analysis(self, parsed: dict, data: dict, context: EnterpriseAIContext) -> dict:
        """Enrich the parsed analysis with computed data."""
        # Add period comparison if available
        if "period_comparison" not in parsed and data.get("period_comparison"):
            parsed["period_comparison"] = data["period_comparison"]

        # Add contributions if available
        if "contributions" not in parsed and data.get("contributions"):
            parsed["data_contributions"] = data["contributions"][:10]

        # Add correlations if available
        if "correlations" not in parsed and data.get("correlations"):
            parsed["correlations"] = data["correlations"]

        # Add data sources
        if "data_sources" not in parsed:
            parsed["data_sources"] = data.get("data_sources", [])

        return parsed

    def _generate_from_data(self, data: dict, metric: str, direction: str) -> str:
        """Generate a basic root cause analysis from data alone."""
        period = data.get("period_comparison", {})
        contributions = data.get("contributions", [])
        correlations = data.get("correlations", {})

        parts = []

        if period:
            parts.append(
                f"Observation: {metric} {direction}d by {abs(period.get('percentage_change', 0)):.1f}% "
                f"({period.get('previous_value', 0):.2f} to {period.get('current_value', 0):.2f})."
            )

        if contributions:
            top_contributors = contributions[:3]
            for c in top_contributors:
                parts.append(
                    f"Contributor: {c['dimension']}={c['value']} "
                    f"contributed {c['contribution_pct']}% of total."
                )

        if correlations:
            strong_corr = {k: v for k, v in correlations.items() if abs(v) > 0.5}
            if strong_corr:
                for col, corr in strong_corr.items():
                    parts.append(f"Correlation: {metric} correlates with {col} (r={corr}).")

        conclusion = " ".join(parts) if parts else "Insufficient data for root cause analysis."

        return json.dumps(
            {
                "observation": f"{metric} {direction}d",
                "magnitude": (
                    f"{abs(period.get('percentage_change', 0)):.1f}%" if period else "Unknown"
                ),
                "root_causes": [],
                "ruled_out": [],
                "conclusion": conclusion,
                "recommended_actions": [],
                "overall_confidence": 0.6,
            }
        )
