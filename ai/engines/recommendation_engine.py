"""Enterprise Recommendation Engine.

Generates actionable, industry-specific recommendations with:
  - Data-driven triggers (e.g., low inventory → restock)
  - Expected impact estimation
  - Priority (high/medium/low)
  - Feasibility (easy/medium/hard)
  - Integration with KPI thresholds and industry knowledge

Industry templates:
  - Retail: restock, reduce inventory, expand marketing
  - Healthcare: staffing, readmission monitoring, resource allocation
  - Education: attendance intervention, course optimization
  - Government: budget review, project monitoring
  - Finance: cost reduction, revenue optimization
  - Manufacturing: production planning, quality improvement
  - Logistics: route optimization, capacity management
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


# ── Industry Recommendation Templates ──────────────────


_RETAIL_RECOMMENDATIONS = [
    {"trigger": "high_sales_product", "action": "Restock high-demand items", "expected_impact": "Prevent stockouts, maintain revenue", "priority": "high", "feasibility": "easy"},
    {"trigger": "low_sales_product", "action": "Reduce excess inventory for slow-moving items", "expected_impact": "Free up working capital, reduce storage costs", "priority": "medium", "feasibility": "medium"},
    {"trigger": "high_performing_region", "action": "Expand marketing in high-performing regions", "expected_impact": "10-15% revenue increase in target regions", "priority": "high", "feasibility": "easy"},
    {"trigger": "low_performing_region", "action": "Investigate underperforming regions", "expected_impact": "Identify root causes, potential 5-10% recovery", "priority": "medium", "feasibility": "medium"},
    {"trigger": "declining_profit_margin", "action": "Review pricing strategy and supplier costs", "expected_impact": "2-5% margin improvement", "priority": "high", "feasibility": "medium"},
    {"trigger": "high_discount_usage", "action": "Optimize discount strategy", "expected_impact": "Improve margin while maintaining volume", "priority": "medium", "feasibility": "medium"},
]

_HEALTHCARE_RECOMMENDATIONS = [
    {"trigger": "high_readmission", "action": "Monitor departments with higher readmission rates", "expected_impact": "Reduce readmissions by 15-20%", "priority": "high", "feasibility": "medium"},
    {"trigger": "peak_admission_period", "action": "Increase staffing during peak periods", "expected_impact": "Reduce wait times by 30%", "priority": "high", "feasibility": "medium"},
    {"trigger": "high_billing_amount", "action": "Review high-cost procedures for efficiency", "expected_impact": "10-15% cost reduction", "priority": "medium", "feasibility": "hard"},
    {"trigger": "low_bed_utilization", "action": "Optimize bed allocation and discharge planning", "expected_impact": "Improve utilization by 10-20%", "priority": "medium", "feasibility": "medium"},
    {"trigger": "long_wait_times", "action": "Implement triage optimization and scheduling", "expected_impact": "Reduce average wait time by 25%", "priority": "high", "feasibility": "medium"},
]

_EDUCATION_RECOMMENDATIONS = [
    {"trigger": "declining_attendance", "action": "Investigate courses with declining attendance", "expected_impact": "Identify root causes, improve retention", "priority": "high", "feasibility": "easy"},
    {"trigger": "low_enrollment", "action": "Review curriculum relevance and marketing", "expected_impact": "5-10% enrollment increase", "priority": "medium", "feasibility": "medium"},
    {"trigger": "high_performance_variance", "action": "Provide targeted support for underperforming programs", "expected_impact": "Reduce performance gap by 20%", "priority": "medium", "feasibility": "medium"},
    {"trigger": "resource_underutilization", "action": "Optimize resource allocation across departments", "expected_impact": "10-15% efficiency improvement", "priority": "low", "feasibility": "hard"},
]

_GOVERNMENT_RECOMMENDATIONS = [
    {"trigger": "budget_overrun", "action": "Review projects with budget overruns", "expected_impact": "Prevent further overruns, improve accountability", "priority": "high", "feasibility": "medium"},
    {"trigger": "project_delay", "action": "Accelerate delayed projects with additional resources", "expected_impact": "Reduce delay by 30-50%", "priority": "high", "feasibility": "hard"},
    {"trigger": "underutilized_budget", "action": "Reallocate underutilized budget to high-priority areas", "expected_impact": "Improve service delivery", "priority": "medium", "feasibility": "medium"},
    {"trigger": "high_cost_project", "action": "Conduct cost-benefit analysis for high-cost projects", "expected_impact": "5-10% cost optimization", "priority": "medium", "feasibility": "easy"},
]

_FINANCE_RECOMMENDATIONS = [
    {"trigger": "declining_revenue", "action": "Diversify revenue streams and review pricing", "expected_impact": "5-10% revenue recovery", "priority": "high", "feasibility": "hard"},
    {"trigger": "increasing_costs", "action": "Identify and reduce non-essential expenses", "expected_impact": "3-7% cost reduction", "priority": "high", "feasibility": "medium"},
    {"trigger": "low_profit_margin", "action": "Optimize operational efficiency and pricing", "expected_impact": "2-5% margin improvement", "priority": "high", "feasibility": "medium"},
    {"trigger": "high_transaction_volume", "action": "Automate high-volume processes", "expected_impact": "20-30% processing cost reduction", "priority": "medium", "feasibility": "hard"},
]

_MANUFACTURING_RECOMMENDATIONS = [
    {"trigger": "production_bottleneck", "action": "Identify and address production bottlenecks", "expected_impact": "10-20% throughput increase", "priority": "high", "feasibility": "medium"},
    {"trigger": "high_defect_rate", "action": "Implement quality control improvements", "expected_impact": "Reduce defects by 30-50%", "priority": "high", "feasibility": "medium"},
    {"trigger": "low_capacity_utilization", "action": "Optimize production scheduling", "expected_impact": "10-15% utilization improvement", "priority": "medium", "feasibility": "medium"},
    {"trigger": "high_inventory_cost", "action": "Implement just-in-time inventory management", "expected_impact": "15-25% inventory cost reduction", "priority": "medium", "feasibility": "hard"},
]

_LOGISTICS_RECOMMENDATIONS = [
    {"trigger": "high_transportation_cost", "action": "Optimize routes and consolidate shipments", "expected_impact": "10-20% cost reduction", "priority": "high", "feasibility": "medium"},
    {"trigger": "delivery_delay", "action": "Review and optimize delivery schedules", "expected_impact": "Reduce delays by 25-40%", "priority": "high", "feasibility": "medium"},
    {"trigger": "low_capacity_utilization", "action": "Optimize load planning and capacity allocation", "expected_impact": "10-15% efficiency gain", "priority": "medium", "feasibility": "medium"},
    {"trigger": "high_fuel_cost", "action": "Implement fuel-efficient practices and vehicle maintenance", "expected_impact": "5-10% fuel cost reduction", "priority": "medium", "feasibility": "easy"},
]

_INDUSTRY_TEMPLATES = {
    "retail": _RETAIL_RECOMMENDATIONS,
    "healthcare": _HEALTHCARE_RECOMMENDATIONS,
    "education": _EDUCATION_RECOMMENDATIONS,
    "government": _GOVERNMENT_RECOMMENDATIONS,
    "finance": _FINANCE_RECOMMENDATIONS,
    "manufacturing": _MANUFACTURING_RECOMMENDATIONS,
    "logistics": _LOGISTICS_RECOMMENDATIONS,
}

# Generic recommendations for unknown industries
_GENERIC_RECOMMENDATIONS = [
    {"trigger": "declining_metric", "action": "Investigate the root cause of the decline", "expected_impact": "Identify and address underlying issues", "priority": "high", "feasibility": "easy"},
    {"trigger": "high_variance", "action": "Investigate sources of variability", "expected_impact": "Improve consistency and predictability", "priority": "medium", "feasibility": "medium"},
    {"trigger": "low_performing_segment", "action": "Focus resources on improving underperforming segments", "expected_impact": "10-15% improvement in targeted areas", "priority": "medium", "feasibility": "medium"},
    {"trigger": "high_performing_segment", "action": "Replicate success factors from top performers", "expected_impact": "5-10% overall improvement", "priority": "low", "feasibility": "hard"},
]


class RecommendationEngine:
    """Generates actionable, industry-specific recommendations."""

    def __init__(self, db: DbSession | None = None):
        self.db = db
        self.gateway = AIGateway(db) if db else None
        self.context_engine = EnterpriseContextEngine(db)
        self.orchestrator = PromptOrchestrator()

    def generate(
        self,
        df: pd.DataFrame | None = None,
        semantic_mappings: dict | None = None,
        industry: str = "unknown",
        user_id: int | None = None,
        context: EnterpriseAIContext | None = None,
        analysis_data: dict | None = None,
        user_message: str = "What should I do?",
    ) -> dict:
        """Generate recommendations based on data and industry.

        Args:
            df: DataFrame with the dataset.
            semantic_mappings: Semantic entity-to-column mappings.
            industry: Detected industry.
            user_id: User ID.
            context: Pre-built EnterpriseAIContext.
            analysis_data: Pre-computed analysis data.
            user_message: The user's question.

        Returns:
            Dict with recommendations, industry, triggers_detected, confidence.
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

        # Gather data if not provided
        if analysis_data is None:
            gatherer = DataGatherer(df, context)
            analysis_data = gatherer.gather_for_summary()

        # Detect triggers from data
        triggers = self._detect_triggers(analysis_data, context)

        # Match triggers to recommendation templates
        template_recs = self._match_templates(triggers, industry)

        # Generate AI-enhanced recommendations
        ai_recs = self._generate_ai_recommendations(
            analysis_data, triggers, context, user_message, user_id
        )

        # Merge template and AI recommendations
        all_recs = self._merge_recommendations(template_recs, ai_recs)

        # Save to database
        if self.db and all_recs:
            try:
                insight = AIInsight(
                    insight_type="recommendation",
                    title=f"Recommendations for {context.industry.display_name or industry}",
                    summary=f"Generated {len(all_recs)} recommendations based on data analysis",
                    details={"recommendations": all_recs, "triggers": triggers},
                    key_findings=triggers,
                    recommendations=[r.get("action", str(r)) for r in all_recs],
                    risks=[],
                    opportunities=[r.get("action", str(r)) for r in all_recs if r.get("priority") == "high"],
                    confidence_score=all_recs[0].get("confidence", 0.7) if all_recs else 0.5,
                    data_sources=analysis_data.get("data_sources", []),
                    user_id=user_id,
                )
                self.db.add(insight)
                self.db.commit()
                self.db.refresh(insight)
            except Exception as e:
                logger.warning(f"Failed to save recommendations: {e}")

        return {
            "recommendations": all_recs,
            "industry": industry,
            "triggers_detected": triggers,
            "confidence": all_recs[0].get("confidence", 0.7) if all_recs else 0.5,
        }

    def _detect_triggers(self, data: dict, context: EnterpriseAIContext) -> list[dict]:
        """Detect recommendation triggers from the data."""
        triggers = []

        # Check period comparison for declining/increasing metrics
        period = data.get("period_comparison", {})
        if period:
            pct = period.get("percentage_change", 0)
            if pct < -5:
                triggers.append({
                    "trigger": "declining_metric",
                    "evidence": f"Metric declined by {abs(pct):.1f}%",
                    "data": period,
                })
            elif pct > 10:
                triggers.append({
                    "trigger": "high_performing_segment",
                    "evidence": f"Metric increased by {pct:.1f}%",
                    "data": period,
                })

        # Check top contributors for high/low performers
        for key, items in data.get("top_contributors", {}).items():
            if items:
                top = items[0]
                if top.get("share", 0) > 40:
                    triggers.append({
                        "trigger": "high_sales_product",
                        "evidence": f"Top item has {top['share']}% share",
                        "data": top,
                    })
                bottom = items[-1] if len(items) > 1 else None
                if bottom and bottom.get("share", 100) < 5:
                    triggers.append({
                        "trigger": "low_sales_product",
                        "evidence": f"Bottom item has only {bottom.get('share', 0)}% share",
                        "data": bottom,
                    })

        # Check numeric stats for variance
        for col, stats in data.get("numeric_stats", {}).items():
            if stats.get("std", 0) > 0 and stats.get("mean", 0) != 0:
                cv = stats["std"] / abs(stats["mean"])
                if cv > 0.5:
                    triggers.append({
                        "trigger": "high_variance",
                        "evidence": f"{col} has coefficient of variation {cv:.2f}",
                        "data": {"column": col, "cv": round(cv, 2)},
                    })

        # Check by_dimension for low-performing segments
        for key, items in data.get("by_dimension", {}).items():
            if items and len(items) > 1:
                top_val = items[0].get(list(items[0].keys())[-1], 0)
                bottom_val = items[-1].get(list(items[-1].keys())[-1], 0)
                if top_val > 0 and bottom_val / top_val < 0.3:
                    triggers.append({
                        "trigger": "low_performing_segment",
                        "evidence": f"Bottom segment is {bottom_val/top_val*100:.0f}% of top",
                        "data": {"top": items[0], "bottom": items[-1]},
                    })

        return triggers

    def _match_templates(self, triggers: list[dict], industry: str) -> list[dict]:
        """Match detected triggers to industry recommendation templates."""
        templates = _INDUSTRY_TEMPLATES.get(industry, _GENERIC_RECOMMENDATIONS)
        trigger_types = {t["trigger"] for t in triggers}

        matched = []
        for template in templates:
            if template["trigger"] in trigger_types or template["trigger"] == "declining_metric":
                matched.append({
                    "action": template["action"],
                    "priority": template["priority"],
                    "expected_impact": template["expected_impact"],
                    "feasibility": template["feasibility"],
                    "trigger": template["trigger"],
                    "source": "template",
                    "confidence": 0.8,
                })

        return matched

    def _generate_ai_recommendations(
        self,
        data: dict,
        triggers: list[dict],
        context: EnterpriseAIContext,
        user_message: str,
        user_id: int | None = None,
    ) -> list[dict]:
        """Generate AI-enhanced recommendations."""
        if not self.gateway:
            return []

        try:
            additional = {
                "triggers": triggers,
                "analysis_data": data,
            }

            result = self.gateway.chat(
                user_message=(
                    f"{user_message}\n\n"
                    f"Based on the analysis data and detected triggers, "
                    f"generate 3-5 specific, actionable recommendations.\n"
                    f"Respond with JSON:\n"
                    f'{{"recommendations": [{{"action": "...", "priority": "high|medium|low", '
                    f'"expected_impact": "...", "feasibility": "easy|medium|hard", '
                    f'"trigger": "...", "confidence": 0.0}}]}}'
                ),
                assistant_type="decision_copilot",
                user_id=user_id,
                context=context.to_dict(),
            )

            import re
            json_match = re.search(r'\{.*"recommendations".*\}', result["response"], re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                for rec in parsed.get("recommendations", []):
                    rec["source"] = "ai"
                return parsed.get("recommendations", [])
        except Exception as e:
            logger.warning(f"AI recommendation generation failed: {e}")

        return []

    def _merge_recommendations(
        self, template_recs: list[dict], ai_recs: list[dict]
    ) -> list[dict]:
        """Merge template and AI recommendations, deduplicating by action."""
        seen_actions: set[str] = set()
        merged = []

        # Add template recommendations first (higher confidence)
        for rec in template_recs:
            action_key = rec["action"].lower()[:50]
            if action_key not in seen_actions:
                seen_actions.add(action_key)
                merged.append(rec)

        # Add AI recommendations
        for rec in ai_recs:
            action_key = rec.get("action", "").lower()[:50]
            if action_key and action_key not in seen_actions:
                seen_actions.add(action_key)
                merged.append(rec)

        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        merged.sort(key=lambda r: priority_order.get(r.get("priority", "low"), 3))

        return merged
