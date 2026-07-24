"""MODULE 13 — Governance.

Tracks business glossary, data dictionary, lineage, metadata versioning,
ownership, classification, sensitivity, and retention policies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from semantic.mapping_engine import SemanticMappingResult


@dataclass
class GlossaryEntry:
    """A business glossary entry."""

    term: str
    definition: str
    entity_key: str
    industry: str
    synonyms: list = field(default_factory=list)
    owner: str = ""
    steward: str = ""


@dataclass
class DataDictionaryEntry:
    """A data dictionary entry for a column."""

    column_name: str
    business_name: str
    entity_key: str
    data_type: str
    nullable: bool
    description: str = ""
    classification: str = "internal"  # public, internal, confidential, restricted
    sensitivity: str = "low"  # low, medium, high, critical
    owner: str = ""
    retention_days: int = 365
    pii: bool = False


@dataclass
class GovernanceResult:
    """Result of governance analysis."""

    glossary: list[GlossaryEntry] = field(default_factory=list)
    data_dictionary: list[DataDictionaryEntry] = field(default_factory=list)
    lineage: dict = field(default_factory=dict)
    classifications: dict = field(default_factory=dict)
    version: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {
            "glossary": [
                {
                    "term": g.term,
                    "definition": g.definition,
                    "entity": g.entity_key,
                    "industry": g.industry,
                    "synonyms": g.synonyms,
                    "owner": g.owner,
                    "steward": g.steward,
                }
                for g in self.glossary
            ],
            "data_dictionary": [
                {
                    "column": d.column_name,
                    "business_name": d.business_name,
                    "entity": d.entity_key,
                    "data_type": d.data_type,
                    "nullable": d.nullable,
                    "description": d.description,
                    "classification": d.classification,
                    "sensitivity": d.sensitivity,
                    "owner": d.owner,
                    "retention_days": d.retention_days,
                    "pii": d.pii,
                }
                for d in self.data_dictionary
            ],
            "lineage": self.lineage,
            "classifications": self.classifications,
            "version": self.version,
        }


# Classification rules: which entities are sensitive
SENSITIVITY_RULES: dict[str, tuple[str, str, bool]] = {
    # entity_key: (classification, sensitivity, is_pii)
    "patient": ("confidential", "high", True),
    "citizen": ("confidential", "high", True),
    "student": ("confidential", "medium", True),
    "member": ("internal", "medium", True),
    "customer": ("internal", "medium", True),
    "donor": ("internal", "medium", True),
    "beneficiary": ("confidential", "medium", True),
    "doctor": ("internal", "low", False),
    "teacher": ("internal", "low", False),
    "pastor": ("internal", "low", False),
    "revenue": ("internal", "medium", False),
    "billing": ("confidential", "high", True),
    "insurance": ("confidential", "high", True),
    "diagnosis": ("restricted", "critical", True),
    "grade": ("confidential", "medium", True),
    "offering": ("internal", "low", False),
    "donation": ("internal", "low", False),
}


class GovernanceEngine:
    """Generates governance metadata from semantic mappings."""

    @staticmethod
    def analyze(mapping_result: SemanticMappingResult) -> GovernanceResult:
        """Generate governance metadata.

        Args:
            mapping_result: Semantic mapping result.

        Returns:
            GovernanceResult with glossary, data dictionary, and classifications.
        """
        from semantic.entity_library import ENTITY_LIBRARY

        glossary: list[GlossaryEntry] = []
        data_dictionary: list[DataDictionaryEntry] = []
        classifications: dict = {}

        # Build glossary from detected entities
        for entity_key in mapping_result.business_entities:
            entity = ENTITY_LIBRARY.get(entity_key)
            if not entity:
                continue

            glossary.append(
                GlossaryEntry(
                    term=entity["display_name"],
                    definition=f"A {entity['display_name']} entity in the {entity['industry']} domain.",
                    entity_key=entity_key,
                    industry=entity["industry"],
                    synonyms=entity["synonyms"],
                )
            )

        # Build data dictionary from column mappings
        for mapping in mapping_result.semantic_result.mappings:
            entity = ENTITY_LIBRARY.get(mapping.entity_key, {})
            classification, sensitivity, is_pii = SENSITIVITY_RULES.get(
                mapping.entity_key, ("internal", "low", False)
            )

            # Find column metadata
            col_meta = None
            for cm in mapping_result.table_metadata.columns:
                if cm.name == mapping.column_name:
                    col_meta = cm
                    break

            data_dictionary.append(
                DataDictionaryEntry(
                    column_name=mapping.column_name,
                    business_name=entity.get("display_name", mapping.entity_display),
                    entity_key=mapping.entity_key,
                    data_type=col_meta.dtype if col_meta else "unknown",
                    nullable=col_meta.nullable if col_meta else True,
                    description=f"Maps to business entity: {entity.get('display_name', mapping.entity_display)}",
                    classification=classification,
                    sensitivity=sensitivity,
                    pii=is_pii,
                )
            )

            classifications[mapping.column_name] = {
                "classification": classification,
                "sensitivity": sensitivity,
                "pii": is_pii,
            }

        # Build lineage
        lineage = {
            "source": "uploaded_dataset",
            "stages": [
                {"stage": "upload", "action": "file_received"},
                {"stage": "metadata_extraction", "action": "schema_discovered"},
                {"stage": "data_profiling", "action": "quality_assessed"},
                {"stage": "semantic_mapping", "action": "entities_detected"},
                {"stage": "relationship_detection", "action": "relationships_mapped"},
                {"stage": "industry_detection", "action": f"industry={mapping_result.industry}"},
                {"stage": "knowledge_graph", "action": "graph_built"},
                {"stage": "kpi_generation", "action": "kpis_computed"},
                {"stage": "dashboard_generation", "action": "dashboard_configured"},
            ],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        return GovernanceResult(
            glossary=glossary,
            data_dictionary=data_dictionary,
            lineage=lineage,
            classifications=classifications,
        )
