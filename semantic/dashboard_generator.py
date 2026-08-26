"""MODULE 10 â€” Dashboard Generator.

Generates dashboard configurations from semantic entities.
Never generates Retail dashboards for Healthcare data.
Always builds dashboards according to detected business entities.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from semantic.dashboard_registry import DashboardRegistry
from semantic.industry_knowledge import get_industry_knowledge
from semantic.kpi_generator import KPIGenerator
from semantic.mapping_engine import SemanticMappingResult
from semantic.report_registry import ReportRegistry


@dataclass
class DashboardConfig:
    """Configuration for a generated dashboard."""

    title: str
    subtitle: str
    industry: str
    kpi_cards: list[dict] = field(default_factory=list)
    charts: list[dict] = field(default_factory=list)
    filters: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    template: str = ""
    widgets: list[dict] = field(default_factory=list)
    reports: list[str] = field(default_factory=list)
    ai_insights: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "subtitle": self.subtitle,
            "industry": self.industry,
            "kpi_cards": self.kpi_cards,
            "charts": self.charts,
            "filters": self.filters,
            "recommendations": self.recommendations,
            "template": self.template,
            "widgets": self.widgets,
            "reports": self.reports,
            "ai_insights": self.ai_insights,
        }


class DashboardGenerator:
    """Generates dashboard configurations from semantic analysis."""

    CONFIDENCE_THRESHOLD = 85.0

    @staticmethod
    def generate(
        df: pd.DataFrame,
        mapping_result: SemanticMappingResult,
        admin_confirmed: bool = False,
    ) -> DashboardConfig:
        """Generate a dashboard configuration from semantic mappings.

        Args:
            df: The DataFrame.
            mapping_result: Semantic mapping result.
            admin_confirmed: Whether an admin has confirmed low-confidence results.

        Returns:
            DashboardConfig with KPIs, charts, and filters.

        Raises:
            ValueError: If industry confidence is below threshold and not admin-confirmed.
        """
        industry = mapping_result.industry
        confidence = mapping_result.industry_confidence

        if confidence < DashboardGenerator.CONFIDENCE_THRESHOLD and not admin_confirmed:
            raise ValueError(
                f"Industry confidence {confidence:.1f}% is below threshold "
                f"{DashboardGenerator.CONFIDENCE_THRESHOLD}%. "
                f"Admin confirmation required to generate dashboard for industry '{industry}'."
            )

        knowledge = get_industry_knowledge(industry)

        template = DashboardRegistry.get(industry)
        if template is None:
            raise ValueError(
                f"No dashboard template registered for industry '{industry}'. "
                f"Detected entities: {mapping_result.business_entities}. "
                f"Please register a template or override the industry."
            )
        mapped_entities = set(mapping_result.business_entities)
        widgets = [
            widget.to_dict(available=set(widget.required_entities).issubset(mapped_entities))
            for widget in template.widgets
        ]
        kpi_result = KPIGenerator.generate(df, mapping_result)
        kpi_cards = kpi_result.to_cards()
        charts = [
            widget for widget in widgets if widget["type"] != "kpi_card" and widget["available"]
        ]
        filters = DashboardGenerator._generate_filters(df, mapping_result)
        industry_display = (
            knowledge.get("display_name", industry.title()) if knowledge else industry.title()
        )
        subtitle = knowledge.get("description", "") if knowledge else ""

        return DashboardConfig(
            title=template.title or f"{industry_display} Dashboard",
            subtitle=subtitle,
            industry=industry,
            kpi_cards=kpi_cards,
            charts=charts,
            filters=filters,
            recommendations=mapping_result.recommendations,
            template=template.key,
            widgets=widgets,
            reports=ReportRegistry.get(industry),
            ai_insights=list(template.ai_insights),
        )

    @staticmethod
    def _generate_charts(
        df: pd.DataFrame, mapping_result: SemanticMappingResult, industry: str
    ) -> list[dict]:
        """Generate chart specifications based on semantic mappings."""
        col_mapping = mapping_result.semantic_result.get_column_mapping()
        charts = []

        revenue_col = DashboardGenerator._find_col(
            col_mapping, ["revenue", "offering", "tithe", "donation", "billing"]
        )
        date_col = DashboardGenerator._find_col(col_mapping, ["date"])
        category_col = DashboardGenerator._find_col(
            col_mapping, ["course", "diagnosis", "event", "product", "program", "project"]
        )
        region_col = DashboardGenerator._find_col(col_mapping, ["region"])
        dept_col = DashboardGenerator._find_col(
            col_mapping, ["ward", "department", "department_edu", "ministry"]
        )
        entity_col = DashboardGenerator._find_col(
            col_mapping,
            ["patient", "student", "member", "customer", "donor", "beneficiary", "citizen"],
        )

        # 1. Trend over time
        if date_col and date_col in df.columns and revenue_col and revenue_col in df.columns:
            charts.append(
                {
                    "type": "line",
                    "title": f"{'Revenue' if industry == 'retail' else 'Amount'} Over Time",
                    "x": date_col,
                    "y": revenue_col,
                    "aggregation": "sum",
                }
            )

        # 2. By category
        if (
            category_col
            and category_col in df.columns
            and revenue_col
            and revenue_col in df.columns
        ):
            label = DashboardGenerator._category_label(industry)
            charts.append(
                {
                    "type": "bar",
                    "title": f"Amount by {label}",
                    "x": category_col,
                    "y": revenue_col,
                    "aggregation": "sum",
                }
            )

        # 3. By department/region
        group_col = dept_col or region_col
        if group_col and group_col in df.columns and revenue_col and revenue_col in df.columns:
            label = "Department" if dept_col else "Region"
            if industry == "healthcare":
                chart_type = "treemap"
            elif industry == "ngo":
                chart_type = "sunburst"
            elif industry == "government":
                chart_type = "icicle"
            elif industry == "church":
                chart_type = "rose"
            elif industry == "education":
                chart_type = "waterfall"
            else:
                chart_type = "bar"

            charts.append(
                {
                    "type": chart_type,
                    "title": f"Amount by {label}",
                    "x": group_col,
                    "y": revenue_col,
                    "aggregation": "sum",
                }
            )

        # 4. Entity distribution
        if entity_col and entity_col in df.columns:
            charts.append(
                {
                    "type": "pie",
                    "title": f"Distribution by {DashboardGenerator._entity_label(industry)}",
                    "x": entity_col,
                    "aggregation": "count",
                }
            )

        # 5. Scatter: revenue vs quantity (if available)
        qty_col = None
        for col in df.columns:
            if col.lower() in ("quantity", "qty", "units", "count", "volume", "beneficiaries"):
                qty_col = col
                break
        if qty_col and qty_col in df.columns and revenue_col and revenue_col in df.columns:
            charts.append(
                {
                    "type": "scatter",
                    "title": f"Amount vs {qty_col.title()}",
                    "x": revenue_col,
                    "y": qty_col,
                }
            )

        # 6. Heatmap
        if (
            region_col
            and region_col in df.columns
            and category_col
            and category_col in df.columns
            and revenue_col
            and revenue_col in df.columns
        ):
            charts.append(
                {
                    "type": "heatmap",
                    "title": "Heatmap: Region x Category",
                    "x": region_col,
                    "y": category_col,
                    "z": revenue_col,
                    "aggregation": "sum",
                }
            )

        return charts

    @staticmethod
    def _generate_filters(df: pd.DataFrame, mapping_result: SemanticMappingResult) -> list[str]:
        """Generate filter column suggestions."""
        col_mapping = mapping_result.semantic_result.get_column_mapping()
        filters = []
        for entity_key in [
            "region",
            "department",
            "department_edu",
            "ward",
            "course",
            "diagnosis",
            "event",
            "product",
            "program",
            "project",
        ]:
            col = DashboardGenerator._find_col(col_mapping, [entity_key])
            if col and col in df.columns and col not in filters:
                filters.append(col)
        return filters

    @staticmethod
    def _find_col(col_mapping: dict, entity_keys: list[str]) -> str | None:
        for col, entity in col_mapping.items():
            if entity in entity_keys:
                return col
        return None

    @staticmethod
    def _category_label(industry: str) -> str:
        labels = {
            "healthcare": "Diagnosis",
            "education": "Course",
            "church": "Event Type",
            "retail": "Category",
            "government": "Project Type",
            "ngo": "Program",
        }
        return labels.get(industry, "Category")

    @staticmethod
    def _entity_label(industry: str) -> str:
        labels = {
            "healthcare": "Patient",
            "education": "Student",
            "church": "Member",
            "retail": "Customer",
            "government": "Department",
            "ngo": "Donor",
        }
        return labels.get(industry, "Entity")
