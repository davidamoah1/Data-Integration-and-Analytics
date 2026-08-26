"""MODULE 5 â€” Relationship Engine.

Automatically identifies relationships between detected business entities
based on column names, foreign key detection, and entity library definitions.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from semantic.entity_library import ENTITY_LIBRARY
from semantic.semantic_engine import SemanticResult


@dataclass
class Relationship:
    """A relationship between two business entities."""

    source_entity: str
    target_entity: str
    relationship_type: str  # has_many, belongs_to, has, etc.
    label: str
    source_column: str = ""
    target_column: str = ""
    confidence: float = 1.0
    detected_via: str = "library"  # library, foreign_key, heuristic


@dataclass
class RelationshipResult:
    """Result of relationship detection."""

    relationships: list[Relationship] = field(default_factory=list)
    entity_graph: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "relationships": [
                {
                    "source": r.source_entity,
                    "target": r.target_entity,
                    "type": r.relationship_type,
                    "label": r.label,
                    "source_column": r.source_column,
                    "target_column": r.target_column,
                    "confidence": round(r.confidence, 2),
                    "detected_via": r.detected_via,
                }
                for r in self.relationships
            ],
            "entity_graph": self.entity_graph,
        }


class RelationshipEngine:
    """Detects relationships between business entities in a dataset."""

    @staticmethod
    def detect(
        semantic_result: SemanticResult, df: pd.DataFrame | None = None
    ) -> RelationshipResult:
        """Detect relationships from semantic mappings.

        Args:
            semantic_result: Result from SemanticEngine.analyze().
            df: Optional DataFrame for foreign key detection.

        Returns:
            RelationshipResult with all detected relationships.
        """
        relationships: list[Relationship] = []
        seen: set[tuple[str, str, str]] = set()
        entity_keys = set(semantic_result.detected_entities)

        # 1. Library-based relationships
        for entity_key in entity_keys:
            entity = ENTITY_LIBRARY.get(entity_key)
            if not entity:
                continue
            for rel in entity["relationships"]:
                target = rel["target"]
                # Only include if target entity is also detected or known
                if target in ENTITY_LIBRARY:
                    key = (entity_key, target, rel["type"])
                    if key not in seen:
                        seen.add(key)
                        relationships.append(
                            Relationship(
                                source_entity=entity_key,
                                target_entity=target,
                                relationship_type=rel["type"],
                                label=rel["label"],
                                confidence=0.9,
                                detected_via="library",
                            )
                        )

        # 2. Foreign key-based relationships
        if df is not None:
            fk_rels = RelationshipEngine._detect_fk_relationships(df, semantic_result)
            for rel in fk_rels:
                key = (rel.source_entity, rel.target_entity, rel.relationship_type)
                if key not in seen:
                    seen.add(key)
                    relationships.append(rel)

        # 3. Build entity graph
        graph: dict[str, list[dict]] = {}
        for rel in relationships:
            if rel.source_entity not in graph:
                graph[rel.source_entity] = []
            graph[rel.source_entity].append(
                {
                    "target": rel.target_entity,
                    "type": rel.relationship_type,
                    "label": rel.label,
                }
            )
            # Reverse relationship
            if rel.target_entity not in graph:
                graph[rel.target_entity] = []
            graph[rel.target_entity].append(
                {
                    "target": rel.source_entity,
                    "type": f"inverse_{rel.relationship_type}",
                    "label": rel.label,
                }
            )

        return RelationshipResult(relationships=relationships, entity_graph=graph)

    @staticmethod
    def _detect_fk_relationships(
        df: pd.DataFrame, semantic_result: SemanticResult
    ) -> list[Relationship]:
        """Detect relationships from foreign key-like columns."""
        rels = []
        col_mapping = semantic_result.get_column_mapping()

        for col_name, entity_key in col_mapping.items():
            normalized = col_name.lower().replace(" ", "_")
            if normalized.endswith("_id") and entity_key not in (
                "revenue",
                "expense",
                "date",
                "region",
            ):
                # This column references another entity
                ref_entity_name = normalized[:-3]
                # Try to find matching entity
                for ek, ev in ENTITY_LIBRARY.items():
                    if ref_entity_name in ev["synonyms"] or ref_entity_name == ek:
                        rels.append(
                            Relationship(
                                source_entity=entity_key,
                                target_entity=ek,
                                relationship_type="references",
                                label=f"via {col_name}",
                                source_column=col_name,
                                target_column="id",
                                confidence=0.7,
                                detected_via="foreign_key",
                            )
                        )
                        break

        return rels
