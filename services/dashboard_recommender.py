"""Dashboard Recommendation Engine.

Recommends dashboards based on:
  - Industry
  - Available measures (metrics)
  - Available dimensions
  - Time fields
  - Geographic fields
  - Business entities

Users may accept, customize, or reject recommendations.
"""

from __future__ import annotations

import logging

import pandas as pd

from semantic.dashboard_generator import DashboardGenerator
from semantic.dashboard_registry import DashboardRegistry
from semantic.mapping_engine import SemanticMappingResult

logger = logging.getLogger(__name__)


class DashboardRecommendationEngine:
    """Recommends dashboards based on semantic analysis results."""

    def recommend(
        self,
        df: pd.DataFrame,
        mapping_result: SemanticMappingResult | None,
        admin_confirmed: bool = False,
    ) -> dict:
        """Generate dashboard recommendations.

        Args:
            df: The dataset DataFrame.
            mapping_result: Semantic mapping result from SemanticMappingEngine.
            admin_confirmed: Whether admin confirmed low-confidence industry.

        Returns:
            Dict with recommendations, reasoning, and dashboard config.
        """
        if not mapping_result:
            return self._empty_recommendation()

        industry = mapping_result.industry
        confidence = mapping_result.industry_confidence
        entities = mapping_result.business_entities

        # Identify available measures, dimensions, time, geo
        measures = self._identify_measures(mapping_result)
        dimensions = self._identify_dimensions(mapping_result)
        time_fields = self._identify_time_fields(df, mapping_result)
        geo_fields = self._identify_geo_fields(mapping_result)

        # Get available dashboard templates for this industry
        available_templates = self._get_industry_templates(industry)

        # Generate dashboard config
        dashboard_config = None
        needs_confirmation = False
        confirmation_reason = ""

        try:
            dashboard_config = DashboardGenerator.generate(
                df, mapping_result, admin_confirmed=admin_confirmed
            )
        except ValueError as e:
            needs_confirmation = True
            confirmation_reason = str(e)

        # Build recommendation reasoning
        reasoning = self._build_reasoning(
            industry, confidence, measures, dimensions, time_fields, geo_fields, available_templates
        )

        # Build recommended charts
        recommended_charts = self._recommend_charts(
            measures, dimensions, time_fields, geo_fields, available_templates
        )

        return {
            "recommended": dashboard_config is not None,
            "needs_confirmation": needs_confirmation,
            "confirmation_reason": confirmation_reason,
            "industry": industry,
            "industry_confidence": round(confidence, 2),
            "reasoning": reasoning,
            "available_measures": measures,
            "available_dimensions": dimensions,
            "time_fields": time_fields,
            "geo_fields": geo_fields,
            "available_templates": available_templates,
            "recommended_charts": recommended_charts,
            "dashboard_config": dashboard_config.to_dict() if dashboard_config else None,
            "actions": {
                "accept": "Accept the recommended dashboard as-is",
                "customize": "Customize which charts and KPIs to include",
                "reject": "Reject and build dashboard manually",
            },
        }

    def _identify_measures(self, mapping_result: SemanticMappingResult) -> list[dict]:
        """Identify available measures (metrics) from semantic mappings."""
        measures = []
        if not hasattr(mapping_result, "semantic_result"):
            return measures

        for mapping in mapping_result.semantic_result.mappings:
            if mapping.role == "metric":
                measures.append({
                    "column": mapping.column_name,
                    "entity": mapping.entity_key,
                    "display": mapping.entity_display,
                    "confidence": round(mapping.confidence, 2),
                })
        return measures

    def _identify_dimensions(self, mapping_result: SemanticMappingResult) -> list[dict]:
        """Identify available dimensions from semantic mappings."""
        dimensions = []
        if not hasattr(mapping_result, "semantic_result"):
            return dimensions

        for mapping in mapping_result.semantic_result.mappings:
            if mapping.role in ("dimension", "entity"):
                dimensions.append({
                    "column": mapping.column_name,
                    "entity": mapping.entity_key,
                    "display": mapping.entity_display,
                    "confidence": round(mapping.confidence, 2),
                })
        return dimensions

    def _identify_time_fields(self, df: pd.DataFrame, mapping_result: SemanticMappingResult) -> list[dict]:
        """Identify time/date fields."""
        time_fields = []
        if not hasattr(mapping_result, "semantic_result"):
            return time_fields

        for mapping in mapping_result.semantic_result.mappings:
            if mapping.entity_key == "date":
                time_fields.append({
                    "column": mapping.column_name,
                    "display": mapping.entity_display,
                    "is_datetime": pd.api.types.is_datetime64_any_dtype(df[mapping.column_name])
                    if mapping.column_name in df.columns
                    else False,
                })
        return time_fields

    def _identify_geo_fields(self, mapping_result: SemanticMappingResult) -> list[dict]:
        """Identify geographic fields."""
        geo_fields = []
        geo_entities = {"region", "country", "city", "state", "district", "location", "branch"}
        if not hasattr(mapping_result, "semantic_result"):
            return geo_fields

        for mapping in mapping_result.semantic_result.mappings:
            if mapping.entity_key in geo_entities:
                geo_fields.append({
                    "column": mapping.column_name,
                    "entity": mapping.entity_key,
                    "display": mapping.entity_display,
                })
        return geo_fields

    def _get_industry_templates(self, industry: str) -> list[dict]:
        """Get available dashboard templates for an industry."""
        templates = []
        try:
            template = DashboardRegistry.get(industry)
            if template:
                templates.append({
                    "industry": industry,
                    "name": getattr(template, "name", industry.title()),
                    "kpi_count": len(getattr(template, "kpi_cards", [])),
                    "chart_count": len(getattr(template, "charts", [])),
                })
        except Exception:
            pass

        # Also get generic/unknown template
        try:
            generic = DashboardRegistry.get("unknown")
            if generic and industry != "unknown":
                templates.append({
                    "industry": "unknown",
                    "name": "Generic Analytics",
                    "kpi_count": len(getattr(generic, "kpi_cards", [])),
                    "chart_count": len(getattr(generic, "charts", [])),
                })
        except Exception:
            pass

        return templates

    def _build_reasoning(
        self,
        industry: str,
        confidence: float,
        measures: list[dict],
        dimensions: list[dict],
        time_fields: list[dict],
        geo_fields: list[dict],
        templates: list[dict],
    ) -> str:
        """Build human-readable reasoning for the recommendation."""
        parts = []

        if industry == "unknown":
            parts.append("Industry could not be determined with sufficient confidence.")
            parts.append(f"Best guess confidence: {confidence:.0f}%.")
            parts.append("A generic analytics dashboard is recommended until industry is confirmed.")
        else:
            parts.append(f"Industry detected as '{industry.title()}' with {confidence:.0f}% confidence.")
            if confidence < 70:
                parts.append("Confidence is below threshold — user confirmation is required.")
            elif confidence < 85:
                parts.append("Confidence is moderate — recommendation shown for review.")

        parts.append(f"Found {len(measures)} measure(s) and {len(dimensions)} dimension(s).")
        if time_fields:
            parts.append(f"Time fields available: {', '.join(f['column'] for f in time_fields)}.")
        if geo_fields:
            parts.append(f"Geographic fields available: {', '.join(f['column'] for f in geo_fields)}.")
        if templates:
            parts.append(f"Dashboard template available for '{templates[0]['industry']}'.")

        return " ".join(parts)

    def _recommend_charts(
        self,
        measures: list[dict],
        dimensions: list[dict],
        time_fields: list[dict],
        geo_fields: list[dict],
        templates: list[dict],
    ) -> list[dict]:
        """Recommend specific charts based on available data."""
        charts = []

        # Time series: if we have measures and time fields
        if measures and time_fields:
            for measure in measures[:3]:
                charts.append({
                    "type": "line_chart",
                    "title": f"{measure['display']} over time",
                    "x_axis": time_fields[0]["column"],
                    "y_axis": measure["column"],
                    "reasoning": f"Track {measure['display']} trends over time",
                })

        # Bar chart: measure by dimension
        if measures and dimensions:
            for measure in measures[:2]:
                for dim in dimensions[:2]:
                    charts.append({
                        "type": "bar_chart",
                        "title": f"{measure['display']} by {dim['display']}",
                        "x_axis": dim["column"],
                        "y_axis": measure["column"],
                        "reasoning": f"Compare {measure['display']} across {dim['display']}",
                    })

        # Pie chart: dimension distribution
        if dimensions:
            for dim in dimensions[:2]:
                charts.append({
                    "type": "pie_chart",
                    "title": f"{dim['display']} distribution",
                    "column": dim["column"],
                    "reasoning": f"Show distribution of {dim['display']}",
                })

        # Geo chart: if geo fields and measures
        if geo_fields and measures:
            charts.append({
                "type": "geo_chart",
                "title": f"{measures[0]['display']} by {geo_fields[0]['display']}",
                "geo_column": geo_fields[0]["column"],
                "measure": measures[0]["column"],
                "reasoning": f"Visualize {measures[0]['display']} geographically",
            })

        # KPI cards
        if measures:
            for measure in measures[:4]:
                charts.append({
                    "type": "kpi_card",
                    "title": f"Total {measure['display']}",
                    "measure": measure["column"],
                    "aggregation": "sum",
                    "reasoning": f"Key metric: {measure['display']}",
                })

        return charts[:12]  # Limit to 12 recommendations

    def _empty_recommendation(self) -> dict:
        return {
            "recommended": False,
            "needs_confirmation": True,
            "confirmation_reason": "Semantic analysis not available",
            "industry": "unknown",
            "industry_confidence": 0,
            "reasoning": "No semantic analysis available to generate recommendations.",
            "available_measures": [],
            "available_dimensions": [],
            "time_fields": [],
            "geo_fields": [],
            "available_templates": [],
            "recommended_charts": [],
            "dashboard_config": None,
            "actions": {},
        }
