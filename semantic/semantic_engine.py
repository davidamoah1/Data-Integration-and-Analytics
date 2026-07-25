"""MODULE 3 — Semantic Engine.

Determines the BUSINESS MEANING of columns instead of relying on raw names.
Maps column names to business entities using:
  - Synonym matching
  - Fuzzy string similarity
  - Data type analysis
  - Sample value analysis
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from semantic.entity_library import ENTITY_LIBRARY, get_all_synonyms


@dataclass
class SemanticMapping:
    """Mapping of a column to a business entity."""

    column_name: str
    entity_key: str
    entity_display: str
    industry: str
    confidence: float
    match_method: str  # exact, synonym, fuzzy, heuristic
    role: str = "attribute"  # entity, attribute, metric, dimension


@dataclass
class SemanticResult:
    """Result of semantic analysis on a dataset."""

    mappings: list[SemanticMapping] = field(default_factory=list)
    detected_industry: str = "unknown"
    industry_confidence: float = 0.0
    detected_entities: list[str] = field(default_factory=list)
    business_concepts: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "mappings": [
                {
                    "column": m.column_name,
                    "entity": m.entity_key,
                    "display": m.entity_display,
                    "industry": m.industry,
                    "confidence": round(m.confidence, 2),
                    "method": m.match_method,
                    "role": m.role,
                }
                for m in self.mappings
            ],
            "detected_industry": self.detected_industry,
            "industry_confidence": round(self.industry_confidence, 2),
            "detected_entities": self.detected_entities,
            "business_concepts": self.business_concepts,
        }

    def get_column_mapping(self) -> dict[str, str]:
        """Return a simple column → entity_key mapping."""
        return {m.column_name: m.entity_key for m in self.mappings}

    def get_entity_columns(self, entity_key: str) -> list[str]:
        """Get all columns mapped to a specific entity."""
        return [m.column_name for m in self.mappings if m.entity_key == entity_key]


class SemanticEngine:
    """Maps raw column names to business entities."""

    SYNONYM_MAP: dict[str, str] = {}

    @classmethod
    def _ensure_synonyms(cls):
        if not cls.SYNONYM_MAP:
            cls.SYNONYM_MAP = get_all_synonyms()

    @classmethod
    def analyze(cls, df: pd.DataFrame) -> SemanticResult:
        """Analyze a DataFrame and produce semantic mappings.

        Args:
            df: DataFrame to analyze.

        Returns:
            SemanticResult with all mappings and detected industry.
        """
        cls._ensure_synonyms()
        mappings: list[SemanticMapping] = []
        industry_votes: dict[str, int] = {}
        entity_keys_found: set[str] = set()

        for col_name in df.columns:
            mapping = cls._map_column(df, col_name)
            if mapping:
                mappings.append(mapping)
                entity_keys_found.add(mapping.entity_key)
                if mapping.industry != "universal":
                    industry_votes[mapping.industry] = industry_votes.get(
                        mapping.industry, 0
                    ) + int(mapping.confidence)

        # Detect industry — no default fallback; "unknown" forces admin confirmation
        detected_industry = "unknown"
        industry_confidence = 0.0
        if industry_votes:
            best_industry = max(industry_votes, key=industry_votes.get)
            total_votes = sum(industry_votes.values())
            detected_industry = best_industry
            industry_confidence = (
                (industry_votes[best_industry] / total_votes * 100) if total_votes > 0 else 0
            )

        # Build business concepts summary
        business_concepts = {}
        for entity_key in entity_keys_found:
            entity = ENTITY_LIBRARY.get(entity_key)
            if entity:
                business_concepts[entity_key] = {
                    "display_name": entity["display_name"],
                    "industry": entity["industry"],
                    "kpis": entity["kpis"],
                    "relationships": entity["relationships"],
                }

        return SemanticResult(
            mappings=mappings,
            detected_industry=detected_industry,
            industry_confidence=industry_confidence,
            detected_entities=sorted(entity_keys_found),
            business_concepts=business_concepts,
        )

    @classmethod
    def _map_column(cls, df: pd.DataFrame, col_name: str) -> SemanticMapping | None:
        """Map a single column to a business entity."""
        normalized = col_name.lower().strip().replace(" ", "_").replace("-", "_")

        # 1. Exact synonym match
        if normalized in cls.SYNONYM_MAP:
            entity_key = cls.SYNONYM_MAP[normalized]
            entity = ENTITY_LIBRARY[entity_key]
            return SemanticMapping(
                column_name=col_name,
                entity_key=entity_key,
                entity_display=entity["display_name"],
                industry=entity["industry"],
                confidence=1.0,
                match_method="exact",
                role=cls._determine_role(normalized, entity_key, df, col_name),
            )

        # 2. Partial synonym match (contains or is contained)
        # Skip very short column names to avoid false positives (e.g. "age" -> "agent")
        if len(normalized) >= 4:
            for syn, entity_key in cls.SYNONYM_MAP.items():
                if syn in normalized or normalized in syn:
                    entity = ENTITY_LIBRARY[entity_key]
                    confidence = min(len(normalized), len(syn)) / max(len(normalized), len(syn))
                    if confidence > 0.6:
                        return SemanticMapping(
                            column_name=col_name,
                            entity_key=entity_key,
                            entity_display=entity["display_name"],
                            industry=entity["industry"],
                            confidence=confidence,
                            match_method="synonym",
                            role=cls._determine_role(normalized, entity_key, df, col_name),
                        )

        # 3. Fuzzy match using simple character overlap
        best_match = None
        best_score = 0.0
        for syn, entity_key in cls.SYNONYM_MAP.items():
            score = cls._fuzzy_score(normalized, syn)
            if score > best_score:
                best_score = score
                best_match = (entity_key, syn)

        if best_match and best_score > 0.5 and len(normalized) >= 4:
            entity_key, syn = best_match
            entity = ENTITY_LIBRARY[entity_key]
            return SemanticMapping(
                column_name=col_name,
                entity_key=entity_key,
                entity_display=entity["display_name"],
                industry=entity["industry"],
                confidence=best_score,
                match_method="fuzzy",
                role=cls._determine_role(normalized, entity_key, df, col_name),
            )

        # 4. Heuristic: data type based
        return cls._heuristic_map(df, col_name, normalized)

    @staticmethod
    def _fuzzy_score(a: str, b: str) -> float:
        """Simple fuzzy matching score based on character overlap."""
        if not a or not b:
            return 0.0
        a_set = set(a)
        b_set = set(b)
        intersection = a_set & b_set
        union = a_set | b_set
        jaccard = len(intersection) / len(union) if union else 0

        # Also check prefix match
        prefix_len = 0
        for i in range(min(len(a), len(b))):
            if a[i] == b[i]:
                prefix_len += 1
            else:
                break
        prefix_score = prefix_len / max(len(a), len(b)) if max(len(a), len(b)) > 0 else 0

        return jaccard * 0.4 + prefix_score * 0.6

    @staticmethod
    def _determine_role(normalized: str, entity_key: str, df: pd.DataFrame, col_name: str) -> str:
        """Determine if a column is an entity, attribute, metric, or dimension."""
        # If the column name IS the entity (e.g. patient_id → patient), it's an entity
        entity = ENTITY_LIBRARY.get(entity_key, {})
        synonyms = entity.get("synonyms", [])

        # ID columns are entities
        if (
            normalized.endswith("_id")
            or normalized.endswith("_no")
            or normalized.endswith("_number")
        ) and any(normalized == s or normalized.startswith(s) for s in synonyms):
            return "entity"

        # Numeric columns that match revenue/sales/amount are metrics
        metric_entities = {
            "revenue",
            "expense",
            "offering",
            "tithe",
            "donation",
            "billing",
            "production",
            "downtime",
            "machine",
            "crop",
            "livestock",
            "weather",
            "transaction",
            "loan",
            "card",
            "claim",
            "policy",
            "agent",
            "reservation",
            "room",
            "service",
            "call",
            "data_usage",
            "plan",
            "subscriber",
        }
        if entity_key in metric_entities:
            return "metric"

        # Date columns are dimensions
        if entity_key == "date":
            return "dimension"

        # Region/category are dimensions
        if entity_key in ("region",):
            return "dimension"

        # Otherwise it's an attribute
        return "attribute"

    @staticmethod
    def _heuristic_map(df: pd.DataFrame, col_name: str, normalized: str) -> SemanticMapping | None:
        """Heuristic mapping based on data type and patterns."""
        series = df[col_name]

        # Date columns
        if np.issubdtype(series.dtype, np.datetime64):
            return SemanticMapping(
                column_name=col_name,
                entity_key="date",
                entity_display="Date",
                industry="universal",
                confidence=0.7,
                match_method="heuristic",
                role="dimension",
            )

        # Check if it's a date stored as string
        if series.dtype == "object":
            sample = series.dropna().head(20)
            if len(sample) > 0:
                sample_str = sample.astype(str)
                date_like = sample_str.str.match(r"\d{4}[-/]\d{2}[-/]\d{2}")
                if date_like.all() and len(sample) > 3:
                    return SemanticMapping(
                        column_name=col_name,
                        entity_key="date",
                        entity_display="Date",
                        industry="universal",
                        confidence=0.6,
                        match_method="heuristic",
                        role="dimension",
                    )

        # Numeric columns → potential revenue/metric
        if np.issubdtype(series.dtype, np.number):
            # Check if values look like monetary amounts
            non_null = series.dropna()
            if len(non_null) > 0 and normalized in (
                "sales",
                "revenue",
                "amount",
                "total",
                "income",
                "turnover",
                "fee",
                "tuition",
                "price",
            ):
                return SemanticMapping(
                    column_name=col_name,
                    entity_key="revenue",
                    entity_display="Revenue",
                    industry="universal",
                    confidence=0.8,
                    match_method="heuristic",
                    role="metric",
                )

        # No match found
        return None
