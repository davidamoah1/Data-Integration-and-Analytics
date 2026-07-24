"""Main Semantic Intelligence Service.

Orchestrates the full pipeline:
  Upload → Metadata → Profiling → Semantic Mapping → Relationships
  → Industry Detection → Knowledge Graph → KPIs → Dashboard → Governance

This is the single entry point for the semantic layer.
"""

from __future__ import annotations

import logging

import pandas as pd

from semantic.dashboard_generator import DashboardGenerator
from semantic.governance import GovernanceEngine
from semantic.knowledge_graph import KnowledgeGraphBuilder
from semantic.kpi_generator import KPIGenerator
from semantic.mapping_engine import SemanticMappingEngine
from semantic.semantic_search import SemanticSearch

logger = logging.getLogger(__name__)


class SemanticIntelligenceService:
    """Main service for the semantic intelligence engine."""

    @staticmethod
    def analyze_dataset(
        df: pd.DataFrame,
        table_name: str = "uploaded_dataset",
        overrides: dict | None = None,
        admin_confirmed: bool = False,
    ) -> dict:
        """Run the full semantic analysis pipeline on a dataset.

        Args:
            df: DataFrame to analyze.
            table_name: Name for the dataset.
            overrides: Optional admin overrides {column_name: entity_key}.
            admin_confirmed: Whether admin has confirmed low-confidence industry detection.

        Returns:
            Complete analysis result as a dict.
        """
        logger.info(
            f"SemanticIntelligenceService: Analyzing dataset '{table_name}' with {len(df)} rows"
        )

        # Run the mapping engine
        mapping_result = SemanticMappingEngine.analyze(df, table_name, overrides)

        # Build knowledge graph
        knowledge_graph = KnowledgeGraphBuilder.build(mapping_result)

        # Generate KPIs
        kpi_result = KPIGenerator.generate(df, mapping_result)

        # Generate dashboard config (with confidence gate)
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
            logger.warning(
                f"Dashboard generation blocked for '{table_name}': {confirmation_reason}"
            )

        # Generate governance metadata
        governance_result = GovernanceEngine.analyze(mapping_result)

        result = {
            "mapping": mapping_result.to_dict(),
            "knowledge_graph": knowledge_graph.to_dict(),
            "kpis": kpi_result.to_dict(),
            "dashboard": dashboard_config.to_dict() if dashboard_config else None,
            "governance": governance_result.to_dict(),
            "needs_confirmation": needs_confirmation,
            "confirmation_reason": confirmation_reason,
        }
        return result

    @staticmethod
    def detect_industry(df: pd.DataFrame) -> dict:
        """Quick industry detection without full analysis.

        Args:
            df: DataFrame to analyze.

        Returns:
            Dict with detected industry and confidence.
        """
        mapping_result = SemanticMappingEngine.analyze(df)
        return {
            "industry": mapping_result.industry,
            "confidence": mapping_result.industry_confidence,
            "detected_entities": mapping_result.business_entities,
        }

    @staticmethod
    def semantic_search(query: str, df: pd.DataFrame | None = None) -> dict:
        """Perform semantic search.

        Args:
            query: Search query.
            df: Optional DataFrame to search within.

        Returns:
            Search results dict.
        """
        semantic_result = None
        if df is not None:
            semantic_result = SemanticMappingEngine.analyze(df).semantic_result
        return SemanticSearch.search(query, semantic_result)

    @staticmethod
    def get_business_glossary(df: pd.DataFrame | None = None) -> list[dict]:
        """Get business glossary entries.

        Args:
            df: Optional DataFrame to generate glossary from.

        Returns:
            List of glossary entries.
        """
        if df is not None:
            mapping_result = SemanticMappingEngine.analyze(df)
            governance = GovernanceEngine.analyze(mapping_result)
            return governance.to_dict()["glossary"]
        else:
            # Return full entity library as glossary
            from semantic.entity_library import ENTITY_LIBRARY

            return [
                {
                    "term": e["display_name"],
                    "definition": f"A {e['display_name']} entity in the {e['industry']} domain.",
                    "entity": k,
                    "industry": e["industry"],
                    "synonyms": e["synonyms"],
                }
                for k, e in ENTITY_LIBRARY.items()
            ]

    @staticmethod
    def get_ai_context(df: pd.DataFrame) -> dict:
        """Generate enriched AI context from semantic analysis.

        This replaces the raw table/column context in the AI context builder
        with business-meaning-aware context.

        Args:
            df: DataFrame to analyze.

        Returns:
            Dict with semantic context for AI consumption.
        """
        mapping_result = SemanticMappingEngine.analyze(df)
        knowledge_graph = KnowledgeGraphBuilder.build(mapping_result)

        return {
            "detected_industry": mapping_result.industry,
            "industry_confidence": mapping_result.industry_confidence,
            "business_entities": mapping_result.business_entities,
            "business_concepts": mapping_result.business_concepts,
            "column_mappings": mapping_result.semantic_result.to_dict()["mappings"],
            "relationships": mapping_result.relationship_result.to_dict()["relationships"],
            "kpi_definitions": mapping_result.kpi_definitions,
            "ai_prompts": mapping_result.ai_prompts,
            "recommendations": mapping_result.recommendations,
            "alerts": mapping_result.alerts,
            "data_quality": mapping_result.data_profile.to_dict()["overall_quality_score"],
            "knowledge_graph_stats": knowledge_graph.to_dict()["stats"],
        }
