"""Natural Language Analytics Engine.

Translates natural language questions into structured analytical operations:
  - Intent detection (compare, rank, trend, explain, summarize, filter)
  - Period-aware query construction
  - Multi-dimensional analysis (group by, filter, aggregate)
  - Result interpretation (not just data, but explanation)

Supports requests such as:
  - "Compare this quarter with last quarter"
  - "Show top-performing regions"
  - "Explain customer churn"
  - "Summarize financial performance"
  - "Highlight unusual spending"
"""

from __future__ import annotations

import json
import logging

import pandas as pd
from sqlalchemy.orm import Session as DbSession

from ai.context_engine import EnterpriseAIContext, EnterpriseContextEngine
from ai.data_gatherer import DataGatherer
from ai.gateway import AIGateway
from ai.prompt_orchestrator import PromptOrchestrator

logger = logging.getLogger(__name__)


class NLAnalyticsEngine:
    """Translates natural language into structured analytical operations."""

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
        """Analyze a natural language question.

        Args:
            question: The user's natural language question.
            df: DataFrame with the dataset.
            semantic_mappings: Semantic entity-to-column mappings.
            industry: Detected industry.
            user_id: User ID.
            context: Pre-built EnterpriseAIContext.

        Returns:
            Dict with intent, query_interpretation, analysis, explanation,
            visualizations, confidence.
        """
        # Build context if not provided
        if context is None:
            context = self.context_engine.build(
                assistant_type="data_copilot",
                user_id=user_id,
                df=df,
                semantic_mappings=semantic_mappings,
                industry=industry,
            )

        # Detect intent
        intent = self._detect_intent(question)

        # Perform the analysis based on intent
        analysis_result = self._perform_analysis(intent, question, df, context)

        # Generate explanation
        explanation = self._generate_explanation(
            intent, question, analysis_result, context, user_id
        )

        # Recommend visualizations
        visualizations = self._recommend_visualizations(intent, analysis_result, context)

        return {
            "intent": intent,
            "query_interpretation": self._interpret_query(question, intent, context),
            "analysis": analysis_result,
            "explanation": explanation,
            "visualizations": visualizations,
            "confidence": self._calculate_confidence(intent, analysis_result),
        }

    def _detect_intent(self, question: str) -> str:
        """Detect the analytical intent from the question."""
        q = question.lower()

        if any(kw in q for kw in ["compare", "versus", "vs", "difference between", "contrast"]):
            return "compare"
        if any(
            kw in q
            for kw in ["top", "best", "highest", "leading", "rank", "bottom", "worst", "lowest"]
        ):
            return "rank"
        if any(
            kw in q for kw in ["trend", "over time", "growth", "decline", "change", "progression"]
        ):
            return "trend"
        if any(kw in q for kw in ["explain", "why", "cause", "reason", "driver"]):
            return "explain"
        if any(kw in q for kw in ["summarize", "summary", "overview", "brief", "snapshot"]):
            return "summarize"
        if any(kw in q for kw in ["filter", "show only", "where", "specific", "particular"]):
            return "filter"
        if any(
            kw in q for kw in ["highlight", "unusual", "anomaly", "outlier", "abnormal", "strange"]
        ):
            return "highlight"
        if any(kw in q for kw in ["breakdown", "by ", "group", "segment", "category"]):
            return "breakdown"

        return "summarize"

    def _perform_analysis(
        self,
        intent: str,
        question: str,
        df: pd.DataFrame | None,
        context: EnterpriseAIContext,
    ) -> dict:
        """Perform the analytical operation based on intent."""
        if df is None or df.empty:
            return {"method": "no_data", "results": "No data available", "data_points": []}

        gatherer = DataGatherer(df, context)

        if intent == "compare":
            return self._analyze_compare(question, df, gatherer)
        elif intent == "rank":
            return self._analyze_rank(question, df, gatherer)
        elif intent == "trend":
            return self._analyze_trend(question, df, gatherer)
        elif intent == "explain":
            return self._analyze_explain(question, df, gatherer)
        elif intent == "summarize":
            return self._analyze_summarize(df, gatherer)
        elif intent == "filter":
            return self._analyze_filter(question, df)
        elif intent == "highlight":
            return self._analyze_highlight(question, df, gatherer)
        elif intent == "breakdown":
            return self._analyze_breakdown(question, df, gatherer)
        else:
            return self._analyze_summarize(df, gatherer)

    def _analyze_compare(self, question: str, df: pd.DataFrame, gatherer: DataGatherer) -> dict:
        """Compare periods or segments."""
        data = gatherer.gather_for_summary()
        period = data.get("period_comparison", {})
        data.get("by_dimension", {})

        results = []
        if period:
            results.append(
                f"Current period ({period.get('current_period', '')}): {period.get('current_value', 0):.2f}"
            )
            results.append(
                f"Previous period ({period.get('previous_period', '')}): {period.get('previous_value', 0):.2f}"
            )
            results.append(
                f"Change: {period.get('absolute_change', 0):+.2f} ({period.get('percentage_change', 0):+.1f}%)"
            )

        return {
            "method": "period_comparison",
            "results": " | ".join(results) if results else "No comparison data available",
            "data_points": results,
            "period_comparison": period,
        }

    def _analyze_rank(self, question: str, df: pd.DataFrame, gatherer: DataGatherer) -> dict:
        """Rank top/bottom performers."""
        data = gatherer.gather_for_summary()
        contributors = data.get("top_contributors", {})

        results = []
        for _key, items in contributors.items():
            top_n = items[:5]
            for i, item in enumerate(top_n, 1):
                dim_name = list(item.keys())[0]
                val_name = list(item.keys())[1]
                results.append(
                    f"#{i}: {item[dim_name]} ({item[val_name]:.2f}, {item.get('share', 0):.1f}%)"
                )

        return {
            "method": "ranking",
            "results": "\n".join(results) if results else "No ranking data available",
            "data_points": results,
            "rankings": contributors,
        }

    def _analyze_trend(self, question: str, df: pd.DataFrame, gatherer: DataGatherer) -> dict:
        """Analyze trends over time."""
        data = gatherer.gather_for_summary()
        trends = data.get("time_trends", {})

        results = []
        for metric, values in trends.items():
            if values:
                first = values[0]["value"]
                last = values[-1]["value"]
                change = last - first
                pct = (change / first * 100) if first != 0 else 0
                direction = "increasing" if change > 0 else "decreasing" if change < 0 else "stable"
                results.append(
                    f"{metric}: {direction} ({pct:+.1f}%) from {first:.2f} to {last:.2f}"
                )

        return {
            "method": "trend_analysis",
            "results": "\n".join(results) if results else "No trend data available",
            "data_points": results,
            "trends": trends,
        }

    def _analyze_explain(self, question: str, df: pd.DataFrame, gatherer: DataGatherer) -> dict:
        """Explain a metric or phenomenon."""
        data = gatherer.gather_for_summary()
        period = data.get("period_comparison", {})
        contributors = data.get("top_contributors", {})

        results = []
        if period:
            direction = "increased" if period.get("percentage_change", 0) > 0 else "decreased"
            results.append(f"Metric {direction} by {abs(period.get('percentage_change', 0)):.1f}%")

        for _key, items in contributors.items():
            if items:
                top = items[0]
                dim_name = list(top.keys())[0]
                val_name = list(top.keys())[1]
                results.append(
                    f"Top contributor: {top[dim_name]} with {top[val_name]:.2f} ({top.get('share', 0):.1f}%)"
                )

        return {
            "method": "explanation",
            "results": "\n".join(results) if results else "Unable to explain with available data",
            "data_points": results,
        }

    def _analyze_summarize(self, df: pd.DataFrame, gatherer: DataGatherer) -> dict:
        """Summarize the dataset."""
        data = gatherer.gather_for_summary()
        overall = data.get("overall", {})

        results = [f"Total records: {overall.get('row_count', len(df))}"]
        for key, val in overall.items():
            if key.startswith("total_") and isinstance(val, (int, float)):
                results.append(f"{key.replace('total_', 'Total ').title()}: {val:,.2f}")

        return {
            "method": "summary",
            "results": "\n".join(results),
            "data_points": results,
            "overall": overall,
        }

    def _analyze_filter(self, question: str, df: pd.DataFrame) -> dict:
        """Filter data based on the question."""
        return {
            "method": "filter",
            "results": "Filtering requires specific criteria. Please specify what to filter by.",
            "data_points": [],
        }

    def _analyze_highlight(self, question: str, df: pd.DataFrame, gatherer: DataGatherer) -> dict:
        """Highlight unusual patterns."""
        data = gatherer.gather_for_summary()
        stats = data.get("numeric_stats", {})

        highlights = []
        for col, col_stats in stats.items():
            mean = col_stats.get("mean", 0)
            std = col_stats.get("std", 0)
            max_val = col_stats.get("max", 0)
            min_val = col_stats.get("min", 0)
            if std > 0 and mean != 0:
                cv = std / abs(mean)
                if cv > 0.5:
                    highlights.append(f"{col}: High variability (CV={cv:.2f})")
                if max_val > mean + 3 * std:
                    highlights.append(f"{col}: Maximum value {max_val:.2f} is >3Ïƒ above mean")
                if min_val < mean - 3 * std:
                    highlights.append(f"{col}: Minimum value {min_val:.2f} is >3Ïƒ below mean")

        return {
            "method": "highlight",
            "results": "\n".join(highlights) if highlights else "No unusual patterns detected",
            "data_points": highlights,
        }

    def _analyze_breakdown(self, question: str, df: pd.DataFrame, gatherer: DataGatherer) -> dict:
        """Break down data by dimensions."""
        data = gatherer.gather_for_summary()
        by_dim = data.get("by_dimension", {})

        results = []
        for key, items in by_dim.items():
            results.append(f"\n{key.replace('_', ' ').title()}:")
            for item in items[:10]:
                parts = [f"{k}={v}" for k, v in item.items()]
                results.append(f"  {', '.join(parts)}")

        return {
            "method": "breakdown",
            "results": "\n".join(results) if results else "No breakdown data available",
            "data_points": results,
            "by_dimension": by_dim,
        }

    def _interpret_query(self, question: str, intent: str, context: EnterpriseAIContext) -> str:
        """Generate a plain-language interpretation of the query."""
        intent_descriptions = {
            "compare": "comparing metrics across periods or segments",
            "rank": "ranking items by performance",
            "trend": "analyzing trends over time",
            "explain": "explaining the causes or drivers of a metric",
            "summarize": "summarizing the overall data",
            "filter": "filtering data by specific criteria",
            "highlight": "highlighting unusual patterns or anomalies",
            "breakdown": "breaking down data by dimensions",
        }
        desc = intent_descriptions.get(intent, "analyzing the data")
        return f"The question is interpreted as {desc}."

    def _generate_explanation(
        self,
        intent: str,
        question: str,
        analysis: dict,
        context: EnterpriseAIContext,
        user_id: int | None = None,
    ) -> str:
        """Generate a plain-language explanation of the results."""
        if not self.gateway:
            return analysis.get("results", "Analysis complete.")

        try:
            result = self.gateway.chat(
                user_message=(
                    f"Question: {question}\n"
                    f"Intent: {intent}\n"
                    f"Analysis results: {json.dumps(analysis, default=str)[:2000]}\n"
                    f"Provide a clear, concise explanation of these results in plain language."
                ),
                assistant_type="data_copilot",
                user_id=user_id,
                context=context.to_dict(),
            )
            return result["response"]
        except Exception:
            return analysis.get("results", "Analysis complete.")

    def _recommend_visualizations(
        self, intent: str, analysis: dict, context: EnterpriseAIContext
    ) -> list[dict]:
        """Recommend appropriate visualizations for the analysis."""
        viz_map = {
            "compare": [
                {
                    "type": "grouped_bar",
                    "rationale": "Side-by-side comparison of periods or segments",
                }
            ],
            "rank": [
                {"type": "horizontal_bar", "rationale": "Ranked display of top/bottom performers"}
            ],
            "trend": [{"type": "line", "rationale": "Time series trend visualization"}],
            "explain": [
                {"type": "waterfall", "rationale": "Shows contribution of each factor to the total"}
            ],
            "summarize": [{"type": "kpi_cards", "rationale": "Key metrics at a glance"}],
            "filter": [{"type": "table", "rationale": "Filtered data in tabular form"}],
            "highlight": [{"type": "scatter", "rationale": "Identify outliers visually"}],
            "breakdown": [
                {"type": "stacked_bar", "rationale": "Show composition across dimensions"}
            ],
        }
        return viz_map.get(intent, [{"type": "table", "rationale": "Default tabular display"}])

    def _calculate_confidence(self, intent: str, analysis: dict) -> float:
        """Calculate confidence score for the analysis."""
        if analysis.get("method") == "no_data":
            return 0.1
        if analysis.get("data_points"):
            return 0.8
        return 0.5
