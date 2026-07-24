"""MODULE 9 — KPI Generator.

Generates KPIs from business entities instead of SQL tables.
Uses semantic mappings to compute industry-appropriate KPIs.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from semantic.kpi_registry import KPIRegistry
from semantic.mapping_engine import SemanticMappingResult


@dataclass
class KPI:
    """A generated KPI."""

    key: str
    label: str
    value: float
    formatted: str
    entity: str
    category: str  # operational, financial, clinical, academic, etc.
    icon: str = "📊"


@dataclass
class KPIResultSet:
    """A set of generated KPIs."""

    kpis: list[KPI] = field(default_factory=list)
    industry: str = ""

    def to_dict(self) -> dict:
        return {
            "industry": self.industry,
            "kpis": [
                {
                    "key": k.key,
                    "label": k.label,
                    "value": k.value,
                    "formatted": k.formatted,
                    "entity": k.entity,
                    "category": k.category,
                    "icon": k.icon,
                }
                for k in self.kpis
            ],
        }

    def to_cards(self) -> list[dict]:
        """Return KPIs in a card-friendly format."""
        return [
            {
                "label": k.label,
                "value": k.formatted,
                "icon": k.icon,
                "entity": k.entity,
                "category": k.category,
            }
            for k in self.kpis
        ]


def _fmt_currency(v: float) -> str:
    if abs(v) >= 1_000_000:
        return f"${v / 1_000_000:.1f}M"
    elif abs(v) >= 1_000:
        return f"${v / 1_000:.1f}K"
    return f"${v:,.0f}"


def _fmt_number(v: float) -> str:
    if abs(v) >= 1_000_000:
        return f"{v / 1_000_000:.1f}M"
    elif abs(v) >= 1_000:
        return f"{v / 1_000:.1f}K"
    return f"{v:,.0f}"


def _fmt_pct(v: float) -> str:
    return f"{v:.1f}%"


class KPIGenerator:
    """Generates KPIs from business entities and semantic mappings."""

    @staticmethod
    def generate(df: pd.DataFrame, mapping_result: SemanticMappingResult) -> KPIResultSet:
        """Generate KPIs from a DataFrame using semantic mappings.

        Args:
            df: The DataFrame to compute KPIs from.
            mapping_result: Semantic mapping result.

        Returns:
            KPIResultSet with computed KPIs.
        """
        industry = mapping_result.industry
        col_mapping = mapping_result.semantic_result.get_column_mapping()
        kpis: list[KPI] = []

        # Find key columns
        revenue_col = KPIGenerator._find_column(
            col_mapping, ["revenue", "offering", "tithe", "donation", "billing"]
        )
        entity_id_col = KPIGenerator._find_column(
            col_mapping, ["order", "admission", "appointment", "donation"]
        )
        customer_col = KPIGenerator._find_column(
            col_mapping,
            ["patient", "student", "member", "customer", "donor", "beneficiary", "citizen"],
        )

        # Compute universal KPIs
        if revenue_col and revenue_col in df.columns:
            total_revenue = float(df[revenue_col].sum())
            kpis.append(
                KPI(
                    key="total_revenue",
                    label="Total Revenue" if industry == "retail" else "Total Amount",
                    value=total_revenue,
                    formatted=_fmt_currency(total_revenue),
                    entity="revenue",
                    category="financial",
                    icon="💰",
                )
            )

            # Average per transaction
            if entity_id_col and entity_id_col in df.columns:
                tx_count = df[entity_id_col].nunique()
            else:
                tx_count = len(df)
            avg_value = total_revenue / tx_count if tx_count > 0 else 0
            kpis.append(
                KPI(
                    key="avg_value",
                    label="Avg per Transaction",
                    value=avg_value,
                    formatted=_fmt_currency(avg_value),
                    entity="revenue",
                    category="financial",
                    icon="✨",
                )
            )

        # Transaction count
        if entity_id_col and entity_id_col in df.columns:
            tx_count = int(df[entity_id_col].nunique())
        else:
            tx_count = len(df)
        kpis.append(
            KPI(
                key="total_transactions",
                label="Total Transactions",
                value=tx_count,
                formatted=_fmt_number(tx_count),
                entity="order",
                category="operational",
                icon="🛒",
            )
        )

        # Unique entities (customers/patients/students/members/donors)
        if customer_col and customer_col in df.columns:
            entity_count = int(df[customer_col].nunique())
            entity_label = KPIGenerator._entity_label(industry, mapping_result)
            kpis.append(
                KPI(
                    key="total_entities",
                    label=f"Total {entity_label}",
                    value=entity_count,
                    formatted=_fmt_number(entity_count),
                    entity=customer_col,
                    category="operational",
                    icon="👥",
                )
            )

        # Profit (if available)
        profit_col = None
        for col in df.columns:
            if col.lower() in ("profit", "net_profit", "earnings", "margin", "net"):
                profit_col = col
                break
        if profit_col and profit_col in df.columns:
            total_profit = float(df[profit_col].sum())
            total_rev = (
                float(df[revenue_col].sum()) if revenue_col and revenue_col in df.columns else 0
            )
            margin = (total_profit / total_rev * 100) if total_rev > 0 else 0
            kpis.append(
                KPI(
                    key="total_profit",
                    label="Total Profit",
                    value=total_profit,
                    formatted=_fmt_currency(total_profit),
                    entity="revenue",
                    category="financial",
                    icon="📈",
                )
            )
            kpis.append(
                KPI(
                    key="profit_margin",
                    label=f"Profit Margin ({margin:.1f}%)",
                    value=margin,
                    formatted=_fmt_pct(margin),
                    entity="revenue",
                    category="financial",
                    icon="📊",
                )
            )

        # Data quality score
        quality = mapping_result.data_profile.overall_quality_score
        kpis.append(
            KPI(
                key="data_quality",
                label="Data Quality Score",
                value=quality,
                formatted=_fmt_pct(quality),
                entity="universal",
                category="quality",
                icon="✅",
            )
        )

        kpis.extend(KPIGenerator._registry_kpis(df, industry, col_mapping))

        return KPIResultSet(kpis=kpis, industry=industry)

    @staticmethod
    def _find_column(col_mapping: dict, entity_keys: list[str]) -> str | None:
        """Find a column mapped to any of the given entity keys."""
        for col, entity in col_mapping.items():
            if entity in entity_keys:
                return col
        return None

    @staticmethod
    def _entity_label(industry: str, mapping_result: SemanticMappingResult) -> str:
        """Get the appropriate label for the primary entity."""
        labels = {
            "healthcare": "Patients",
            "education": "Students",
            "church": "Members",
            "retail": "Customers",
            "government": "Citizens",
            "ngo": "Beneficiaries",
        }
        return labels.get(industry, "Entities")

    @staticmethod
    def _registry_kpis(df: pd.DataFrame, industry: str, col_mapping: dict) -> list[KPI]:
        kpis = []
        for definition in KPIRegistry.definitions(industry):
            column = KPIGenerator._find_column(col_mapping, [definition.entity])
            if not column or column not in df.columns:
                continue
            if definition.metric == "sum" and pd.api.types.is_numeric_dtype(df[column]):
                value = float(df[column].sum())
                formatted = _fmt_currency(value)
            else:
                value = int(df[column].nunique())
                formatted = _fmt_number(value)
            kpis.append(
                KPI(
                    key=definition.key,
                    label=definition.label,
                    value=value,
                    formatted=formatted,
                    entity=definition.entity,
                    category=definition.category,
                )
            )
        return kpis
