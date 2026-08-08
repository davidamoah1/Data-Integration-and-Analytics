"""AI Dashboard Assistant.

Translates natural language requests into dashboard actions.

Supported actions:
  - "Show revenue by region" → Create/update chart
  - "Replace this chart with a heatmap" → Change chart type
  - "Highlight the top five products" → Add filter/ranking
  - "Compare this month with last month" → Add comparison

The assistant uses intent detection and entity extraction to map
natural language to structured dashboard operations.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ActionType(str, Enum):
    CREATE_CHART = "create_chart"
    REPLACE_CHART = "replace_chart"
    ADD_FILTER = "add_filter"
    HIGHLIGHT_TOP = "highlight_top"
    COMPARE_PERIODS = "compare_periods"
    REMOVE_CHART = "remove_chart"
    RESIZE_CHART = "resize_chart"
    ADD_KPI = "add_kpi"
    CHANGE_LAYOUT = "change_layout"
    EXPORT = "export"
    UNKNOWN = "unknown"


@dataclass
class DashboardAction:
    """A parsed dashboard action from natural language."""

    action_type: str
    parameters: dict = field(default_factory=dict)
    confidence: float = 0.0
    explanation: str = ""
    original_query: str = ""

    def to_dict(self) -> dict:
        return {
            "action_type": self.action_type,
            "parameters": self.parameters,
            "confidence": round(self.confidence, 2),
            "explanation": self.explanation,
            "original_query": self.original_query,
        }


class AIDashboardAssistant:
    """Natural language to dashboard action translator."""

    # Intent patterns
    INTENT_PATTERNS: list[dict] = [
        # Create chart
        {
            "type": ActionType.CREATE_CHART.value,
            "patterns": [
                r"show\s+(.+?)\s+by\s+(.+)",
                r"display\s+(.+?)\s+by\s+(.+)",
                r"plot\s+(.+?)\s+by\s+(.+)",
                r"chart\s+(.+?)\s+by\s+(.+)",
                r"visualize\s+(.+?)\s+by\s+(.+)",
                r"show\s+(.+?)\s+over\s+time",
                r"show\s+(.+?)\s+trend",
            ],
            "confidence": 0.85,
        },
        # Replace chart
        {
            "type": ActionType.REPLACE_CHART.value,
            "patterns": [
                r"replace\s+(?:this\s+)?(?:chart|graph|plot)\s+with\s+(?:a\s+)?(\w+)",
                r"change\s+(?:this\s+)?(?:chart|graph)\s+to\s+(?:a\s+)?(\w+)",
                r"swap\s+(?:this\s+)?(?:chart|graph)\s+for\s+(?:a\s+)?(\w+)",
                r"use\s+(?:a\s+)?(\w+)\s+instead",
            ],
            "confidence": 0.8,
        },
        # Highlight top N
        {
            "type": ActionType.HIGHLIGHT_TOP.value,
            "patterns": [
                r"highlight\s+(?:the\s+)?top\s+(\d+)\s+(\w+)",
                r"show\s+(?:the\s+)?top\s+(\d+)\s+(\w+)",
                r"best\s+(\d+)\s+(\w+)",
                r"leading\s+(\d+)\s+(\w+)",
            ],
            "confidence": 0.85,
        },
        # Compare periods
        {
            "type": ActionType.COMPARE_PERIODS.value,
            "patterns": [
                r"compare\s+(?:this\s+)?(\w+)\s+with\s+(?:last\s+)?(\w+)",
                r"compare\s+(\w+)\s+vs\s+(\w+)",
                r"(\w+)\s+versus\s+(\w+)",
                r"month.over.month",
                r"year.over.year",
                r"compare\s+periods",
            ],
            "confidence": 0.75,
        },
        # Add filter
        {
            "type": ActionType.ADD_FILTER.value,
            "patterns": [
                r"filter\s+(?:by\s+)?(.+)",
                r"only\s+show\s+(.+)",
                r"exclude\s+(.+)",
                r"where\s+(.+)",
            ],
            "confidence": 0.7,
        },
        # Remove chart
        {
            "type": ActionType.REMOVE_CHART.value,
            "patterns": [
                r"remove\s+(?:this\s+)?(?:chart|graph|plot)",
                r"delete\s+(?:this\s+)?(?:chart|graph)",
                r"hide\s+(?:this\s+)?(?:chart|graph)",
                r"get\s+rid\s+of\s+(?:this\s+)?(?:chart|graph)",
            ],
            "confidence": 0.8,
        },
        # Resize chart
        {
            "type": ActionType.RESIZE_CHART.value,
            "patterns": [
                r"make\s+(?:this\s+)?(?:chart|graph)\s+(bigger|larger|smaller|wider|narrower)",
                r"resize\s+(?:this\s+)?(?:chart|graph)",
                r"enlarge\s+(?:this\s+)?(?:chart|graph)",
            ],
            "confidence": 0.75,
        },
        # Change layout
        {
            "type": ActionType.CHANGE_LAYOUT.value,
            "patterns": [
                r"use\s+(?:a\s+)?(\w+)\s+layout",
                r"switch\s+(?:to\s+)?(?:a\s+)?(\w+)\s+layout",
                r"change\s+layout\s+to\s+(\w+)",
            ],
            "confidence": 0.7,
        },
        # Export
        {
            "type": ActionType.EXPORT.value,
            "patterns": [
                r"export\s+(?:this\s+)?(?:dashboard|report)\s+(?:as\s+)?(\w+)",
                r"download\s+(?:this\s+)?(?:dashboard|report)\s+(?:as\s+)?(\w+)",
                r"save\s+(?:as\s+)?(\w+)",
            ],
            "confidence": 0.8,
        },
    ]

    # Chart type synonyms
    CHART_TYPE_SYNONYMS: dict[str, str] = {
        "line": "line_chart",
        "line chart": "line_chart",
        "bar": "bar_chart",
        "bar chart": "bar_chart",
        "horizontal bar": "horizontal_bar",
        "pie": "pie_chart",
        "pie chart": "pie_chart",
        "donut": "donut_chart",
        "donut chart": "donut_chart",
        "histogram": "histogram",
        "scatter": "scatter_plot",
        "scatter plot": "scatter_plot",
        "heatmap": "heatmap",
        "heat map": "heatmap",
        "map": "geo_map",
        "geo map": "geo_map",
        "gauge": "gauge",
        "leaderboard": "leaderboard",
        "table": "table",
        "treemap": "treemap",
        "tree map": "treemap",
        "funnel": "funnel",
        "sunburst": "sunburst",
        "waterfall": "waterfall",
        "rose": "rose_chart",
    }

    # Layout synonyms
    LAYOUT_SYNONYMS: dict[str, str] = {
        "standard": "standard",
        "compact": "compact",
        "mobile": "mobile",
        "executive": "executive",
        "default": "standard",
        "simple": "compact",
        "minimal": "executive",
    }

    def parse_query(self, query: str) -> DashboardAction:
        """Parse a natural language query into a dashboard action.

        Args:
            query: Natural language query from the user.

        Returns:
            DashboardAction with action type, parameters, and confidence.
        """
        query_lower = query.lower().strip()

        for intent in self.INTENT_PATTERNS:
            for pattern in intent["patterns"]:
                match = re.search(pattern, query_lower)
                if match:
                    action = self._build_action(
                        intent["type"],
                        match,
                        query,
                        intent["confidence"],
                    )
                    return action

        # No pattern matched
        return DashboardAction(
            action_type=ActionType.UNKNOWN.value,
            confidence=0.0,
            explanation="I couldn't understand that request. Try asking me to show data by category, replace a chart, highlight top items, or compare periods.",
            original_query=query,
        )

    def execute_action(
        self,
        action: DashboardAction,
        dashboard_metadata: dict,
        df_columns: list[str],
    ) -> dict:
        """Execute a parsed action against dashboard metadata.

        Args:
            action: The parsed DashboardAction.
            dashboard_metadata: Current dashboard metadata dict.
            df_columns: Available columns in the dataset.

        Returns:
            Dict with updates to apply to the dashboard.
        """
        result: dict[str, Any] = {
            "action": action.to_dict(),
            "updates": {},
            "success": True,
            "message": "",
        }

        if action.action_type == ActionType.CREATE_CHART.value:
            result["updates"] = self._execute_create_chart(action, df_columns)
            result["message"] = f"Creating chart: {action.parameters.get('title', 'New chart')}"

        elif action.action_type == ActionType.REPLACE_CHART.value:
            result["updates"] = self._execute_replace_chart(action)
            result["message"] = (
                f"Replacing chart with {action.parameters.get('new_type', 'new type')}"
            )

        elif action.action_type == ActionType.HIGHLIGHT_TOP.value:
            result["updates"] = self._execute_highlight_top(action, df_columns)
            result["message"] = (
                f"Highlighting top {action.parameters.get('n', 5)} {action.parameters.get('entity', 'items')}"
            )

        elif action.action_type == ActionType.COMPARE_PERIODS.value:
            result["updates"] = self._execute_compare_periods(action)
            result["message"] = (
                f"Comparing {action.parameters.get('period1', 'current')} vs {action.parameters.get('period2', 'previous')}"
            )

        elif action.action_type == ActionType.ADD_FILTER.value:
            result["updates"] = self._execute_add_filter(action, df_columns)
            result["message"] = f"Adding filter: {action.parameters.get('column', 'unknown')}"

        elif action.action_type == ActionType.REMOVE_CHART.value:
            result["updates"] = {"remove_chart": True}
            result["message"] = "Removing chart"

        elif action.action_type == ActionType.RESIZE_CHART.value:
            result["updates"] = self._execute_resize(action)
            result["message"] = f"Resizing chart: {action.parameters.get('size', 'default')}"

        elif action.action_type == ActionType.CHANGE_LAYOUT.value:
            result["updates"] = {"layout": action.parameters.get("layout", "standard")}
            result["message"] = f"Changing to {action.parameters.get('layout', 'standard')} layout"

        elif action.action_type == ActionType.EXPORT.value:
            result["updates"] = {"export_format": action.parameters.get("format", "pdf")}
            result["message"] = f"Exporting as {action.parameters.get('format', 'PDF')}"

        else:
            result["success"] = False
            result["message"] = action.explanation

        return result

    def get_suggestions(self, dashboard_metadata: dict, df_columns: list[str]) -> list[str]:
        """Get suggested queries based on current dashboard state.

        Args:
            dashboard_metadata: Current dashboard metadata.
            df_columns: Available columns.

        Returns:
            List of suggested natural language queries.
        """
        suggestions: list[str] = []
        numeric_cols = [c for c in df_columns if not c.lower().endswith("_id")]
        categorical_cols = [c for c in df_columns if c not in numeric_cols]

        if len(numeric_cols) >= 2:
            suggestions.append(
                f"Show {numeric_cols[0].replace('_', ' ')} by {categorical_cols[0].replace('_', ' ') if categorical_cols else 'category'}"
            )

        if len(numeric_cols) >= 1:
            suggestions.append(
                f"Highlight the top 5 {categorical_cols[0].replace('_', ' ') if categorical_cols else 'items'}"
            )

        suggestions.append("Compare this month with last month")
        suggestions.append("Replace this chart with a heatmap")
        suggestions.append("Export this dashboard as PDF")

        existing_types = {c.get("chart_type") for c in dashboard_metadata.get("charts", [])}
        if "scatter_plot" not in existing_types and len(numeric_cols) >= 2:
            suggestions.append(
                f"Show {numeric_cols[0].replace('_', ' ')} vs {numeric_cols[1].replace('_', ' ')}"
            )

        return suggestions[:6]

    # ── Private: Action builders ───────────────────────

    def _build_action(
        self, action_type: str, match: re.Match, query: str, confidence: float
    ) -> DashboardAction:
        """Build a DashboardAction from a regex match."""
        groups = match.groups()
        params: dict[str, Any] = {}
        explanation = ""

        if action_type == ActionType.CREATE_CHART.value:
            if len(groups) >= 2:
                metric = groups[0].strip()
                dimension = groups[1].strip()
                params["metric"] = metric
                params["dimension"] = dimension
                params["title"] = f"{metric.title()} by {dimension.title()}"
                params["chart_type"] = (
                    "line_chart" if "time" in dimension or "trend" in dimension else "bar_chart"
                )
                explanation = (
                    f"Create a {params['chart_type']} showing {metric} grouped by {dimension}"
                )
            elif len(groups) == 1:
                metric = groups[0].strip()
                params["metric"] = metric
                params["chart_type"] = "line_chart"
                params["title"] = f"{metric.title()} Over Time"
                explanation = f"Create a line chart showing {metric} over time"

        elif action_type == ActionType.REPLACE_CHART.value:
            if groups:
                chart_name = groups[0].strip()
                resolved = self.CHART_TYPE_SYNONYMS.get(chart_name, chart_name)
                params["new_type"] = resolved
                explanation = f"Replace the current chart with a {chart_name}"

        elif action_type == ActionType.HIGHLIGHT_TOP.value:
            if len(groups) >= 2:
                n = int(groups[0]) if groups[0].isdigit() else 5
                entity = groups[1].strip()
                params["n"] = n
                params["entity"] = entity
                explanation = f"Highlight the top {n} {entity}"

        elif action_type == ActionType.COMPARE_PERIODS.value:
            if len(groups) >= 2:
                params["period1"] = groups[0].strip()
                params["period2"] = groups[1].strip()
                explanation = f"Compare {params['period1']} with {params['period2']}"
            else:
                params["period1"] = "current month"
                params["period2"] = "last month"
                explanation = "Compare current period with previous period"

        elif action_type == ActionType.ADD_FILTER.value:
            if groups:
                params["column"] = groups[0].strip()
                explanation = f"Add a filter on {params['column']}"

        elif action_type == ActionType.RESIZE_CHART.value:
            if groups:
                size_word = groups[0].strip()
                params["size"] = size_word
                if size_word in ("bigger", "larger", "enlarge"):
                    params["width"] = 12
                    params["height"] = 400
                elif size_word == "wider":
                    params["width"] = 12
                elif size_word == "narrower":
                    params["width"] = 4
                else:
                    params["width"] = 4
                    params["height"] = 200
                explanation = f"Make the chart {size_word}"

        elif action_type == ActionType.CHANGE_LAYOUT.value:
            if groups:
                layout_name = groups[0].strip()
                params["layout"] = self.LAYOUT_SYNONYMS.get(layout_name, layout_name)
                explanation = f"Switch to {params['layout']} layout"

        elif action_type == ActionType.EXPORT.value and groups:
            fmt = groups[0].strip()
            params["format"] = fmt
            explanation = f"Export the dashboard as {fmt}"

        return DashboardAction(
            action_type=action_type,
            parameters=params,
            confidence=confidence,
            explanation=explanation,
            original_query=query,
        )

    # ── Private: Action executors ──────────────────────

    def _execute_create_chart(self, action: DashboardAction, df_columns: list[str]) -> dict:
        params = action.parameters
        metric_col = self._find_column(df_columns, params.get("metric", ""))
        dimension_col = self._find_column(df_columns, params.get("dimension", ""))

        return {
            "create_chart": {
                "chart_type": params.get("chart_type", "bar_chart"),
                "title": params.get("title", "New Chart"),
                "x_axis": dimension_col,
                "y_axis": metric_col,
                "aggregation": "sum",
                "section": "primary_charts",
            }
        }

    def _execute_replace_chart(self, action: DashboardAction) -> dict:
        return {
            "replace_chart": {
                "new_type": action.parameters.get("new_type", "bar_chart"),
            }
        }

    def _execute_highlight_top(self, action: DashboardAction, df_columns: list[str]) -> dict:
        return {
            "add_filter": {
                "type": "top_n",
                "n": action.parameters.get("n", 5),
                "entity": action.parameters.get("entity", ""),
                "column": self._find_column(df_columns, action.parameters.get("entity", "")),
            }
        }

    def _execute_compare_periods(self, action: DashboardAction) -> dict:
        return {
            "create_chart": {
                "chart_type": "line_chart",
                "title": f"{action.parameters.get('period1', 'Current')} vs {action.parameters.get('period2', 'Previous')}",
                "comparison": True,
                "period1": action.parameters.get("period1"),
                "period2": action.parameters.get("period2"),
            }
        }

    def _execute_add_filter(self, action: DashboardAction, df_columns: list[str]) -> dict:
        col = self._find_column(df_columns, action.parameters.get("column", ""))
        return {
            "add_filter": {
                "column": col or action.parameters.get("column", ""),
                "filter_type": "single_select",
            }
        }

    def _execute_resize(self, action: DashboardAction) -> dict:
        return {
            "resize_chart": {
                "width": action.parameters.get("width", 6),
                "height": action.parameters.get("height", 300),
            }
        }

    @staticmethod
    def _find_column(df_columns: list[str], hint: str) -> str | None:
        """Find a column matching a hint (case-insensitive, fuzzy)."""
        if not hint:
            return None
        hint_lower = hint.lower().replace(" ", "_")
        for col in df_columns:
            if col.lower() == hint_lower:
                return col
        for col in df_columns:
            if hint_lower in col.lower() or col.lower() in hint_lower:
                return col
        return None
