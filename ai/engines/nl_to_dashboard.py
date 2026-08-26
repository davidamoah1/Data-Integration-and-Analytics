"""Natural Language to Dashboard Engine â€” generates dashboard configs from descriptions.

Translates descriptions like "Create a sales dashboard" into structured
dashboard configurations with appropriate chart types and data mappings.
"""

import json
import re

from sqlalchemy.orm import Session as DbSession

from ai.gateway import AIGateway


class NLToDashboardEngine:
    """Generates dashboard configurations from natural language."""

    def __init__(self, db: DbSession):
        self.db = db
        self.gateway = AIGateway(db)

    def generate_dashboard(
        self, description: str, data_source: str | None = None, user_id: int | None = None
    ) -> dict:
        """Generate a dashboard configuration from a description.

        Returns:
            Dict with dashboard_config, charts, explanation.
        """
        context = {}
        if data_source:
            context["data_source"] = data_source

        result = self.gateway.chat(
            user_message=(
                f"Create a dashboard for: {description}\n\n"
                f"Respond with JSON:\n"
                f'{{"dashboard_config": {{"title": "...", "layout": "grid|tabs", "filters": [...]}}, '
                f'"charts": [{{"type": "bar|line|pie|scatter|heatmap|histogram|area|funnel|gauge", '
                f'"title": "...", "x_axis": "...", "y_axis": "...", "aggregation": "sum|avg|count|min|max", '
                f'"color": "..."}}], '
                f'"explanation": "..."}}\n'
                f"Available chart types: bar, line, pie, scatter, heatmap, histogram, area, funnel, gauge\n"
                f"Available data columns: order_id, order_date, ship_date, customer_name, segment, "
                f"region, category, sub_category, product_name, sales, quantity, discount, profit"
            ),
            assistant_type="dashboard_copilot",
            user_id=user_id,
            context=context,
        )

        config, charts, explanation = self._extract_dashboard(result["response"])

        return {
            "dashboard_config": config,
            "charts": charts,
            "explanation": explanation,
        }

    def _extract_dashboard(self, response: str) -> tuple[dict, list[dict], str]:
        """Extract dashboard config from AI response."""
        try:
            json_match = re.search(r'\{.*"dashboard_config".*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                return (
                    data.get("dashboard_config", {}),
                    data.get("charts", []),
                    data.get("explanation", ""),
                )
        except (json.JSONDecodeError, AttributeError):
            pass

        # Try code block
        code_match = re.search(r"```(?:json)?\s*(.*?)\s*```", response, re.DOTALL)
        if code_match:
            try:
                data = json.loads(code_match.group(1))
                if "dashboard_config" in data:
                    return (
                        data["dashboard_config"],
                        data.get("charts", []),
                        data.get("explanation", ""),
                    )
            except json.JSONDecodeError:
                pass

        return {}, [], response
