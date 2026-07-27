"""Enterprise Prompt Orchestration.

Modular, composable prompt pipelines for specialized AI tasks.

Instead of a single monolithic system prompt, each task type has:
  - A base system prompt (role + guidelines)
  - A task-specific prompt template (structured output requirements)
  - Context injection (from EnterpriseContextEngine)
  - Output schema specification (JSON or structured text)

Prompt Pipelines:
  - Executive Summary
  - KPI Explanation
  - Trend Analysis
  - Root Cause Analysis
  - Forecasting
  - Risk Analysis
  - Data Quality Explanation
  - Dashboard Assistance
  - ETL Assistance
  - NL Analytics
  - Report Generation
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ai.context_engine import EnterpriseAIContext

logger = logging.getLogger(__name__)


class PromptTaskType(str, Enum):
    """Types of AI prompt tasks."""

    EXECUTIVE_SUMMARY = "executive_summary"
    KPI_EXPLANATION = "kpi_explanation"
    TREND_ANALYSIS = "trend_analysis"
    ROOT_CAUSE_ANALYSIS = "root_cause_analysis"
    FORECASTING = "forecasting"
    RISK_ANALYSIS = "risk_analysis"
    DATA_QUALITY = "data_quality"
    DASHBOARD_ASSISTANCE = "dashboard_assistance"
    ETL_ASSISTANCE = "etl_assistance"
    NL_ANALYTICS = "nl_analytics"
    ANOMALY_DETECTION = "anomaly_detection"
    REPORT_GENERATION = "report_generation"
    GENERAL_CHAT = "general_chat"


@dataclass
class PromptPipeline:
    """A structured prompt pipeline for a specific task."""

    task_type: PromptTaskType
    system_prompt: str
    task_prompt: str
    output_schema: dict
    output_format: str = "json"  # "json" or "structured_text"
    max_tokens: int = 4096
    temperature: float = 0.3  # Lower for analytical tasks

    def build_messages(
        self,
        user_message: str,
        context: EnterpriseAIContext,
        additional_data: dict | None = None,
    ) -> list[dict]:
        """Build the complete message list for the LLM.

        Args:
            user_message: The user's question/request.
            context: Enterprise AI context.
            additional_data: Task-specific data (e.g., forecast results, anomaly details).

        Returns:
            List of message dicts for the LLM.
        """
        messages: list[dict] = []

        # 1. System prompt (role + guidelines)
        messages.append({"role": "system", "content": self.system_prompt})

        # 2. Context injection
        context_str = context.to_prompt_context(max_chars=4000)
        if context_str:
            messages.append({
                "role": "system",
                "content": f"Platform Context:\n{context_str}",
            })

        # 3. Task-specific prompt (output requirements)
        task_content = self.task_prompt
        if self.output_format == "json":
            task_content += f"\n\nRespond with JSON matching this schema:\n{json.dumps(self.output_schema, indent=2)}"
        task_content += f"\n\nGuidelines:\n- Base every claim on the provided data\n- Quantify changes with specific numbers and percentages\n- Distinguish between data-backed analysis and assumptions\n- Include a confidence level (0-1) with brief justification\n- If data is insufficient, say so clearly"
        messages.append({"role": "system", "content": task_content})

        # 4. Additional data (e.g., pre-computed results)
        if additional_data:
            messages.append({
                "role": "system",
                "content": f"Analysis Data:\n{json.dumps(additional_data, default=str)[:3000]}",
            })

        # 5. User message
        messages.append({"role": "user", "content": user_message})

        return messages


# ── Prompt Templates ───────────────────────────────────


_BASE_SYSTEM = (
    "You are an Enterprise AI Decision Support System for DataFlow, "
    "an Enterprise Data Intelligence Platform.\n"
    "You act as an experienced business analyst who explains data clearly, "
    "detects issues, forecasts trends, recommends actions, and generates "
    "executive-ready reports.\n\n"
    "Core principles:\n"
    "- Every claim must be backed by data\n"
    "- Quantify all changes with specific numbers and percentages\n"
    "- Distinguish between data-backed analysis and assumptions\n"
    "- Provide confidence levels for all predictions\n"
    "- Prioritize recommendations by impact and feasibility\n"
    "- Respect user permissions — never expose unauthorized data\n"
    "- Be concise but thorough — executives need clarity, not verbosity"
)


_EXECUTIVE_SUMMARY_SCHEMA = {
    "title": "string — Brief title for the summary",
    "executive_summary": "string — 2-3 sentence overview of the most important finding",
    "kpi_highlights": [
        {
            "metric": "string — KPI name",
            "value": "string — Current value",
            "change": "string — Period-over-period change (e.g., '+8.7%')",
            "direction": "up|down|stable",
        }
    ],
    "main_drivers": ["string — Factors contributing to the observed changes"],
    "risks": [
        {
            "risk": "string — Description of the risk",
            "severity": "low|medium|high",
            "evidence": "string — Data supporting this risk",
        }
    ],
    "opportunities": ["string — Actionable opportunities identified"],
    "forecast": {
        "direction": "up|down|stable",
        "expected_range": "string — e.g., '6-9% growth'",
        "horizon": "string — e.g., 'next month'",
        "assumptions": ["string — Key assumptions"],
    },
    "recommended_actions": [
        {
            "action": "string — Specific recommended action",
            "priority": "high|medium|low",
            "expected_impact": "string — Expected outcome",
            "feasibility": "easy|medium|hard",
        }
    ],
    "confidence": {
        "score": 0.0,
        "methodology": "string — Brief explanation of how confidence was determined",
        "data_limitations": ["string — Known limitations"],
    },
}


_KPI_EXPLANATION_SCHEMA = {
    "kpi_name": "string",
    "current_value": "string",
    "formula": "string — How the KPI is calculated",
    "interpretation": "string — What this value means in business terms",
    "drivers": [
        {
            "factor": "string — What contributed to this value",
            "contribution": "string — Quantified contribution (e.g., '42% of growth')",
        }
    ],
    "benchmark": "string — Industry benchmark or target if known",
    "status": "healthy|warning|critical",
    "recommendation": "string — What to do about this KPI",
    "confidence": 0.0,
}


_TREND_ANALYSIS_SCHEMA = {
    "metric": "string — Metric being analyzed",
    "trend_direction": "increasing|decreasing|stable|volatile",
    "rate_of_change": "string — e.g., '+8.7% month-over-month'",
    "period_comparison": {
        "current_period": "string — e.g., 'July 2024'",
        "previous_period": "string — e.g., 'June 2024'",
        "current_value": "string",
        "previous_value": "string",
        "absolute_change": "string",
        "percentage_change": "string",
    },
    "significance": "string — Statistical significance if determinable",
    "contributing_factors": ["string — Factors driving the trend"],
    "projection": "string — Expected continuation of the trend",
    "confidence": 0.0,
}


_ROOT_CAUSE_SCHEMA = {
    "observation": "string — What was observed (the change or issue)",
    "magnitude": "string — Quantified change (e.g., 'Revenue decreased by 11%')",
    "root_causes": [
        {
            "cause": "string — Identified root cause",
            "evidence": "string — Data supporting this cause",
            "contribution": "string — How much this cause contributed",
            "confidence": 0.0,
        }
    ],
    "ruled_out": ["string — Alternative explanations that were ruled out and why"],
    "conclusion": "string — Summary of the root cause analysis",
    "recommended_actions": ["string — Actions to address the root cause"],
    "overall_confidence": 0.0,
}


_FORECAST_SCHEMA = {
    "metric": "string — Metric being forecasted",
    "method": "string — Forecasting method used",
    "horizon": "string — Forecast time horizon",
    "predictions": [
        {
            "period": "string",
            "value": "string",
            "lower_ci": "string — Lower confidence interval",
            "upper_ci": "string — Upper confidence interval",
        }
    ],
    "assumptions": ["string — Key assumptions for the forecast"],
    "model_limitations": ["string — Limitations of the forecasting approach"],
    "interpretation": "string — What the forecast means for the business",
    "confidence": 0.0,
}


_RISK_SCHEMA = {
    "risks": [
        {
            "risk": "string — Description of the risk",
            "category": "financial|operational|compliance|strategic|market",
            "severity": "low|medium|high|critical",
            "probability": "string — Likelihood of occurrence",
            "potential_impact": "string — Quantified impact if it occurs",
            "evidence": "string — Data supporting this risk assessment",
            "mitigation": "string — Recommended mitigation strategy",
        }
    ],
    "overall_risk_level": "low|medium|high|critical",
    "confidence": 0.0,
}


_DATA_QUALITY_SCHEMA = {
    "overall_score": 0.0,
    "quality_grade": "A|B|C|D|F",
    "issues": [
        {
            "issue": "string — Description of the quality issue",
            "column": "string — Affected column",
            "severity": "low|medium|high",
            "affected_rows": "string — Number or percentage of affected rows",
            "root_cause": "string — Likely cause of the issue",
            "fix_recommendation": "string — How to fix it",
            "prevention": "string — How to prevent it in the future",
        }
    ],
    "recommendations": ["string — Prioritized recommendations"],
    "confidence": 0.0,
}


_NL_ANALYTICS_SCHEMA = {
    "intent": "compare|rank|trend|explain|summarize|filter",
    "query_interpretation": "string — How the AI interpreted the user's question",
    "analysis": {
        "method": "string — Analytical approach used",
        "results": "string — Summary of findings",
        "data_points": ["string — Key data points supporting the analysis"],
    },
    "explanation": "string — Plain-language explanation of the results",
    "visualizations": [
        {
            "type": "string — Recommended chart type",
            "config": "string — Chart configuration",
            "rationale": "string — Why this visualization is appropriate",
        }
    ],
    "confidence": 0.0,
}


_REPORT_SCHEMA = {
    "title": "string",
    "report_type": "string",
    "executive_summary": "string — 1-2 paragraph summary",
    "sections": [
        {
            "title": "string",
            "content": "string — Markdown content for this section",
            "charts": ["string — Chart references or descriptions"],
            "tables": ["string — Table data in markdown format"],
        }
    ],
    "methodology": "string — Data sources and analysis methods used",
    "recommendations": ["string — Actionable recommendations"],
    "appendix": "string — Additional data or detailed tables",
    "confidence": 0.0,
}


# ── Task-Specific Prompt Templates ─────────────────────


_TASK_PROMPTS = {
    PromptTaskType.EXECUTIVE_SUMMARY: (
        "Generate an executive summary based on the provided data.\n"
        "The summary should be concise, evidence-based, and suitable for C-level executives.\n\n"
        "Structure:\n"
        "1. Executive Summary — 2-3 sentence overview of the most important finding\n"
        "2. KPI Highlights — Key metrics with period-over-period changes\n"
        "3. Main Drivers — What contributed to the observed changes\n"
        "4. Risks — Identified risks with severity and evidence\n"
        "5. Opportunities — Actionable opportunities\n"
        "6. Forecast — Expected direction and range for next period\n"
        "7. Recommended Actions — Prioritized by impact and feasibility\n"
        "8. Confidence — Score (0-1) with methodology and limitations"
    ),
    PromptTaskType.KPI_EXPLANATION: (
        "Explain the specified KPI in business terms.\n"
        "Include the formula, current value, interpretation, drivers, benchmark, and status.\n"
        "Provide a recommendation for what to do about this KPI value."
    ),
    PromptTaskType.TREND_ANALYSIS: (
        "Analyze the trend for the specified metric.\n"
        "Compare the current period with the previous period.\n"
        "Identify the rate of change, contributing factors, and projected continuation.\n"
        "Assess statistical significance if possible."
    ),
    PromptTaskType.ROOT_CAUSE_ANALYSIS: (
        "Perform a root cause analysis for the observed change or issue.\n\n"
        "Process:\n"
        "1. State the observation and its magnitude\n"
        "2. Identify potential root causes with supporting evidence\n"
        "3. Quantify each cause's contribution\n"
        "4. Rule out alternative explanations\n"
        "5. Conclude with the most likely root cause(s)\n"
        "6. Recommend actions to address the root cause"
    ),
    PromptTaskType.FORECASTING: (
        "Generate a forecast for the specified metric.\n"
        "If pre-computed forecast data is provided, interpret it.\n"
        "Otherwise, based on the available data, project likely future values.\n"
        "Always include assumptions, model limitations, and confidence level."
    ),
    PromptTaskType.RISK_ANALYSIS: (
        "Identify and assess risks based on the provided data.\n"
        "Categorize risks (financial, operational, compliance, strategic, market).\n"
        "For each risk, provide severity, probability, potential impact, evidence, and mitigation.\n"
        "Conclude with an overall risk level."
    ),
    PromptTaskType.DATA_QUALITY: (
        "Analyze data quality and explain any issues found.\n"
        "For each issue, identify the affected column, severity, root cause, and fix recommendation.\n"
        "Provide an overall quality score (0-100) and grade (A-F).\n"
        "Include prevention recommendations for the future."
    ),
    PromptTaskType.DASHBOARD_ASSISTANCE: (
        "Help the user with their dashboard.\n"
        "Interpret their request and determine the appropriate dashboard action.\n"
        "Provide the action type, parameters, and a brief explanation."
    ),
    PromptTaskType.ETL_ASSISTANCE: (
        "Help the user with ETL pipeline configuration.\n"
        "Translate their natural language description into concrete pipeline steps.\n"
        "Each step should be a JSON object with type and configuration.\n"
        "Suggest data quality checks after transformations."
    ),
    PromptTaskType.NL_ANALYTICS: (
        "Translate the user's natural language question into a structured analytical operation.\n"
        "Determine the intent (compare, rank, trend, explain, summarize, filter).\n"
        "Perform the analysis and provide a plain-language explanation.\n"
        "Recommend appropriate visualizations."
    ),
    PromptTaskType.REPORT_GENERATION: (
        "Generate a professional report based on the provided data.\n"
        "Include an executive summary, detailed sections with charts and tables,\n"
        "methodology, recommendations, and appendix.\n"
        "Format content in Markdown."
    ),
    PromptTaskType.GENERAL_CHAT: (
        "Respond to the user's question using the provided platform context.\n"
        "Be helpful, accurate, and data-driven.\n"
        "If the question requires specialized analysis (executive summary, root cause, etc.),\n"
        "suggest the appropriate analysis type."
    ),
}


# ── Output Schemas ─────────────────────────────────────


_OUTPUT_SCHEMAS = {
    PromptTaskType.EXECUTIVE_SUMMARY: _EXECUTIVE_SUMMARY_SCHEMA,
    PromptTaskType.KPI_EXPLANATION: _KPI_EXPLANATION_SCHEMA,
    PromptTaskType.TREND_ANALYSIS: _TREND_ANALYSIS_SCHEMA,
    PromptTaskType.ROOT_CAUSE_ANALYSIS: _ROOT_CAUSE_SCHEMA,
    PromptTaskType.FORECASTING: _FORECAST_SCHEMA,
    PromptTaskType.RISK_ANALYSIS: _RISK_SCHEMA,
    PromptTaskType.DATA_QUALITY: _DATA_QUALITY_SCHEMA,
    PromptTaskType.NL_ANALYTICS: _NL_ANALYTICS_SCHEMA,
    PromptTaskType.REPORT_GENERATION: _REPORT_SCHEMA,
    PromptTaskType.DASHBOARD_ASSISTANCE: {
        "action_type": "string — create_chart|replace_chart|add_filter|resize|export|etc.",
        "parameters": "dict — Action-specific parameters",
        "explanation": "string — Why this action was chosen",
        "confidence": 0.0,
    },
    PromptTaskType.ETL_ASSISTANCE: {
        "pipeline_steps": [
            {"type": "string — extract|transform|load", "config": "dict"}
        ],
        "explanation": "string — Explanation of the pipeline",
        "quality_checks": ["string — Recommended quality checks"],
        "confidence": 0.0,
    },
    PromptTaskType.GENERAL_CHAT: {
        "response": "string — The response to the user's question",
        "suggested_followups": ["string — Suggested follow-up questions"],
        "confidence": 0.0,
    },
}


# ── Pipeline Registry ──────────────────────────────────


class PromptOrchestrator:
    """Manages prompt pipelines for all AI task types."""

    def __init__(self):
        self._pipelines: dict[PromptTaskType, PromptPipeline] = {}
        self._init_pipelines()

    def _init_pipelines(self):
        """Initialize all built-in prompt pipelines."""
        for task_type in PromptTaskType:
            self._pipelines[task_type] = PromptPipeline(
                task_type=task_type,
                system_prompt=_BASE_SYSTEM,
                task_prompt=_TASK_PROMPTS.get(task_type, ""),
                output_schema=_OUTPUT_SCHEMAS.get(task_type, {}),
                output_format="json" if task_type != PromptTaskType.GENERAL_CHAT else "structured_text",
                temperature=0.3 if task_type != PromptTaskType.GENERAL_CHAT else 0.7,
            )

    def get_pipeline(self, task_type: PromptTaskType) -> PromptPipeline:
        """Get the prompt pipeline for a task type."""
        return self._pipelines.get(task_type, self._pipelines[PromptTaskType.GENERAL_CHAT])

    def build_messages(
        self,
        task_type: PromptTaskType,
        user_message: str,
        context: EnterpriseAIContext,
        additional_data: dict | None = None,
    ) -> list[dict]:
        """Build complete message list for a specific task type."""
        pipeline = self.get_pipeline(task_type)
        return pipeline.build_messages(user_message, context, additional_data)

    def detect_task_type(self, user_message: str) -> PromptTaskType:
        """Detect the most appropriate task type from the user's message.

        Uses keyword matching to route to the right pipeline.
        """
        msg_lower = user_message.lower()

        # Executive summary
        if any(kw in msg_lower for kw in ["executive summary", "what happened", "brief", "overview", "summarize performance"]):
            return PromptTaskType.EXECUTIVE_SUMMARY

        # Root cause analysis
        if any(kw in msg_lower for kw in ["why did", "why is", "why are", "what caused", "root cause", "reason for"]):
            return PromptTaskType.ROOT_CAUSE_ANALYSIS

        # Trend analysis
        if any(kw in msg_lower for kw in ["trend", "over time", "month over month", "year over year", "quarter over quarter", "period comparison"]):
            return PromptTaskType.TREND_ANALYSIS

        # Forecasting
        if any(kw in msg_lower for kw in ["forecast", "predict", "future", "next month", "next quarter", "projection", "expect"]):
            return PromptTaskType.FORECASTING

        # Risk analysis
        if any(kw in msg_lower for kw in ["risk", "threat", "danger", "concern", "vulnerability"]):
            return PromptTaskType.RISK_ANALYSIS

        # Data quality
        if any(kw in msg_lower for kw in ["data quality", "missing values", "duplicates", "outliers", "errors in data", "clean data"]):
            return PromptTaskType.DATA_QUALITY

        # KPI explanation
        if any(kw in msg_lower for kw in ["explain kpi", "what is this kpi", "kpi meaning", "metric explanation"]):
            return PromptTaskType.KPI_EXPLANATION

        # NL Analytics
        if any(kw in msg_lower for kw in ["compare", "top performing", "bottom performing", "rank", "highlight", "breakdown by"]):
            return PromptTaskType.NL_ANALYTICS

        # Report generation
        if any(kw in msg_lower for kw in ["generate report", "create report", "monthly report", "annual report", "export report"]):
            return PromptTaskType.REPORT_GENERATION

        # Dashboard assistance
        if any(kw in msg_lower for kw in ["create chart", "add filter", "replace chart", "make dashboard", "resize", "change layout"]):
            return PromptTaskType.DASHBOARD_ASSISTANCE

        # ETL assistance
        if any(kw in msg_lower for kw in ["etl", "pipeline", "extract", "transform", "load", "ingest data"]):
            return PromptTaskType.ETL_ASSISTANCE

        return PromptTaskType.GENERAL_CHAT

    def list_task_types(self) -> list[dict]:
        """List all available task types."""
        return [
            {
                "task_type": t.value,
                "description": _TASK_PROMPTS.get(t, "")[:100],
                "output_format": self.get_pipeline(t).output_format,
            }
            for t in PromptTaskType
        ]


# ── Global instance ────────────────────────────────────

_orchestrator: PromptOrchestrator | None = None


def get_prompt_orchestrator() -> PromptOrchestrator:
    """Get the global prompt orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = PromptOrchestrator()
    return _orchestrator
