"""Semantic Model — the brain of the platform.

Every dataset gets a metadata model that captures:
  - dataset identity (name, domain)
  - business entities (patient, doctor, department, ...)
  - metrics (patient_count, revenue, avg_stay, ...)
  - dimensions (region, gender, date, ...)
  - relationships (patient → admission → doctor)
  - business definitions (human-readable)
  - KPI dictionary (queryable, with computed values)
  - statistical patterns

This is what separates AEDIP from normal dashboards. Instead of
"show column X as a bar chart", the system understands that column X
is "patient_id" which means "Patient" which is an entity in the
"healthcare" domain, and it should be counted to produce "patient_count".
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from semantic.entity_library import ENTITY_LIBRARY
from semantic.industry_knowledge import get_industry_knowledge
from semantic.relationship_engine import RelationshipResult


@dataclass
class EntityDefinition:
    """A business entity detected in the dataset."""

    key: str
    display_name: str
    industry: str
    columns: list[str]  # which DataFrame columns map to this entity
    role: str  # entity, attribute, metric, dimension
    definition: str = ""
    synonyms: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "display_name": self.display_name,
            "industry": self.industry,
            "columns": self.columns,
            "role": self.role,
            "definition": self.definition,
            "synonyms": self.synonyms,
        }


@dataclass
class MetricDefinition:
    """A computed or computable metric for this dataset."""

    key: str
    label: str
    entity: str
    category: str  # operational, financial, clinical, academic, etc.
    aggregation: str  # sum, count, avg, min, max, distinct_count
    column: str | None = None
    value: float | None = None
    formatted: str = ""
    definition: str = ""
    threshold: dict | None = None

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "label": self.label,
            "entity": self.entity,
            "category": self.category,
            "aggregation": self.aggregation,
            "column": self.column,
            "value": self.value,
            "formatted": self.formatted,
            "definition": self.definition,
            "threshold": self.threshold,
        }


@dataclass
class DimensionDefinition:
    """A dimension for slicing/filtering data."""

    key: str
    display_name: str
    column: str
    cardinality: str  # low, medium, high
    sample_values: list = field(default_factory=list)
    definition: str = ""

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "display_name": self.display_name,
            "column": self.column,
            "cardinality": self.cardinality,
            "sample_values": [str(v) for v in self.sample_values[:10]],
            "definition": self.definition,
        }


@dataclass
class RelationshipDefinition:
    """A relationship between entities in this dataset."""

    source: str
    target: str
    type: str  # has_many, belongs_to, references, has
    label: str
    source_column: str = ""
    target_column: str = ""
    confidence: float = 1.0

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "target": self.target,
            "type": self.type,
            "label": self.label,
            "source_column": self.source_column,
            "target_column": self.target_column,
            "confidence": round(self.confidence, 2),
        }


@dataclass
class SemanticModel:
    """The metadata model for a single dataset.

    This is the central object that the dashboard, AI copilot, and
    analytics engine use to understand what the data means.
    """

    dataset: str
    domain: str  # industry: healthcare, banking, education, etc.
    domain_confidence: float = 0.0
    entities: list[EntityDefinition] = field(default_factory=list)
    metrics: list[MetricDefinition] = field(default_factory=list)
    dimensions: list[DimensionDefinition] = field(default_factory=list)
    relationships: list[RelationshipDefinition] = field(default_factory=list)
    business_rules: list[str] = field(default_factory=list)
    recommended_charts: list[str] = field(default_factory=list)
    ai_insights: list[str] = field(default_factory=list)
    row_count: int = 0
    column_count: int = 0
    quality_score: float = 0.0

    def to_dict(self) -> dict:
        return {
            "dataset": self.dataset,
            "domain": self.domain,
            "domain_confidence": round(self.domain_confidence, 2),
            "row_count": self.row_count,
            "column_count": self.column_count,
            "quality_score": round(self.quality_score, 2),
            "entities": [e.to_dict() for e in self.entities],
            "metrics": [m.to_dict() for m in self.metrics],
            "dimensions": [d.to_dict() for d in self.dimensions],
            "relationships": [r.to_dict() for r in self.relationships],
            "business_rules": self.business_rules,
            "recommended_charts": self.recommended_charts,
            "ai_insights": self.ai_insights,
        }

    def to_json(self) -> str:
        import json

        return json.dumps(self.to_dict(), indent=2, default=str)

    def get_entity(self, key: str) -> EntityDefinition | None:
        """Get an entity by key."""
        for e in self.entities:
            if e.key == key:
                return e
        return None

    def get_metric(self, key: str) -> MetricDefinition | None:
        """Get a metric by key."""
        for m in self.metrics:
            if m.key == key:
                return m
        return None

    def get_dimension(self, key: str) -> DimensionDefinition | None:
        """Get a dimension by key."""
        for d in self.dimensions:
            if d.key == key:
                return d
        return None

    def entity_keys(self) -> list[str]:
        """Return all entity keys."""
        return [e.key for e in self.entities]

    def metric_keys(self) -> list[str]:
        """Return all metric keys."""
        return [m.key for m in self.metrics]

    def dimension_keys(self) -> list[str]:
        """Return all dimension keys."""
        return [d.key for d in self.dimensions]


class SemanticModelBuilder:
    """Builds a SemanticModel from a SemanticMappingResult and DataFrame."""

    @staticmethod
    def build(
        df: pd.DataFrame,
        mapping_result,  # SemanticMappingResult (late import to avoid circular dep)
        dataset_name: str = "uploaded_dataset",
    ) -> SemanticModel:
        """Build a complete semantic model.

        Args:
            df: The DataFrame.
            mapping_result: Result from SemanticMappingEngine.analyze().
            dataset_name: Name for the dataset.

        Returns:
            SemanticModel with entities, metrics, dimensions, relationships.
        """
        semantic = mapping_result.semantic_result
        col_mapping = semantic.get_column_mapping()
        industry = mapping_result.industry
        knowledge = get_industry_knowledge(industry) or {}

        # Build entities
        entities = SemanticModelBuilder._build_entities(semantic, col_mapping)

        # Build dimensions
        dimensions = SemanticModelBuilder._build_dimensions(df, semantic, col_mapping)

        # Build metrics
        metrics = SemanticModelBuilder._build_metrics(df, mapping_result, industry)

        # Build relationships
        relationships = SemanticModelBuilder._build_relationships(
            mapping_result.relationship_result
        )

        # Industry knowledge
        business_rules = knowledge.get("business_rules", [])
        recommended_charts = knowledge.get("recommended_charts", [])
        ai_insights = knowledge.get("ai_prompts", [])

        return SemanticModel(
            dataset=dataset_name,
            domain=industry,
            domain_confidence=mapping_result.industry_confidence,
            entities=entities,
            metrics=metrics,
            dimensions=dimensions,
            relationships=relationships,
            business_rules=business_rules,
            recommended_charts=recommended_charts,
            ai_insights=ai_insights,
            row_count=len(df),
            column_count=len(df.columns),
            quality_score=mapping_result.data_profile.overall_quality_score,
        )

    @staticmethod
    def _build_entities(semantic, col_mapping: dict) -> list[EntityDefinition]:
        """Build entity definitions from semantic mappings."""
        entity_cols: dict[str, list[str]] = {}
        entity_roles: dict[str, str] = {}

        for mapping in semantic.mappings:
            entity_cols.setdefault(mapping.entity_key, []).append(mapping.column_name)
            entity_roles[mapping.entity_key] = mapping.role

        entities = []
        for key in sorted(entity_cols.keys()):
            entity_def = ENTITY_LIBRARY.get(key, {})
            industry = entity_def.get("industry", "universal")
            display = entity_def.get("display_name", key.replace("_", " ").title())
            synonyms = entity_def.get("synonyms", [])

            definition = BusinessDefinitions.get_entity_definition(key, industry)

            entities.append(EntityDefinition(
                key=key,
                display_name=display,
                industry=industry,
                columns=entity_cols[key],
                role=entity_roles.get(key, "attribute"),
                definition=definition,
                synonyms=synonyms,
            ))

        return entities

    @staticmethod
    def _build_dimensions(
        df: pd.DataFrame, semantic, col_mapping: dict
    ) -> list[DimensionDefinition]:
        """Build dimension definitions from semantic mappings."""
        dimension_entities = {"date", "region", "gender", "category", "department"}
        dimensions = []

        for mapping in semantic.mappings:
            if mapping.role == "dimension" or mapping.entity_key in dimension_entities:
                col = mapping.column_name
                if col not in df.columns:
                    continue

                series = df[col].dropna()
                unique_pct = (series.nunique() / max(len(series), 1) * 100) if len(series) > 0 else 0

                if unique_pct < 5:
                    cardinality = "low"
                elif unique_pct < 20:
                    cardinality = "medium"
                else:
                    cardinality = "high"

                sample = series.head(10).tolist()

                definition = BusinessDefinitions.get_dimension_definition(mapping.entity_key)

                dimensions.append(DimensionDefinition(
                    key=mapping.entity_key,
                    display_name=mapping.entity_display,
                    column=col,
                    cardinality=cardinality,
                    sample_values=sample,
                    definition=definition,
                ))

        return dimensions

    @staticmethod
    def _build_metrics(
        df: pd.DataFrame, mapping_result, industry: str
    ) -> list[MetricDefinition]:
        """Build metric definitions by computing KPIs."""
        from semantic.kpi_generator import KPIGenerator
        kpi_result = KPIGenerator.generate(df, mapping_result)
        knowledge = get_industry_knowledge(industry) or {}
        kpi_defs = knowledge.get("kpis", {})

        metrics = []
        col_mapping = mapping_result.semantic_result.get_column_mapping()
        for kpi in kpi_result.kpis:
            # Find definition text
            definition = BusinessDefinitions.get_metric_definition(kpi.key, industry)

            # Find threshold from KPI registry
            from semantic.kpi_registry import KPIRegistry
            threshold = None
            for reg_def in KPIRegistry.definitions(industry):
                if reg_def.key == kpi.key:
                    threshold = reg_def.threshold
                    break

            # Find the actual DataFrame column for this KPI's entity
            metric_column = None
            for col, entity_key in col_mapping.items():
                if entity_key == kpi.entity:
                    metric_column = col
                    break

            metrics.append(MetricDefinition(
                key=kpi.key,
                label=kpi.label,
                entity=kpi.entity,
                category=kpi.category,
                aggregation="sum" if kpi.value != int(kpi.value) else "count",
                column=metric_column,
                value=kpi.value,
                formatted=kpi.formatted,
                definition=definition,
                threshold=threshold,
            ))

        return metrics

    @staticmethod
    def _build_relationships(rel_result: RelationshipResult) -> list[RelationshipDefinition]:
        """Build relationship definitions from relationship result."""
        relationships = []
        for rel in rel_result.relationships:
            relationships.append(RelationshipDefinition(
                source=rel.source_entity,
                target=rel.target_entity,
                type=rel.relationship_type,
                label=rel.label,
                source_column=rel.source_column,
                target_column=rel.target_column,
                confidence=rel.confidence,
            ))
        return relationships


class BusinessDefinitions:
    """Human-readable business definitions for entities, metrics, and dimensions.

    This is the layer that makes the system understandable to humans.
    Instead of just "patient_count", it explains "Total number of unique
    patients who have visited the healthcare facility."
    """

    _entity_definitions: dict[str, str] = {
        "patient": "A person who receives medical care at a healthcare facility.",
        "doctor": "A medical professional who provides healthcare services to patients.",
        "admission": "A formal entry of a patient into a healthcare facility for treatment.",
        "ward": "A division of a hospital providing specific types of care.",
        "diagnosis": "The identification of a patient's medical condition.",
        "medicine": "A substance used to treat or prevent disease.",
        "lab_test": "A medical procedure to detect, diagnose, or monitor disease.",
        "appointment": "A scheduled meeting between a patient and healthcare provider.",
        "insurance": "Coverage that pays for healthcare expenses.",
        "billing": "The process of charging for healthcare services rendered.",
        "student": "A person enrolled in an educational institution for learning.",
        "teacher": "An educator who provides instruction to students.",
        "course": "A structured program of study in an educational curriculum.",
        "grade": "An evaluation of a student's academic performance.",
        "attendance": "The record of a student's presence in class.",
        "exam": "A formal assessment of a student's knowledge or proficiency.",
        "member": "A person who belongs to a church or organization.",
        "visitor": "A person who attends a church service but is not a member.",
        "tithe": "A mandatory financial contribution (typically 10% of income) to the church.",
        "offering": "A voluntary financial contribution to the church beyond tithes.",
        "customer": "A person who purchases goods or services from a business.",
        "order": "A request from a customer to purchase goods or services.",
        "product": "An item offered for sale to customers.",
        "revenue": "The total income generated from business activities.",
        "account": "A financial arrangement allowing deposits, withdrawals, and transactions.",
        "transaction": "A single financial exchange between parties.",
        "loan": "Money borrowed that must be repaid with interest.",
        "card": "A payment card issued by a bank for transactions.",
        "policy": "A contract between an insurer and insured providing coverage.",
        "claim": "A formal request for compensation under an insurance policy.",
        "agent": "A representative who sells and services insurance policies.",
        "reservation": "A booking for a room, table, or service in hospitality.",
        "guest": "A person who stays at a hospitality establishment.",
        "room": "A lodging unit available for guest occupancy.",
        "subscriber": "A person who subscribes to a telecommunications service.",
        "call": "A single telephone communication event.",
        "data_usage": "The amount of data consumed by a subscriber.",
        "plan": "A subscription tier with specific features and pricing.",
        "machine": "A piece of equipment used in manufacturing production.",
        "production": "The output of manufactured goods from a machine or line.",
        "downtime": "Periods when machines are not operational.",
        "crop": "A cultivated plant grown for food or commercial purposes.",
        "livestock": "Farm animals raised for production.",
        "farm": "An agricultural establishment where crops or livestock are raised.",
        "weather": "Environmental conditions affecting agricultural operations.",
        "citizen": "A person recognized as a member of a government jurisdiction.",
        "budget": "A financial plan for government spending.",
        "project": "A planned government initiative with defined scope and budget.",
        "procurement": "The process of acquiring goods or services by government.",
        "contractor": "A person or company engaged to execute government projects.",
        "donor": "A person or organization that contributes to an NGO.",
        "donation": "A financial contribution to an NGO or cause.",
        "grant": "A formal funding allocation from a donor to an NGO.",
        "beneficiary": "A person who receives benefits from an NGO program.",
        "program": "An organized initiative by an NGO to deliver services.",
        "date": "A temporal reference point for data records.",
        "region": "A geographic area used for grouping or filtering data.",
    }

    _dimension_definitions: dict[str, str] = {
        "date": "Time dimension — used for trend analysis, period comparisons, and seasonality detection.",
        "region": "Geographic dimension — used for spatial analysis and regional comparisons.",
        "gender": "Demographic dimension — used for gender-based segmentation.",
        "category": "Classification dimension — used for grouping data by category.",
        "department": "Organizational dimension — used for departmental analysis.",
    }

    _metric_definitions: dict[str, str] = {
        "total_revenue": "Total monetary value of all transactions in the dataset.",
        "avg_value": "Average value per transaction, calculated as total revenue divided by transaction count.",
        "total_transactions": "Total number of individual transactions or records.",
        "total_entities": "Count of unique business entities (patients, customers, students, etc.).",
        "total_profit": "Net profit after costs have been deducted from revenue.",
        "profit_margin": "Profit as a percentage of total revenue.",
        "data_quality": "Overall data quality score based on completeness, consistency, validity, and uniqueness.",
        "admissions": "Total number of patient admissions to the healthcare facility.",
        "patients": "Total number of unique patients in the dataset.",
        "bed_occupancy": "Current bed occupancy rate in the hospital wards.",
        "readmissions": "Number of patients readmitted within a specific period.",
        "billing": "Total billing amount for healthcare services rendered.",
        "enrollment": "Total number of enrolled students.",
        "attendance": "Student attendance count or rate.",
        "courses": "Number of distinct courses offered.",
        "fees": "Total fees collected from students.",
        "members": "Total number of church members.",
        "visitors": "Total number of church visitors.",
        "tithe": "Total tithe contributions received.",
        "offering": "Total offering contributions received.",
        "accounts": "Total number of bank accounts.",
        "transactions": "Total number of banking transactions.",
        "balance": "Total balance across all accounts.",
        "loans": "Total number of active loans.",
        "cards": "Total number of issued cards.",
        "policies": "Total number of active insurance policies.",
        "claims": "Total number of insurance claims filed.",
        "premium": "Total premium amount collected.",
        "claim_amount": "Total amount paid out in claims.",
        "agents": "Number of active insurance agents.",
        "reservations": "Total number of reservations booked.",
        "guests": "Total number of unique guests.",
        "rooms": "Total number of rooms available.",
        "subscribers": "Total number of active subscribers.",
        "calls": "Total number of calls made.",
        "data_usage": "Total data consumed in GB.",
        "plans": "Number of distinct service plans.",
        "production": "Total production output volume.",
        "machines": "Number of active machines.",
        "downtime": "Total downtime hours across all machines.",
        "harvest": "Total harvest volume.",
        "farms": "Number of farms in the dataset.",
        "livestock": "Total livestock count.",
        "beneficiaries": "Total number of beneficiaries reached.",
        "donors": "Total number of active donors.",
        "funding": "Total funding received from all sources.",
        "programs": "Number of active programs.",
    }

    @classmethod
    def get_entity_definition(cls, entity_key: str, industry: str = "") -> str:
        """Get a human-readable definition for an entity."""
        return cls._entity_definitions.get(entity_key, "")

    @classmethod
    def get_dimension_definition(cls, dimension_key: str) -> str:
        """Get a human-readable definition for a dimension."""
        return cls._dimension_definitions.get(dimension_key, "")

    @classmethod
    def get_metric_definition(cls, metric_key: str, industry: str = "") -> str:
        """Get a human-readable definition for a metric."""
        return cls._metric_definitions.get(metric_key, "")

    @classmethod
    def register_entity(cls, key: str, definition: str) -> None:
        cls._entity_definitions[key] = definition

    @classmethod
    def register_metric(cls, key: str, definition: str) -> None:
        cls._metric_definitions[key] = definition
