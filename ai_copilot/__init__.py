"""AI Data Analyst Copilot.

Turns dashboards into an intelligent assistant that can:
  - Answer natural language questions about the data
  - Explain why metrics changed (root cause analysis)
  - Surface automated insights (anomalies, trends, correlations)
  - Generate structured narrative reports

Works locally without an LLM by using statistical analysis on the
DataFrame. Can optionally enhance explanations with LLM calls through
the existing ai/gateway.py infrastructure.

Usage:
    from ai_copilot import DataAnalystCopilot

    copilot = DataAnalystCopilot(df, mapping_result)
    answer = copilot.ask("Why did sales drop?")
    insights = copilot.auto_insights()
    report = copilot.generate_report()
"""

from __future__ import annotations

from ai_copilot.copilot import DataAnalystCopilot
from ai_copilot.insight_generator import AutoInsight, InsightGenerator
from ai_copilot.query_engine import ParsedQuery, QueryEngine, QueryIntent
from ai_copilot.report_generator import Report, ReportGenerator
from ai_copilot.root_cause import Contribution, RootCauseAnalyzer, RootCauseResult

__all__ = [
    "DataAnalystCopilot",
    "QueryEngine",
    "QueryIntent",
    "ParsedQuery",
    "RootCauseAnalyzer",
    "RootCauseResult",
    "Contribution",
    "InsightGenerator",
    "AutoInsight",
    "ReportGenerator",
    "Report",
]
