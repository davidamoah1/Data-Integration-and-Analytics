"""AI KPI Engine â€” recommends, explains, monitors, and alerts on KPIs."""

import json

from sqlalchemy import text
from sqlalchemy.orm import Session as DbSession

from ai.gateway import AIGateway
from ai.models import AIKPIRecommendation


class KPIEngine:
    """AI-powered KPI recommendation and monitoring engine."""

    def __init__(self, db: DbSession):
        self.db = db
        self.gateway = AIGateway(db)

    def recommend_kpis(
        self,
        domain: str | None = None,
        data_source: dict | None = None,
        user_id: int | None = None,
        organization_id: int | None = None,
    ) -> dict:
        """Recommend KPIs based on domain and available data.

        Returns:
            Dict with recommendations and explanation.
        """
        # Gather available data context
        context = self._gather_data_context()

        domain_str = f" for the {domain} domain" if domain else ""
        result = self.gateway.chat(
            user_message=(
                f"Recommend 5-10 KPIs{domain_str} based on this platform data:\n"
                f"{json.dumps(context, default=str)}\n\n"
                f"Respond with JSON:\n"
                f'{{"recommendations": [{{"name": "...", "description": "...", '
                f'"formula": "...", "unit": "...", "category": "...", '
                f'"target_value": 0.0, "threshold_warning": 0.0, '
                f'"threshold_critical": 0.0, "rationale": "..."}}], '
                f'"explanation": "..."}}'
            ),
            assistant_type="data_copilot",
            user_id=user_id,
        )

        parsed = self._extract_recommendations(result["response"])

        # Save recommendations to database
        for rec in parsed.get("recommendations", []):
            kpi = AIKPIRecommendation(
                kpi_name=rec.get("name", ""),
                description=rec.get("description", ""),
                formula=rec.get("formula", ""),
                unit=rec.get("unit", ""),
                category=rec.get("category", domain or "general"),
                target_value=rec.get("target_value"),
                threshold_warning=rec.get("threshold_warning"),
                threshold_critical=rec.get("threshold_critical"),
                rationale=rec.get("rationale", ""),
                organization_id=organization_id,
                user_id=user_id,
            )
            self.db.add(kpi)
        self.db.commit()

        return {
            "recommendations": parsed.get("recommendations", []),
            "explanation": parsed.get("explanation", ""),
        }

    def monitor_kpis(self) -> dict:
        """Monitor active KPIs and generate alerts for threshold breaches.

        Returns:
            Dict with kpis and alerts.
        """
        kpis = (
            self.db.query(AIKPIRecommendation).filter(AIKPIRecommendation.is_active.is_(True)).all()
        )

        kpi_results = []
        alerts = []

        for kpi in kpis:
            # Try to calculate current value
            current_value = self._calculate_kpi(kpi)

            kpi_result = {
                "id": kpi.id,
                "name": kpi.kpi_name,
                "description": kpi.description,
                "current_value": current_value,
                "target_value": kpi.target_value,
                "unit": kpi.unit,
                "category": kpi.category,
                "status": "unknown",
            }

            if current_value is not None:
                # Check thresholds
                if kpi.threshold_critical is not None:
                    if current_value <= kpi.threshold_critical:
                        kpi_result["status"] = "critical"
                        alerts.append(
                            {
                                "kpi": kpi.kpi_name,
                                "severity": "critical",
                                "message": f"{kpi.kpi_name} is at critical level: {current_value} {kpi.unit or ''}",
                                "current_value": current_value,
                                "threshold": kpi.threshold_critical,
                            }
                        )
                    elif (
                        kpi.threshold_warning is not None and current_value <= kpi.threshold_warning
                    ):
                        kpi_result["status"] = "warning"
                        alerts.append(
                            {
                                "kpi": kpi.kpi_name,
                                "severity": "warning",
                                "message": f"{kpi.kpi_name} is below warning threshold: {current_value} {kpi.unit or ''}",
                                "current_value": current_value,
                                "threshold": kpi.threshold_warning,
                            }
                        )
                    else:
                        kpi_result["status"] = "healthy"
                else:
                    kpi_result["status"] = "active"

            kpi_results.append(kpi_result)

        return {"kpis": kpi_results, "alerts": alerts}

    def _calculate_kpi(self, kpi: AIKPIRecommendation) -> float | None:
        """Attempt to calculate a KPI's current value from platform data."""
        try:
            # Map common KPI names to queries
            name_lower = kpi.kpi_name.lower()

            if "revenue" in name_lower or "total sales" in name_lower:
                result = self.db.execute(text("SELECT COALESCE(SUM(sales), 0) FROM sales"))
                return float(result.fetchone()[0])

            if "profit" in name_lower:
                result = self.db.execute(text("SELECT COALESCE(SUM(profit), 0) FROM sales"))
                return float(result.fetchone()[0])

            if "average order" in name_lower or "aov" in name_lower:
                result = self.db.execute(text("SELECT COALESCE(AVG(sales), 0) FROM sales"))
                return float(result.fetchone()[0])

            if "order count" in name_lower or "total orders" in name_lower:
                result = self.db.execute(text("SELECT COUNT(*) FROM sales"))
                return float(result.fetchone()[0])

            if "margin" in name_lower:
                result = self.db.execute(
                    text(
                        "SELECT CASE WHEN SUM(sales) > 0 THEN SUM(profit)/SUM(sales)*100 ELSE 0 END FROM sales"
                    )
                )
                return float(result.fetchone()[0])

            return None
        except Exception:
            return None

    def _gather_data_context(self) -> dict:
        """Gather platform data context for KPI recommendations."""
        context = {}
        try:
            result = self.db.execute(
                text(
                    "SELECT COUNT(*) as records, COALESCE(SUM(sales), 0) as sales, "
                    "COALESCE(SUM(profit), 0) as profit, COUNT(DISTINCT region) as regions, "
                    "COUNT(DISTINCT category) as categories FROM sales"
                )
            )
            row = result.fetchone()
            if row:
                context["sales_data"] = {
                    "records": row[0],
                    "total_sales": float(row[1]),
                    "total_profit": float(row[2]),
                    "regions": row[3],
                    "categories": row[4],
                }
            context["available_columns"] = [
                "order_id",
                "order_date",
                "ship_date",
                "customer_name",
                "segment",
                "region",
                "category",
                "sub_category",
                "product_name",
                "sales",
                "quantity",
                "discount",
                "profit",
            ]
        except Exception:
            context["note"] = "Sales data not available"
        return context

    def _extract_recommendations(self, response: str) -> dict:
        """Extract KPI recommendations from AI response."""
        import re

        try:
            json_match = re.search(r'\{.*"recommendations".*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except (json.JSONDecodeError, AttributeError):
            pass
        return {"recommendations": [], "explanation": response}
