"""AI Decision Center â€” the flagship decision intelligence engine.

Instead of only showing charts, the AI explains:
1. WHAT HAPPENED â€” observed changes or patterns
2. WHY IT HAPPENED â€” contributing factors and root causes
3. WHAT MAY HAPPEN NEXT â€” forecast likely future scenarios
4. RECOMMENDED ACTIONS â€” specific, prioritized action items
"""

import json

from sqlalchemy import text
from sqlalchemy.orm import Session as DbSession

from ai.gateway import AIGateway
from ai.models import AIInsight


class DecisionCenterEngine:
    """AI-powered decision intelligence engine."""

    def __init__(self, db: DbSession):
        self.db = db
        self.gateway = AIGateway(db)

    def analyze(
        self,
        metric: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        context: dict | None = None,
        user_id: int | None = None,
    ) -> dict:
        """Generate a decision intelligence analysis.

        Returns:
            Dict with id, title, summary, key_findings, recommendations,
            risks, opportunities, confidence_score, data_sources.
        """
        # Gather data for analysis
        analysis_data = self._gather_analysis_data(metric, date_from, date_to)

        # Build prompt
        prompt = self._build_analysis_prompt(metric, analysis_data, context)

        # Generate analysis via AI
        result = self.gateway.chat(
            user_message=prompt,
            assistant_type="decision_copilot",
            user_id=user_id,
        )

        # Parse the AI response
        parsed = self._parse_analysis(result["response"])

        # Save to database
        insight = AIInsight(
            insight_type="decision",
            title=parsed.get("title", "Decision Analysis"),
            summary=parsed.get("summary", ""),
            details=parsed,
            key_findings=parsed.get("key_findings", []),
            recommendations=parsed.get("recommendations", []),
            risks=parsed.get("risks", []),
            opportunities=parsed.get("opportunities", []),
            confidence_score=parsed.get("confidence_score"),
            data_sources=analysis_data.get("data_sources", []),
            user_id=user_id,
        )
        self.db.add(insight)
        self.db.commit()
        self.db.refresh(insight)

        return {
            "id": insight.id,
            "title": insight.title,
            "summary": insight.summary,
            "key_findings": parsed.get("key_findings", []),
            "recommendations": parsed.get("recommendations", []),
            "risks": parsed.get("risks", []),
            "opportunities": parsed.get("opportunities", []),
            "confidence_score": parsed.get("confidence_score"),
            "data_sources": analysis_data.get("data_sources", []),
        }

    def _gather_analysis_data(
        self, metric: str | None, date_from: str | None, date_to: str | None
    ) -> dict:
        """Gather data for the analysis."""
        data = {"data_sources": []}

        try:
            # Overall sales summary
            result = self.db.execute(
                text(
                    "SELECT COUNT(*) as records, COALESCE(SUM(sales), 0) as total_sales, "
                    "COALESCE(SUM(profit), 0) as total_profit, COALESCE(AVG(sales), 0) as avg_order "
                    "FROM sales"
                )
            )
            row = result.fetchone()
            if row:
                data["overall"] = {
                    "records": row[0],
                    "total_sales": float(row[1]),
                    "total_profit": float(row[2]),
                    "avg_order": float(row[3]),
                }
                data["data_sources"].append({"source": "sales", "records": row[0]})

            # Sales by region
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

            # Sales by category
            result = self.db.execute(
                text(
                    "SELECT category, SUM(sales) as sales FROM sales GROUP BY category ORDER BY sales DESC"
                )
            )
            data["by_category"] = [
                {"category": r[0], "sales": float(r[1])} for r in result.fetchall()
            ]

            # Monthly trend
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

            # Top products
            result = self.db.execute(
                text(
                    "SELECT product_name, SUM(sales) as sales FROM sales "
                    "GROUP BY product_name ORDER BY sales DESC LIMIT 10"
                )
            )
            data["top_products"] = [
                {"product": r[0], "sales": float(r[1])} for r in result.fetchall()
            ]

        except Exception:
            data["note"] = "Sales data not available"

        return data

    def _build_analysis_prompt(self, metric: str | None, data: dict, context: dict | None) -> str:
        """Build the analysis prompt."""
        metric_str = f" focusing on {metric}" if metric else ""
        return (
            f"Provide a decision intelligence analysis{metric_str}.\n\n"
            f"Platform data:\n{json.dumps(data, default=str)}\n\n"
            f"Follow this structure:\n"
            f"1. WHAT HAPPENED â€” Describe the observed change or pattern\n"
            f"2. WHY IT HAPPENED â€” Identify contributing factors and root causes\n"
            f"3. WHAT MAY HAPPEN NEXT â€” Forecast likely future scenarios\n"
            f"4. RECOMMENDED ACTIONS â€” Specific, prioritized action items\n\n"
            f"Respond with JSON:\n"
            f'{{"title": "...", "summary": "...", '
            f'"key_findings": [{{"finding": "...", "metric": "...", "change": "..."}}], '
            f'"recommendations": ["..."], "risks": ["..."], "opportunities": ["..."], '
            f'"confidence_score": 0.0}}'
        )

    def _parse_analysis(self, response: str) -> dict:
        """Parse the AI analysis response."""
        import re

        try:
            json_match = re.search(r'\{.*"summary".*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except (json.JSONDecodeError, AttributeError):
            pass
        return {
            "title": "Decision Analysis",
            "summary": response[:500],
            "key_findings": [],
            "recommendations": [],
            "risks": [],
            "opportunities": [],
        }

    def get_insights(self, insight_type: str | None = None, limit: int = 20) -> list[dict]:
        """Get saved insights."""
        query = self.db.query(AIInsight).filter(AIInsight.is_archived.is_(False))
        if insight_type:
            query = query.filter(AIInsight.insight_type == insight_type)
        insights = query.order_by(AIInsight.created_at.desc()).limit(limit).all()
        return [
            {
                "id": i.id,
                "insight_type": i.insight_type,
                "title": i.title,
                "summary": i.summary,
                "key_findings": i.key_findings,
                "recommendations": i.recommendations,
                "risks": i.risks,
                "opportunities": i.opportunities,
                "confidence_score": i.confidence_score,
                "created_at": str(i.created_at) if i.created_at else None,
            }
            for i in insights
        ]
