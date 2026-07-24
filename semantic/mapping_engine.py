"""MODULE 7 — Semantic Mapping Engine.

Orchestrates metadata extraction, data profiling, semantic analysis,
relationship detection, and industry detection into a unified pipeline.

Allows administrators to confirm or override mappings.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from semantic.data_profiler import DataProfiler, DatasetProfile
from semantic.industry_knowledge import get_industry_knowledge
from semantic.metadata_extractor import MetadataExtractor, TableMetadata
from semantic.relationship_engine import RelationshipEngine, RelationshipResult
from semantic.semantic_engine import SemanticEngine, SemanticResult


@dataclass
class SemanticMappingResult:
    """Complete result of the semantic mapping pipeline."""

    table_metadata: TableMetadata
    data_profile: DatasetProfile
    semantic_result: SemanticResult
    relationship_result: RelationshipResult
    industry: str
    industry_confidence: float
    business_entities: list[str]
    business_concepts: dict
    kpi_definitions: dict
    alerts: list[dict]
    ai_prompts: list[str]
    recommendations: list[str]
    overrides: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "metadata": self.table_metadata.to_dict(),
            "profile": self.data_profile.to_dict(),
            "semantic": self.semantic_result.to_dict(),
            "relationships": self.relationship_result.to_dict(),
            "industry": self.industry,
            "industry_confidence": round(self.industry_confidence, 2),
            "business_entities": self.business_entities,
            "business_concepts": self.business_concepts,
            "kpi_definitions": self.kpi_definitions,
            "alerts": self.alerts,
            "ai_prompts": self.ai_prompts,
            "recommendations": self.recommendations,
            "overrides": self.overrides,
        }


class SemanticMappingEngine:
    """Orchestrates the full semantic analysis pipeline."""

    @staticmethod
    def analyze(
        df: pd.DataFrame,
        table_name: str = "uploaded_dataset",
        overrides: dict | None = None,
    ) -> SemanticMappingResult:
        """Run the full semantic analysis pipeline.

        Args:
            df: DataFrame to analyze.
            table_name: Name for the dataset.
            overrides: Optional admin overrides {column_name: entity_key}.

        Returns:
            SemanticMappingResult with all analysis output.
        """
        # Step 1: Metadata extraction
        metadata = MetadataExtractor.extract(df, table_name)

        # Step 2: Data profiling
        profile = DataProfiler.profile(df)

        # Step 3: Semantic analysis
        semantic = SemanticEngine.analyze(df)

        # Step 4: Apply admin overrides
        overrides = overrides or {}
        if overrides:
            semantic = SemanticMappingEngine._apply_overrides(semantic, overrides)

        # Step 5: Relationship detection
        relationships = RelationshipEngine.detect(semantic, df)

        # Step 6: Industry knowledge enrichment
        industry = semantic.detected_industry
        industry_confidence = semantic.industry_confidence
        knowledge = get_industry_knowledge(industry)

        kpi_defs = knowledge.get("kpis", {}) if knowledge else {}
        alerts = knowledge.get("alerts", []) if knowledge else []
        ai_prompts = knowledge.get("ai_prompts", []) if knowledge else []
        recommendations = knowledge.get("recommendations", []) if knowledge else []

        return SemanticMappingResult(
            table_metadata=metadata,
            data_profile=profile,
            semantic_result=semantic,
            relationship_result=relationships,
            industry=industry,
            industry_confidence=industry_confidence,
            business_entities=semantic.detected_entities,
            business_concepts=semantic.business_concepts,
            kpi_definitions=kpi_defs,
            alerts=alerts,
            ai_prompts=ai_prompts,
            recommendations=recommendations,
            overrides=overrides,
        )

    @staticmethod
    def _apply_overrides(semantic: SemanticResult, overrides: dict) -> SemanticResult:
        """Apply admin overrides to semantic mappings."""
        from semantic.entity_library import ENTITY_LIBRARY
        from semantic.semantic_engine import SemanticMapping

        new_mappings = []
        overridden_columns = set()

        for mapping in semantic.mappings:
            if mapping.column_name in overrides:
                entity_key = overrides[mapping.column_name]
                entity = ENTITY_LIBRARY.get(entity_key)
                if entity:
                    new_mapping = SemanticMapping(
                        column_name=mapping.column_name,
                        entity_key=entity_key,
                        entity_display=entity["display_name"],
                        industry=entity["industry"],
                        confidence=1.0,
                        match_method="admin_override",
                        role=mapping.role,
                    )
                    new_mappings.append(new_mapping)
                    overridden_columns.add(mapping.column_name)
                else:
                    new_mappings.append(mapping)
            else:
                new_mappings.append(mapping)

        # Add new mappings for columns not previously mapped
        for col_name, entity_key in overrides.items():
            if col_name not in overridden_columns:
                entity = ENTITY_LIBRARY.get(entity_key)
                if entity:
                    new_mappings.append(
                        SemanticMapping(
                            column_name=col_name,
                            entity_key=entity_key,
                            entity_display=entity["display_name"],
                            industry=entity["industry"],
                            confidence=1.0,
                            match_method="admin_override",
                            role="attribute",
                        )
                    )

        # Recalculate detected entities and industry
        entity_keys = {m.entity_key for m in new_mappings}
        industry_votes: dict[str, int] = {}
        for m in new_mappings:
            if m.industry != "universal":
                industry_votes[m.industry] = industry_votes.get(m.industry, 0) + int(m.confidence)

        detected_industry = "unknown"
        industry_confidence = 0.0
        if industry_votes:
            best = max(industry_votes, key=industry_votes.get)
            total = sum(industry_votes.values())
            detected_industry = best
            industry_confidence = (industry_votes[best] / total * 100) if total > 0 else 0

        business_concepts = {}
        for ek in entity_keys:
            entity = ENTITY_LIBRARY.get(ek)
            if entity:
                business_concepts[ek] = {
                    "display_name": entity["display_name"],
                    "industry": entity["industry"],
                    "kpis": entity["kpis"],
                    "relationships": entity["relationships"],
                }

        return SemanticResult(
            mappings=new_mappings,
            detected_industry=detected_industry,
            industry_confidence=industry_confidence,
            detected_entities=sorted(entity_keys),
            business_concepts=business_concepts,
        )
