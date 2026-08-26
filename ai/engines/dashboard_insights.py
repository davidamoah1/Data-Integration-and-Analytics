"""AI Dashboard Insights Engine â€” generates insights for dashboards.

Every dashboard should include:
- Key Findings
- Risks
- Opportunities
- Recommendations
- Trend Analysis
"""

import json

from sqlalchemy import text
from sqlalchemy.orm import Session as DbSession

from ai.gateway import AIGateway
from ai.models import AIInsight


class DashboardInsightsEngine:
    """Generates AI insights for dashboards."""

    def __init__(self, db: DbSession):
        self.db = db
        self.gateway = AIGateway(db)

    def generate_insights(
        self,
        dashboard_id: str | None = None,
        data_source: dict | None = None,
        context: dict | None = None,
        user_id: int | None = None,
    ) -> dict:
        """Generate insights for a dashboard.

        Returns:
            Dict with key_findings, risks, opportunities, recommendations, trend_analysis.
        """
        # Gather data
        analysis_data = self._gather_data(data_source)

        result = self.gateway.chat(
            user_message=(
                f"Generate dashboard insights based on this data:\n"
                f"{json.dumps(analysis_data, default=str)}\n\n"
                f"Respond with JSON:\n"
                f'{{"key_findings": [{{"finding": "...", "metric": "...", "value": "..."}}], '
                f'"risks": ["..."], "opportunities": ["..."], '
                f'"recommendations": ["..."], '
                f'"trend_analysis": {{"direction": "up|down|stable", "rate_of_change": "...", '
                f'"projection": "..."}}}}'
            ),
            assistant_type="decision_copilot",
            user_id=user_id,
        )

        parsed = self._extract_insights(result["response"])

        # Save to database
        insight = AIInsight(
            insight_type="dashboard",
            title=f"Dashboard Insights - {dashboard_id or 'general'}",
            summary=json.dumps(parsed.get("key_findings", []), default=str)[:500],
            details=parsed,
            key_findings=parsed.get("key_findings", []),
            recommendations=parsed.get("recommendations", []),
            risks=parsed.get("risks", []),
            opportunities=parsed.get("opportunities", []),
            user_id=user_id,
        )
        self.db.add(insight)
        self.db.commit()

        return parsed

    def _gather_data(self, data_source: dict | None) -> dict:
        """Gather data for insight generation."""
        data = {}
        try:
            result = self.db.execute(
                text(
                    "SELECT region, SUM(sales) as sales, SUM(profit) as profit "
                    "FROM sales GROUP BY region ORDER BY sales DESC"
                )
            )
            data["by_region"] = [
                {"region": r[0], "sales": float(r[1]), "profit": float(r[2])}
                for r in result.fetchall()
            ]

            result = self.db.execute(
                text(
                    "SELECT category, SUM(sales) as sales FROM sales GROUP BY category ORDER BY sales DESC"
                )
            )
            data["by_category"] = [
                {"category": r[0], "sales": float(r[1])} for r in result.fetchall()
            ]

            result = self.db.execute(
                text(
                    "SELECT strftime('%Y-%m', order_date) as month, SUM(sales) as sales "
                    "FROM sales WHERE order_date IS NOT NULL "
                    "GROUP BY month ORDER BY month DESC LIMIT 12"
                )
            )
            data["monthly_trend"] = [
                {"month": r[0], "sales": float(r[1])} for r in result.fetchall()
            ]

            result = self.db.execute(
                text(
                    "SELECT COUNT(*) as total, COALESCE(SUM(sales), 0) as sales, "
                    "COALESCE(SUM(profit), 0) as profit FROM sales"
                )
            )
            row = result.fetchone()
            data["summary"] = {
                "total_records": row[0],
                "total_sales": float(row[1]),
                "total_profit": float(row[2]),
            }
        except Exception:
            data["note"] = "Data not available"

        if data_source:
            data["custom_source"] = data_source

        return data

    def _extract_insights(self, response: str) -> dict:
        """Extract insights from AI response."""
        import re

        try:
            json_match = re.search(r'\{.*"key_findings".*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except (json.JSONDecodeError, AttributeError):
            pass
        return {
            "key_findings": [],
            "risks": [],
            "opportunities": [],
            "recommendations": [],
            "trend_analysis": None,
        }
