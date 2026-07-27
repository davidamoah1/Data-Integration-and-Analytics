"""KPI Intelligence Engine.

Automatically detects business KPIs from semantic analysis, metadata,
and industry knowledge. Each KPI includes:
  - Definition, Formula, Confidence
  - Source columns, Aggregation type

The engine combines:
  1. Industry-specific KPI definitions from KPIRegistry
  2. Semantic entity mappings to find source columns
  3. Data-driven detection (numeric columns, unique counts)
  4. Industry knowledge base for formulas and thresholds
"""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd

from semantic.kpi_registry import KPIRegistry
from semantic.industry_knowledge import get_industry_knowledge
from services.dashboard_engine import KPIDefinition

logger = logging.getLogger(__name__)


class KPIIntelligenceEngine:
    """Automatically detects and generates KPIs from data."""

    # Universal KPI templates — applied to any dataset
    UNIVERSAL_KPI_TEMPLATES = [
        {
            "key": "total_records",
            "label": "Total Records",
            "entity": None,
            "metric": "count",
            "category": "operational",
            "formula": "COUNT(*)",
            "aggregation": "count",
            "icon": "📋",
            "description": "Total number of records in the dataset",
        },
        {
            "key": "data_quality",
            "label": "Data Quality Score",
            "entity": None,
            "metric": "quality",
            "category": "quality",
            "formula": "Composite quality score (0-100)",
            "aggregation": "avg",
            "icon": "✅",
            "description": "Overall data quality score based on completeness, validity, uniqueness",
        },
    ]

    # Industry-specific KPI templates with formulas
    INDUSTRY_KPI_TEMPLATES: dict[str, list[dict]] = {
        "healthcare": [
            {"key": "total_admissions", "label": "Total Admissions", "entity": "admission", "metric": "count", "category": "operational", "formula": "COUNT(DISTINCT admission_id)", "icon": "🏥", "description": "Total number of patient admissions"},
            {"key": "total_patients", "label": "Unique Patients", "entity": "patient", "metric": "count", "category": "operational", "formula": "COUNT(DISTINCT patient_id)", "icon": "👥", "description": "Number of unique patients"},
            {"key": "total_billing", "label": "Total Billing", "entity": "billing", "metric": "sum", "category": "financial", "formula": "SUM(billing_amount)", "icon": "💰", "description": "Total billing amount", "unit": "currency"},
            {"key": "avg_billing", "label": "Avg Billing per Patient", "entity": "billing", "metric": "avg", "category": "financial", "formula": "SUM(billing_amount) / COUNT(DISTINCT patient_id)", "icon": "💵", "description": "Average billing amount per patient", "unit": "currency"},
            {"key": "bed_occupancy", "label": "Bed Occupancy Rate", "entity": "ward", "metric": "custom", "category": "operational", "formula": "occupied_beds / total_beds * 100", "icon": "🛏️", "description": "Percentage of beds occupied", "unit": "%", "threshold_warning": 85, "threshold_critical": 95},
            {"key": "readmission_rate", "label": "Readmission Rate", "entity": "admission", "metric": "custom", "category": "clinical", "formula": "readmissions / total_admissions * 100", "icon": "🔄", "description": "Percentage of patients readmitted", "unit": "%", "threshold_warning": 10, "threshold_critical": 15},
        ],
        "education": [
            {"key": "total_enrollment", "label": "Total Enrollment", "entity": "student", "metric": "count", "category": "operational", "formula": "COUNT(DISTINCT student_id)", "icon": "🎓", "description": "Total number of enrolled students"},
            {"key": "attendance_rate", "label": "Attendance Rate", "entity": "attendance", "metric": "custom", "category": "academic", "formula": "present_days / total_days * 100", "icon": "📅", "description": "Average attendance rate", "unit": "%", "threshold_warning": 75},
            {"key": "total_tuition", "label": "Total Tuition", "entity": "revenue", "metric": "sum", "category": "financial", "formula": "SUM(tuition_amount)", "icon": "💰", "description": "Total tuition collected", "unit": "currency"},
            {"key": "pass_rate", "label": "Pass Rate", "entity": "grade", "metric": "custom", "category": "academic", "formula": "passed_exams / total_exams * 100", "icon": "✅", "description": "Percentage of exams passed", "unit": "%"},
        ],
        "retail": [
            {"key": "total_revenue", "label": "Total Revenue", "entity": "revenue", "metric": "sum", "category": "financial", "formula": "SUM(sales)", "icon": "💰", "description": "Total sales revenue", "unit": "currency"},
            {"key": "total_orders", "label": "Total Orders", "entity": "order", "metric": "count", "category": "operational", "formula": "COUNT(DISTINCT order_id)", "icon": "🛒", "description": "Total number of orders"},
            {"key": "total_customers", "label": "Unique Customers", "entity": "customer", "metric": "count", "category": "operational", "formula": "COUNT(DISTINCT customer_id)", "icon": "👥", "description": "Number of unique customers"},
            {"key": "avg_order_value", "label": "Avg Order Value", "entity": "revenue", "metric": "avg", "category": "financial", "formula": "SUM(sales) / COUNT(DISTINCT order_id)", "icon": "📦", "description": "Average value per order", "unit": "currency"},
            {"key": "profit_margin", "label": "Profit Margin", "entity": "revenue", "metric": "custom", "category": "financial", "formula": "SUM(profit) / SUM(sales) * 100", "icon": "📈", "description": "Profit margin percentage", "unit": "%"},
        ],
        "banking": [
            {"key": "total_balance", "label": "Total Balance", "entity": "account", "metric": "sum", "category": "financial", "formula": "SUM(balance)", "icon": "💰", "description": "Total account balance", "unit": "currency"},
            {"key": "total_accounts", "label": "Total Accounts", "entity": "account", "metric": "count", "category": "operational", "formula": "COUNT(DISTINCT account_id)", "icon": "🏦", "description": "Number of accounts"},
            {"key": "total_transactions", "label": "Total Transactions", "entity": "transaction", "metric": "count", "category": "operational", "formula": "COUNT(*)", "icon": "🔄", "description": "Total transactions"},
            {"key": "total_loans", "label": "Total Loans", "entity": "loan", "metric": "count", "category": "financial", "formula": "COUNT(DISTINCT loan_id)", "icon": "📋", "description": "Number of loans"},
        ],
        "government": [
            {"key": "total_budget", "label": "Total Budget", "entity": "budget_gov", "metric": "sum", "category": "financial", "formula": "SUM(budget_amount)", "icon": "💰", "description": "Total budget allocation", "unit": "currency"},
            {"key": "total_projects", "label": "Total Projects", "entity": "project_gov", "metric": "count", "category": "operational", "formula": "COUNT(DISTINCT project_id)", "icon": "🏗️", "description": "Number of projects"},
            {"key": "budget_utilization", "label": "Budget Utilization", "entity": "budget_gov", "metric": "custom", "category": "financial", "formula": "spent / budget * 100", "icon": "📊", "description": "Budget utilization percentage", "unit": "%"},
        ],
        "manufacturing": [
            {"key": "total_production", "label": "Total Production", "entity": "production", "metric": "sum", "category": "operational", "formula": "SUM(production_volume)", "icon": "🏭", "description": "Total production volume"},
            {"key": "active_machines", "label": "Active Machines", "entity": "machine", "metric": "count", "category": "operational", "formula": "COUNT(DISTINCT machine_id)", "icon": "⚙️", "description": "Number of active machines"},
            {"key": "downtime_hours", "label": "Downtime Hours", "entity": "downtime", "metric": "sum", "category": "operational", "formula": "SUM(downtime_hours)", "icon": "⏰", "description": "Total downtime hours"},
        ],
        "agriculture": [
            {"key": "total_harvest", "label": "Total Harvest", "entity": "crop", "metric": "sum", "category": "operational", "formula": "SUM(harvest_amount)", "icon": "🌾", "description": "Total harvest amount"},
            {"key": "total_farms", "label": "Total Farms", "entity": "farm", "metric": "count", "category": "operational", "formula": "COUNT(DISTINCT farm_id)", "icon": "🚜", "description": "Number of farms"},
            {"key": "avg_yield", "label": "Avg Yield per Hectare", "entity": "crop", "metric": "avg", "category": "operational", "formula": "SUM(yield) / SUM(hectares)", "icon": "📈", "description": "Average yield per hectare"},
        ],
        "church": [
            {"key": "total_members", "label": "Total Members", "entity": "member", "metric": "count", "category": "operational", "formula": "COUNT(DISTINCT member_id)", "icon": "👥", "description": "Number of members"},
            {"key": "total_tithe", "label": "Total Tithe", "entity": "tithe", "metric": "sum", "category": "financial", "formula": "SUM(tithe_amount)", "icon": "💰", "description": "Total tithe collected", "unit": "currency"},
            {"key": "total_offering", "label": "Total Offering", "entity": "offering", "metric": "sum", "category": "financial", "formula": "SUM(offering_amount)", "icon": "🎁", "description": "Total offerings", "unit": "currency"},
        ],
        "ngo": [
            {"key": "total_donations", "label": "Total Donations", "entity": "donation", "metric": "sum", "category": "financial", "formula": "SUM(donation_amount)", "icon": "💰", "description": "Total donations received", "unit": "currency"},
            {"key": "total_beneficiaries", "label": "Beneficiaries", "entity": "beneficiary", "metric": "count", "category": "impact", "formula": "COUNT(DISTINCT beneficiary_id)", "icon": "🤝", "description": "Number of beneficiaries"},
            {"key": "total_donors", "label": "Total Donors", "entity": "donor", "metric": "count", "category": "financial", "formula": "COUNT(DISTINCT donor_id)", "icon": "❤️", "description": "Number of unique donors"},
        ],
        "insurance": [
            {"key": "total_premium", "label": "Total Premium", "entity": "policy", "metric": "sum", "category": "financial", "formula": "SUM(premium_amount)", "icon": "💰", "description": "Total premium income", "unit": "currency"},
            {"key": "total_policies", "label": "Total Policies", "entity": "policy", "metric": "count", "category": "operational", "formula": "COUNT(DISTINCT policy_id)", "icon": "📄", "description": "Number of active policies"},
            {"key": "total_claims", "label": "Total Claims", "entity": "claim", "metric": "count", "category": "operational", "formula": "COUNT(DISTINCT claim_id)", "icon": "📋", "description": "Number of claims"},
        ],
        "hospitality": [
            {"key": "total_reservations", "label": "Reservations", "entity": "reservation", "metric": "count", "category": "operational", "formula": "COUNT(DISTINCT reservation_id)", "icon": "🏨", "description": "Number of reservations"},
            {"key": "total_guests", "label": "Total Guests", "entity": "guest", "metric": "count", "category": "operational", "formula": "COUNT(DISTINCT guest_id)", "icon": "👥", "description": "Number of unique guests"},
            {"key": "total_revenue", "label": "Total Revenue", "entity": "reservation", "metric": "sum", "category": "financial", "formula": "SUM(revenue)", "icon": "💰", "description": "Total revenue", "unit": "currency"},
        ],
        "telecommunications": [
            {"key": "total_subscribers", "label": "Subscribers", "entity": "subscriber", "metric": "count", "category": "operational", "formula": "COUNT(DISTINCT subscriber_id)", "icon": "📱", "description": "Number of subscribers"},
            {"key": "total_calls", "label": "Total Calls", "entity": "call", "metric": "count", "category": "operational", "formula": "COUNT(*)", "icon": "📞", "description": "Total number of calls"},
            {"key": "total_data_usage", "label": "Data Usage", "entity": "data_usage", "metric": "sum", "category": "operational", "formula": "SUM(data_bytes)", "icon": "📶", "description": "Total data usage"},
        ],
    }

    def detect_kpis(
        self,
        df: pd.DataFrame,
        industry: str,
        semantic_mappings: dict | None = None,
        quality_score: float = 100.0,
    ) -> list[KPIDefinition]:
        """Detect KPIs for a dataset.

        Args:
            df: The dataset DataFrame.
            industry: Detected industry.
            semantic_mappings: Column-to-entity mapping from SemanticEngine.
            quality_score: Data quality score (0-100).

        Returns:
            List of KPIDefinition objects with formulas and confidence.
        """
        kpis: list[KPIDefinition] = []
        col_mapping = semantic_mappings or {}

        # 1. Add universal KPIs
        kpis.extend(self._universal_kpis(df, quality_score))

        # 2. Add industry-specific KPIs
        industry_kpis = self._industry_kpis(df, industry, col_mapping)
        kpis.extend(industry_kpis)

        # 3. Add data-driven KPIs (numeric columns not yet covered)
        kpis.extend(self._data_driven_kpis(df, col_mapping, kpis))

        # 4. Add registry KPIs (from KPIRegistry)
        kpis.extend(self._registry_kpis(df, industry, col_mapping))

        # Deduplicate by key
        seen_keys: set[str] = set()
        unique_kpis: list[KPIDefinition] = []
        for kpi in kpis:
            if kpi.key not in seen_keys:
                seen_keys.add(kpi.key)
                unique_kpis.append(kpi)

        return unique_kpis

    def _universal_kpis(self, df: pd.DataFrame, quality_score: float) -> list[KPIDefinition]:
        """Generate universal KPIs."""
        kpis = []
        for template in self.UNIVERSAL_KPI_TEMPLATES:
            if template["key"] == "total_records":
                kpis.append(KPIDefinition(
                    key="total_records",
                    label="Total Records",
                    entity="",
                    metric="count",
                    category="operational",
                    formula="COUNT(*)",
                    source_columns=[],
                    aggregation="count",
                    confidence=1.0,
                    icon="📋",
                    description="Total number of records",
                ))
            elif template["key"] == "data_quality":
                kpis.append(KPIDefinition(
                    key="data_quality",
                    label="Data Quality Score",
                    entity="",
                    metric="quality",
                    category="quality",
                    formula="Composite quality score (0-100)",
                    source_columns=[],
                    aggregation="avg",
                    confidence=1.0,
                    icon="✅",
                    unit="%",
                    description="Overall data quality score",
                ))
        return kpis

    def _industry_kpis(
        self, df: pd.DataFrame, industry: str, col_mapping: dict
    ) -> list[KPIDefinition]:
        """Generate industry-specific KPIs with source columns."""
        templates = self.INDUSTRY_KPI_TEMPLATES.get(industry, [])
        kpis = []

        for template in templates:
            entity = template.get("entity")
            source_cols = self._find_columns_for_entity(col_mapping, entity) if entity else []

            # If no semantic mapping, try heuristic column matching
            if not source_cols and entity:
                source_cols = self._heuristic_find_columns(df, template["key"], entity)

            confidence = 1.0 if source_cols else 0.3
            if source_cols:
                confidence = min(1.0, 0.5 + 0.1 * len(source_cols))

            kpi = KPIDefinition(
                key=template["key"],
                label=template["label"],
                entity=entity or "",
                metric=template["metric"],
                category=template["category"],
                formula=template.get("formula", ""),
                source_columns=source_cols,
                aggregation=template.get("aggregation", "sum"),
                confidence=confidence,
                icon=template.get("icon", "📊"),
                unit=template.get("unit", ""),
                threshold_warning=template.get("threshold_warning"),
                threshold_critical=template.get("threshold_critical"),
                description=template.get("description", ""),
            )
            kpis.append(kpi)

        return kpis

    def _data_driven_kpis(
        self, df: pd.DataFrame, col_mapping: dict, existing: list[KPIDefinition]
    ) -> list[KPIDefinition]:
        """Detect additional KPIs from data characteristics."""
        kpis = []
        existing_keys = {k.key for k in existing}
        existing_cols = set()
        for k in existing:
            existing_cols.update(k.source_columns)

        numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
        for col in numeric_cols:
            if col in existing_cols:
                continue

            # Skip ID-like columns
            if col.lower().endswith("_id") or col.lower().endswith("_no"):
                continue

            # Sum KPI for numeric columns
            kpi_key = f"sum_{col.lower().replace(' ', '_')}"
            if kpi_key not in existing_keys:
                kpis.append(KPIDefinition(
                    key=kpi_key,
                    label=f"Total {col.replace('_', ' ').title()}",
                    entity=col_mapping.get(col, ""),
                    metric="sum",
                    category="financial" if self._looks_monetary(col) else "operational",
                    formula=f"SUM({col})",
                    source_columns=[col],
                    aggregation="sum",
                    confidence=0.6,
                    icon="💰" if self._looks_monetary(col) else "📊",
                    unit="currency" if self._looks_monetary(col) else "",
                    description=f"Sum of {col}",
                ))

            # Average KPI for numeric columns
            avg_key = f"avg_{col.lower().replace(' ', '_')}"
            if avg_key not in existing_keys and len(df) > 0:
                kpis.append(KPIDefinition(
                    key=avg_key,
                    label=f"Avg {col.replace('_', ' ').title()}",
                    entity=col_mapping.get(col, ""),
                    metric="avg",
                    category="operational",
                    formula=f"AVG({col})",
                    source_columns=[col],
                    aggregation="avg",
                    confidence=0.5,
                    icon="📊",
                    description=f"Average of {col}",
                ))

        # Limit data-driven KPIs to avoid overload
        return kpis[:8]

    def _registry_kpis(self, df: pd.DataFrame, industry: str, col_mapping: dict) -> list[KPIDefinition]:
        """Generate KPIs from KPIRegistry definitions."""
        kpis = []
        for definition in KPIRegistry.definitions(industry):
            source_cols = self._find_columns_for_entity(col_mapping, definition.entity)
            if not source_cols:
                continue

            knowledge = get_industry_knowledge(industry)
            kpi_info = {}
            if knowledge and "kpis" in knowledge:
                for category_kpis in knowledge["kpis"].values():
                    for kpi_name in category_kpis:
                        if definition.key in kpi_name:
                            kpi_info = {"formula": kpi_name}
                            break

            kpis.append(KPIDefinition(
                key=definition.key,
                label=definition.label,
                entity=definition.entity,
                metric=definition.metric,
                category=definition.category,
                formula=kpi_info.get("formula", f"{definition.metric.upper()}({definition.entity})"),
                source_columns=source_cols,
                aggregation=definition.metric,
                confidence=0.8 if source_cols else 0.3,
                icon="📊",
                threshold_warning=definition.threshold.get("warning") if definition.threshold else None,
                threshold_critical=definition.threshold.get("critical") if definition.threshold else None,
                description=f"{definition.label} from {definition.entity}",
            ))
        return kpis

    # ── Helpers ─────────────────────────────────────────

    @staticmethod
    def _find_columns_for_entity(col_mapping: dict, entity: str | None) -> list[str]:
        if not entity:
            return []
        return [col for col, ent in col_mapping.items() if ent == entity]

    @staticmethod
    def _heuristic_find_columns(df: pd.DataFrame, kpi_key: str, entity: str) -> list[str]:
        """Try to find columns by heuristic matching."""
        cols = []
        entity_lower = entity.lower()
        for col in df.columns:
            col_lower = col.lower().replace(" ", "_")
            if entity_lower in col_lower or col_lower.endswith(entity_lower):
                cols.append(col)
        return cols

    @staticmethod
    def _looks_monetary(col_name: str) -> bool:
        monetary_keywords = (
            "amount", "price", "cost", "revenue", "sales", "total",
            "balance", "fee", "charge", "payment", "billing", "salary",
            "budget", "spending", "donation", "tithe", "offering", "premium",
        )
        col_lower = col_name.lower()
        return any(kw in col_lower for kw in monetary_keywords)
