from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from semantic.governance import GovernanceEngine
from semantic.mapping_engine import SemanticMappingEngine


@dataclass(frozen=True)
class CatalogDocument:
    organization_id: int | None
    dataset_name: str
    industry: str
    industry_confidence: float
    metadata: dict
    quality: dict
    glossary_terms: list[dict]
    lineage: dict
    classifications: list[dict]
    tags: list[str]

    def to_dict(self) -> dict:
        return {
            "organization_id": self.organization_id,
            "dataset_name": self.dataset_name,
            "industry": self.industry,
            "industry_confidence": self.industry_confidence,
            "metadata": self.metadata,
            "quality": self.quality,
            "glossary_terms": self.glossary_terms,
            "lineage": self.lineage,
            "classifications": self.classifications,
            "tags": self.tags,
        }


class MetadataCatalogService:
    @staticmethod
    def build_document(
        df: pd.DataFrame,
        dataset_name: str = "uploaded_dataset",
        organization_id: int | None = None,
        overrides: dict | None = None,
    ) -> CatalogDocument:
        mapping = SemanticMappingEngine.analyze(df, dataset_name, overrides)
        governance = GovernanceEngine.analyze(mapping)
        glossary_terms = [
            {
                "term": item.term,
                "definition": item.definition,
                "entity": item.entity_key,
                "industry": item.industry,
            }
            for item in governance.glossary
        ]
        classifications = [
            {
                "column": item.column_name,
                "classification": item.classification,
                "sensitivity": item.sensitivity,
                "pii": item.pii,
            }
            for item in governance.data_dictionary
        ]
        tags = sorted(
            {
                mapping.industry,
                *(item.entity_key for item in mapping.semantic_result.mappings),
                *(item["classification"] for item in classifications),
            }
        )
        return CatalogDocument(
            organization_id=organization_id,
            dataset_name=dataset_name,
            industry=mapping.industry,
            industry_confidence=mapping.industry_confidence,
            metadata=mapping.table_metadata.to_dict(),
            quality=mapping.data_profile.to_dict(),
            glossary_terms=glossary_terms,
            lineage=governance.lineage,
            classifications=classifications,
            tags=tags,
        )

    @staticmethod
    def search(document: CatalogDocument, query: str) -> list[dict]:
        needle = query.strip().lower()
        if not needle:
            return []
        matches = []
        for column in document.metadata["columns"]:
            haystack = " ".join(
                [
                    column["name"],
                    column["dtype"],
                    document.industry,
                    *document.tags,
                ]
            ).lower()
            if needle in haystack:
                matches.append(
                    {"type": "column", "name": column["name"], "dataset": document.dataset_name}
                )
        for term in document.glossary_terms:
            haystack = " ".join(str(value) for value in term.values()).lower()
            if needle in haystack:
                matches.append({"type": "business_term", **term, "dataset": document.dataset_name})
        return matches
