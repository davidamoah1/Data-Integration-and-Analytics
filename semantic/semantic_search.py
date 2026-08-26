"""MODULE 12 â€” Semantic Search.

Allows searching for business concepts across datasets even when
table or column names differ. E.g., searching "patients" finds
tbl_patient, hospital_patient, patient_master, etc.
"""

from __future__ import annotations

from semantic.entity_library import ENTITY_LIBRARY, get_all_synonyms
from semantic.semantic_engine import SemanticResult


class SemanticSearch:
    """Semantic search across business entities and columns."""

    @staticmethod
    def search(query: str, semantic_result: SemanticResult | None = None) -> dict:
        """Search for business concepts matching the query.

        Args:
            query: Natural language search query.
            semantic_result: Optional semantic result to search within.

        Returns:
            Dict with matching entities, columns, and synonyms.
        """
        query_lower = query.lower().strip()
        results = {
            "query": query,
            "matched_entities": [],
            "matched_columns": [],
            "matched_synonyms": [],
            "suggestions": [],
        }

        # 1. Search entity library
        for entity_key, entity in ENTITY_LIBRARY.items():
            # Check display name
            if query_lower in entity["display_name"].lower():
                results["matched_entities"].append(
                    {
                        "key": entity_key,
                        "display_name": entity["display_name"],
                        "industry": entity["industry"],
                    }
                )
                continue

            # Check synonyms
            for syn in entity["synonyms"]:
                if query_lower in syn.lower() or syn.lower() in query_lower:
                    results["matched_entities"].append(
                        {
                            "key": entity_key,
                            "display_name": entity["display_name"],
                            "industry": entity["industry"],
                            "matched_synonym": syn,
                        }
                    )
                    results["matched_synonyms"].append({"synonym": syn, "entity": entity_key})
                    break

        # 2. Search within semantic result (mapped columns)
        if semantic_result:
            for mapping in semantic_result.mappings:
                if (
                    query_lower in mapping.column_name.lower()
                    or query_lower in mapping.entity_display.lower()
                ):
                    results["matched_columns"].append(
                        {
                            "column": mapping.column_name,
                            "entity": mapping.entity_key,
                            "display": mapping.entity_display,
                            "confidence": mapping.confidence,
                        }
                    )

        # 3. Generate suggestions (entities in same industry)
        if results["matched_entities"]:
            industries = {
                e["industry"] for e in results["matched_entities"] if e["industry"] != "universal"
            }
            for ind in industries:
                for ek, ev in ENTITY_LIBRARY.items():
                    if ev["industry"] == ind and ek not in {
                        e["key"] for e in results["matched_entities"]
                    }:
                        results["suggestions"].append(
                            {
                                "key": ek,
                                "display_name": ev["display_name"],
                                "industry": ind,
                            }
                        )

        return results

    @staticmethod
    def search_columns(query: str, columns: list[str]) -> list[dict]:
        """Search for columns that match a business concept.

        Args:
            query: Business concept to search for (e.g., "patients").
            columns: List of column names to search within.

        Returns:
            List of matching columns with confidence scores.
        """
        query_lower = query.lower().strip()
        synonym_map = get_all_synonyms()

        # Find the entity the query refers to
        target_entity = None
        if query_lower in synonym_map:
            target_entity = synonym_map[query_lower]
        else:
            # Partial match
            for syn, entity_key in synonym_map.items():
                if query_lower in syn or syn in query_lower:
                    target_entity = entity_key
                    break

        if not target_entity:
            # Fallback: direct string match
            return [
                {"column": c, "entity": "unknown", "confidence": 0.5, "method": "string_match"}
                for c in columns
                if query_lower in c.lower()
            ]

        # Find all synonyms for the target entity
        entity = ENTITY_LIBRARY.get(target_entity, {})
        all_synonyms = set(entity.get("synonyms", []))
        all_synonyms.add(target_entity)

        results = []
        for col in columns:
            col_lower = col.lower().replace(" ", "_").replace("-", "_")
            for syn in all_synonyms:
                if col_lower == syn:
                    results.append(
                        {
                            "column": col,
                            "entity": target_entity,
                            "confidence": 1.0,
                            "method": "exact",
                        }
                    )
                    break
                elif syn in col_lower or col_lower in syn:
                    score = min(len(col_lower), len(syn)) / max(len(col_lower), len(syn))
                    results.append(
                        {
                            "column": col,
                            "entity": target_entity,
                            "confidence": score,
                            "method": "partial",
                        }
                    )
                    break

        return results
