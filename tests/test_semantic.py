"""Tests for the Semantic Intelligence Engine."""

import pandas as pd
import pytest

from semantic.catalog import MetadataCatalogService
from semantic.dashboard_generator import DashboardGenerator
from semantic.data_profiler import DataProfiler
from semantic.entity_library import ENTITY_LIBRARY, get_all_industries, get_all_synonyms
from semantic.governance import SENSITIVITY_RULES, GovernanceEngine
from semantic.industry_knowledge import INDUSTRY_KNOWLEDGE
from semantic.knowledge_graph import KnowledgeGraphBuilder
from semantic.kpi_generator import KPIGenerator
from semantic.mapping_engine import SemanticMappingEngine
from semantic.metadata_extractor import MetadataExtractor
from semantic.relationship_engine import RelationshipEngine
from semantic.semantic_engine import SemanticEngine
from semantic.semantic_search import SemanticSearch

# ── Test Data Fixtures ──


@pytest.fixture
def healthcare_df():
    return pd.DataFrame(
        {
            "patient_id": range(1, 101),
            "patient_name": [f"Patient {i}" for i in range(1, 101)],
            "admission_date": pd.date_range("2024-01-01", periods=100, freq="D"),
            "diagnosis": ["Diabetes", "Hypertension", "Flu", "Asthma"] * 25,
            "ward": ["ICU", "General", "Pediatric", "Maternity"] * 25,
            "doctor_name": [f"Dr. Smith {i % 10}" for i in range(100)],
            "billing_amount": [1000 + i * 50 for i in range(100)],
            "insurance_type": ["Blue Cross", "Aetna", "Cigna", "United"] * 25,
            "region": ["North", "South", "East", "West"] * 25,
        }
    )


@pytest.fixture
def education_df():
    return pd.DataFrame(
        {
            "student_id": range(1, 101),
            "student_name": [f"Student {i}" for i in range(1, 101)],
            "course": ["Math", "Science", "English", "History"] * 25,
            "department": ["Engineering", "Arts", "Business", "Medicine"] * 25,
            "tuition_fee": [500 + i * 10 for i in range(100)],
            "attendance_date": pd.date_range("2024-01-01", periods=100, freq="D"),
            "grade": ["A", "B", "C", "D"] * 25,
            "region": ["North", "South", "East", "West"] * 25,
        }
    )


@pytest.fixture
def church_df():
    return pd.DataFrame(
        {
            "member_id": range(1, 101),
            "member_name": [f"Member {i}" for i in range(1, 101)],
            "offering_amount": [100 + i * 5 for i in range(100)],
            "event_type": ["Sunday Service", "Midweek", "Special", "Conference"] * 25,
            "branch": ["Main", "North", "South", "East"] * 25,
            "payment_method": ["Cash", "Check", "Transfer", "Card"] * 25,
            "offering_date": pd.date_range("2024-01-01", periods=100, freq="D"),
        }
    )


@pytest.fixture
def retail_df():
    return pd.DataFrame(
        {
            "order_id": range(1, 101),
            "customer_name": [f"Customer {i}" for i in range(1, 101)],
            "product_name": [f"Product {i % 20}" for i in range(100)],
            "category": ["Electronics", "Clothing", "Food", "Books"] * 25,
            "sales": [100 + i * 10 for i in range(100)],
            "profit": [20 + i * 2 for i in range(100)],
            "quantity": [i % 10 + 1 for i in range(100)],
            "order_date": pd.date_range("2024-01-01", periods=100, freq="D"),
            "region": ["North", "South", "East", "West"] * 25,
        }
    )


@pytest.fixture
def ngo_df():
    return pd.DataFrame(
        {
            "donor_name": [f"Donor {i}" for i in range(1, 101)],
            "donation_amount": [500 + i * 20 for i in range(100)],
            "program": ["Education", "Health", "Water", "Food"] * 25,
            "funding_source": ["Grant", "Individual", "Corporate", "Government"] * 25,
            "project": [f"Project {i % 10}" for i in range(100)],
            "donation_date": pd.date_range("2024-01-01", periods=100, freq="D"),
            "region": ["North", "South", "East", "West"] * 25,
        }
    )


# ── MODULE 1: Metadata Extraction ──


class TestMetadataExtraction:
    def test_extract_basic(self, retail_df):
        meta = MetadataExtractor.extract(retail_df, "test_table")
        assert meta.name == "test_table"
        assert meta.row_count == 100
        assert meta.column_count == 9

    def test_column_metadata(self, retail_df):
        meta = MetadataExtractor.extract(retail_df)
        col = next(c for c in meta.columns if c.name == "sales")
        assert col.dtype is not None
        assert col.null_count == 0
        assert col.unique_count == 100

    def test_primary_key_detection(self, retail_df):
        meta = MetadataExtractor.extract(retail_df)
        assert "order_id" in meta.primary_keys

    def test_null_detection(self):
        df = pd.DataFrame({"a": [1, None, 3, None, 5], "b": [1, 2, 3, 4, 5]})
        meta = MetadataExtractor.extract(df)
        col_a = next(c for c in meta.columns if c.name == "a")
        assert col_a.null_count == 2
        assert col_a.null_pct == 40.0

    def test_value_distribution(self, retail_df):
        meta = MetadataExtractor.extract(retail_df)
        cat_col = next(c for c in meta.columns if c.name == "category")
        assert len(cat_col.value_distribution) > 0

    def test_numeric_stats(self, retail_df):
        meta = MetadataExtractor.extract(retail_df)
        sales_col = next(c for c in meta.columns if c.name == "sales")
        assert sales_col.min_value is not None
        assert sales_col.max_value is not None
        assert sales_col.mean_value is not None

    def test_foreign_key_detection(self):
        df = pd.DataFrame(
            {
                "id": range(1, 21),
                "customer_id": [1, 2, 3] * 6 + [1, 2],
                "product_id": [10, 20, 30] * 6 + [10, 20],
            }
        )
        meta = MetadataExtractor.extract(df)
        assert len(meta.foreign_keys) >= 2

    def test_to_dict(self, retail_df):
        meta = MetadataExtractor.extract(retail_df)
        d = meta.to_dict()
        assert "name" in d
        assert "columns" in d
        assert len(d["columns"]) == 9


# ── MODULE 2: Data Profiling ──


class TestDataProfiling:
    def test_profile_basic(self, retail_df):
        profile = DataProfiler.profile(retail_df)
        assert profile.row_count == 100
        assert profile.column_count == 9

    def test_completeness(self):
        df = pd.DataFrame({"a": [1, 2, None, 4, 5]})
        profile = DataProfiler.profile(df)
        col = next(c for c in profile.columns if c.name == "a")
        assert col.completeness == 80.0

    def test_duplicate_detection(self):
        df = pd.DataFrame({"a": [1, 1, 2, 3, 3]})
        profile = DataProfiler.profile(df)
        assert profile.duplicate_rows >= 0

    def test_outlier_detection(self):
        df = pd.DataFrame({"a": [1, 2, 3, 4, 100]})
        profile = DataProfiler.profile(df)
        col = next(c for c in profile.columns if c.name == "a")
        assert col.outlier_count >= 1

    def test_quality_score(self, retail_df):
        profile = DataProfiler.profile(retail_df)
        assert 0 <= profile.overall_quality_score <= 100

    def test_quality_issues(self):
        df = pd.DataFrame({"a": [None] * 80 + [1, 2, 3, 4, 5] * 4})
        profile = DataProfiler.profile(df)
        assert len(profile.quality_issues) > 0

    def test_to_dict(self, retail_df):
        profile = DataProfiler.profile(retail_df)
        d = profile.to_dict()
        assert "overall_quality_score" in d
        assert "columns" in d


# ── MODULE 3: Semantic Engine ──


class TestSemanticEngine:
    def test_analyze_retail(self, retail_df):
        result = SemanticEngine.analyze(retail_df)
        assert len(result.mappings) > 0
        assert result.detected_industry == "retail"

    def test_analyze_healthcare(self, healthcare_df):
        result = SemanticEngine.analyze(healthcare_df)
        assert "patient" in result.detected_entities
        assert result.detected_industry == "healthcare"

    def test_analyze_education(self, education_df):
        result = SemanticEngine.analyze(education_df)
        assert "student" in result.detected_entities
        assert result.detected_industry == "education"

    def test_analyze_church(self, church_df):
        result = SemanticEngine.analyze(church_df)
        assert "offering" in result.detected_entities or "member" in result.detected_entities
        assert result.detected_industry == "church"

    def test_analyze_ngo(self, ngo_df):
        result = SemanticEngine.analyze(ngo_df)
        assert "donation" in result.detected_entities or "donor" in result.detected_entities
        assert result.detected_industry == "ngo"

    def test_exact_synonym_match(self):
        df = pd.DataFrame({"patient_id": [1, 2], "patient_name": ["A", "B"]})
        result = SemanticEngine.analyze(df)
        mapping = next(m for m in result.mappings if m.column_name == "patient_id")
        assert mapping.entity_key == "patient"
        assert mapping.match_method == "exact"
        assert mapping.confidence == 1.0

    def test_fuzzy_match(self):
        df = pd.DataFrame({"patient_record": [1, 2], "patient_name": ["A", "B"]})
        result = SemanticEngine.analyze(df)
        # "patient_record" contains "patient" so should match via partial synonym
        assert any(m.entity_key == "patient" for m in result.mappings)

    def test_to_dict(self, retail_df):
        result = SemanticEngine.analyze(retail_df)
        d = result.to_dict()
        assert "mappings" in d
        assert "detected_industry" in d


# ── MODULE 4: Entity Library ──


class TestEntityLibrary:
    def test_entity_count(self):
        assert len(ENTITY_LIBRARY) >= 40

    def test_all_entities_have_required_fields(self):
        for _key, entity in ENTITY_LIBRARY.items():
            assert "display_name" in entity
            assert "industry" in entity
            assert "synonyms" in entity
            assert "kpis" in entity
            assert "relationships" in entity
            assert len(entity["synonyms"]) > 0

    def test_all_industries_present(self):
        industries = get_all_industries()
        assert "healthcare" in industries
        assert "education" in industries
        assert "church" in industries
        assert "retail" in industries
        assert "government" in industries
        assert "ngo" in industries

    def test_synonyms_map(self):
        synonyms = get_all_synonyms()
        assert "patient_id" in synonyms
        assert synonyms["patient_id"] == "patient"
        assert "student_name" in synonyms
        assert synonyms["student_name"] == "student"

    def test_get_entities_by_industry(self):
        from semantic.entity_library import get_entities_by_industry

        hc = get_entities_by_industry("healthcare")
        assert "patient" in hc
        assert "doctor" in hc
        # Universal entities should also be included
        assert "revenue" in hc

    def test_each_industry_has_entities(self):
        for industry in get_all_industries():
            from semantic.entity_library import get_entities_by_industry

            entities = get_entities_by_industry(industry)
            industry_entities = {k: v for k, v in entities.items() if v["industry"] == industry}
            assert (
                len(industry_entities) >= 3
            ), f"{industry} has only {len(industry_entities)} entities"


# ── MODULE 5: Relationship Engine ──


class TestRelationshipEngine:
    def test_detect_relationships(self, healthcare_df):
        semantic = SemanticEngine.analyze(healthcare_df)
        rels = RelationshipEngine.detect(semantic, healthcare_df)
        assert len(rels.relationships) > 0

    def test_library_relationships(self, healthcare_df):
        semantic = SemanticEngine.analyze(healthcare_df)
        rels = RelationshipEngine.detect(semantic)
        # Patient should have relationships
        patient_rels = [r for r in rels.relationships if r.source_entity == "patient"]
        assert len(patient_rels) > 0

    def test_entity_graph(self, healthcare_df):
        semantic = SemanticEngine.analyze(healthcare_df)
        rels = RelationshipEngine.detect(semantic, healthcare_df)
        assert len(rels.entity_graph) > 0

    def test_to_dict(self, retail_df):
        semantic = SemanticEngine.analyze(retail_df)
        rels = RelationshipEngine.detect(semantic, retail_df)
        d = rels.to_dict()
        assert "relationships" in d
        assert "entity_graph" in d


# ── MODULE 6: Industry Knowledge Base ──


class TestIndustryKnowledge:
    def test_all_industries_have_knowledge(self):
        assert len(INDUSTRY_KNOWLEDGE) == 12

    def test_knowledge_structure(self):
        for _key, knowledge in INDUSTRY_KNOWLEDGE.items():
            assert "display_name" in knowledge
            assert "description" in knowledge
            assert "entities" in knowledge
            assert "kpis" in knowledge
            assert "business_rules" in knowledge
            assert "alerts" in knowledge
            assert "ai_prompts" in knowledge
            assert "recommendations" in knowledge

    def test_kpis_by_category(self):
        from semantic.industry_knowledge import get_industry_kpis

        healthcare_kpis = get_industry_kpis("healthcare")
        assert "operational" in healthcare_kpis
        assert "financial" in healthcare_kpis
        assert "clinical" in healthcare_kpis

    def test_alerts(self):
        from semantic.industry_knowledge import get_industry_alerts

        alerts = get_industry_alerts("healthcare")
        assert len(alerts) > 0
        for alert in alerts:
            assert "metric" in alert
            assert "severity" in alert
            assert "message" in alert

    def test_ai_prompts(self):
        from semantic.industry_knowledge import get_industry_prompts

        prompts = get_industry_prompts("education")
        assert len(prompts) > 0


# ── MODULE 7: Semantic Mapping Engine ──


class TestSemanticMappingEngine:
    def test_full_analysis(self, retail_df):
        result = SemanticMappingEngine.analyze(retail_df)
        assert result.industry == "retail"
        assert len(result.business_entities) > 0
        assert result.table_metadata.row_count == 100
        assert result.data_profile.row_count == 100

    def test_overrides(self, retail_df):
        overrides = {"region": "patient"}
        result = SemanticMappingEngine.analyze(retail_df, overrides=overrides)
        # Check that the override was applied
        mapping = next(m for m in result.semantic_result.mappings if m.column_name == "region")
        assert mapping.entity_key == "patient"
        assert mapping.match_method == "admin_override"

    def test_industry_detection_healthcare(self, healthcare_df):
        result = SemanticMappingEngine.analyze(healthcare_df)
        assert result.industry == "healthcare"

    def test_industry_detection_education(self, education_df):
        result = SemanticMappingEngine.analyze(education_df)
        assert result.industry == "education"

    def test_industry_detection_church(self, church_df):
        result = SemanticMappingEngine.analyze(church_df)
        assert result.industry == "church"

    def test_industry_detection_ngo(self, ngo_df):
        result = SemanticMappingEngine.analyze(ngo_df)
        assert result.industry == "ngo"

    def test_kpi_definitions_populated(self, retail_df):
        result = SemanticMappingEngine.analyze(retail_df)
        assert len(result.kpi_definitions) > 0

    def test_to_dict(self, retail_df):
        result = SemanticMappingEngine.analyze(retail_df)
        d = result.to_dict()
        assert "metadata" in d
        assert "profile" in d
        assert "semantic" in d
        assert "relationships" in d


# ── MODULE 8: Knowledge Graph ──


class TestKnowledgeGraph:
    def test_build_graph(self, healthcare_df):
        mapping = SemanticMappingEngine.analyze(healthcare_df)
        graph = KnowledgeGraphBuilder.build(mapping)
        assert len(graph.nodes) > 0
        assert len(graph.edges) > 0

    def test_entity_nodes(self, healthcare_df):
        mapping = SemanticMappingEngine.analyze(healthcare_df)
        graph = KnowledgeGraphBuilder.build(mapping)
        entity_nodes = graph.get_nodes_by_type("entity")
        assert len(entity_nodes) > 0

    def test_kpi_nodes(self, healthcare_df):
        mapping = SemanticMappingEngine.analyze(healthcare_df)
        graph = KnowledgeGraphBuilder.build(mapping)
        kpi_nodes = graph.get_nodes_by_type("kpi")
        assert len(kpi_nodes) > 0

    def test_industry_node(self, retail_df):
        mapping = SemanticMappingEngine.analyze(retail_df)
        graph = KnowledgeGraphBuilder.build(mapping)
        industry_nodes = graph.get_nodes_by_type("industry")
        assert len(industry_nodes) == 1

    def test_column_nodes(self, retail_df):
        mapping = SemanticMappingEngine.analyze(retail_df)
        graph = KnowledgeGraphBuilder.build(mapping)
        column_nodes = graph.get_nodes_by_type("column")
        assert len(column_nodes) > 0

    def test_search(self, healthcare_df):
        mapping = SemanticMappingEngine.analyze(healthcare_df)
        graph = KnowledgeGraphBuilder.build(mapping)
        results = graph.search("patient")
        assert len(results) > 0

    def test_to_dict(self, retail_df):
        mapping = SemanticMappingEngine.analyze(retail_df)
        graph = KnowledgeGraphBuilder.build(mapping)
        d = graph.to_dict()
        assert "nodes" in d
        assert "edges" in d
        assert "stats" in d


# ── MODULE 9: KPI Generator ──


class TestKPIGenerator:
    def test_generate_kpis(self, retail_df):
        mapping = SemanticMappingEngine.analyze(retail_df)
        kpis = KPIGenerator.generate(retail_df, mapping)
        assert len(kpis.kpis) > 0
        assert kpis.industry == "retail"

    def test_revenue_kpi(self, retail_df):
        mapping = SemanticMappingEngine.analyze(retail_df)
        kpis = KPIGenerator.generate(retail_df, mapping)
        revenue_kpi = next(k for k in kpis.kpis if k.key == "total_revenue")
        assert revenue_kpi.value > 0

    def test_healthcare_kpis(self, healthcare_df):
        mapping = SemanticMappingEngine.analyze(healthcare_df)
        kpis = KPIGenerator.generate(healthcare_df, mapping)
        assert kpis.industry == "healthcare"
        assert any(k.entity in ("revenue", "billing") for k in kpis.kpis)

    def test_data_quality_kpi(self, retail_df):
        mapping = SemanticMappingEngine.analyze(retail_df)
        kpis = KPIGenerator.generate(retail_df, mapping)
        quality_kpi = next(k for k in kpis.kpis if k.key == "data_quality")
        assert 0 <= quality_kpi.value <= 100

    def test_to_cards(self, retail_df):
        mapping = SemanticMappingEngine.analyze(retail_df)
        kpis = KPIGenerator.generate(retail_df, mapping)
        cards = kpis.to_cards()
        assert len(cards) > 0
        assert "label" in cards[0]
        assert "value" in cards[0]


# ── MODULE 10: Dashboard Generator ──


class TestDashboardGenerator:
    def test_generate_dashboard(self, retail_df):
        mapping = SemanticMappingEngine.analyze(retail_df)
        config = DashboardGenerator.generate(retail_df, mapping, admin_confirmed=True)
        assert config.industry == "retail"
        assert len(config.kpi_cards) > 0
        assert len(config.charts) > 0

    def test_healthcare_dashboard_not_retail(self, healthcare_df):
        mapping = SemanticMappingEngine.analyze(healthcare_df)
        config = DashboardGenerator.generate(healthcare_df, mapping, admin_confirmed=True)
        assert config.industry == "healthcare"
        assert config.industry != "retail"

    def test_church_dashboard(self, church_df):
        mapping = SemanticMappingEngine.analyze(church_df)
        config = DashboardGenerator.generate(church_df, mapping, admin_confirmed=True)
        assert config.industry == "church"

    def test_ngo_dashboard(self, ngo_df):
        mapping = SemanticMappingEngine.analyze(ngo_df)
        config = DashboardGenerator.generate(ngo_df, mapping, admin_confirmed=True)
        assert config.industry == "ngo"

    def test_dashboard_has_filters(self, retail_df):
        mapping = SemanticMappingEngine.analyze(retail_df)
        config = DashboardGenerator.generate(retail_df, mapping, admin_confirmed=True)
        assert len(config.filters) > 0

    def test_dashboard_has_recommendations(self, retail_df):
        mapping = SemanticMappingEngine.analyze(retail_df)
        config = DashboardGenerator.generate(retail_df, mapping, admin_confirmed=True)
        assert len(config.recommendations) > 0

    def test_to_dict(self, retail_df):
        mapping = SemanticMappingEngine.analyze(retail_df)
        config = DashboardGenerator.generate(retail_df, mapping, admin_confirmed=True)
        d = config.to_dict()
        assert "title" in d
        assert "charts" in d


# ── MODULE 12: Semantic Search ──


class TestSemanticSearch:
    def test_search_patient(self):
        results = SemanticSearch.search("patient")
        assert len(results["matched_entities"]) > 0
        entity_keys = [e["key"] for e in results["matched_entities"]]
        assert "patient" in entity_keys

    def test_search_student(self):
        results = SemanticSearch.search("student")
        assert len(results["matched_entities"]) > 0
        entity_keys = [e["key"] for e in results["matched_entities"]]
        assert "student" in entity_keys

    def test_search_with_semantic_result(self, healthcare_df):
        semantic = SemanticEngine.analyze(healthcare_df)
        results = SemanticSearch.search("patient", semantic)
        assert len(results["matched_columns"]) > 0

    def test_search_columns(self):
        columns = ["patient_id", "patient_name", "student_no", "customer_code", "invoice_total"]
        results = SemanticSearch.search_columns("patient", columns)
        assert len(results) >= 2  # patient_id and patient_name
        for r in results:
            assert r["entity"] == "patient"

    def test_search_suggestions(self):
        results = SemanticSearch.search("patient")
        assert len(results["suggestions"]) > 0


# ── MODULE 13: Governance ──


class TestGovernance:
    def test_governance_analysis(self, healthcare_df):
        mapping = SemanticMappingEngine.analyze(healthcare_df)
        governance = GovernanceEngine.analyze(mapping)
        assert len(governance.glossary) > 0
        assert len(governance.data_dictionary) > 0

    def test_pii_classification(self, healthcare_df):
        mapping = SemanticMappingEngine.analyze(healthcare_df)
        governance = GovernanceEngine.analyze(mapping)
        # Patient data should be classified as PII
        patient_entries = [d for d in governance.data_dictionary if d.entity_key == "patient"]
        for entry in patient_entries:
            assert entry.pii is True
            assert entry.sensitivity == "high"

    def test_diagnosis_is_restricted(self, healthcare_df):
        mapping = SemanticMappingEngine.analyze(healthcare_df)
        governance = GovernanceEngine.analyze(mapping)
        diagnosis_entries = [d for d in governance.data_dictionary if d.entity_key == "diagnosis"]
        for entry in diagnosis_entries:
            assert entry.classification == "restricted"
            assert entry.sensitivity == "critical"

    def test_lineage(self, healthcare_df):
        mapping = SemanticMappingEngine.analyze(healthcare_df)
        governance = GovernanceEngine.analyze(mapping)
        assert "stages" in governance.lineage
        assert len(governance.lineage["stages"]) > 0

    def test_sensitivity_rules_exist(self):
        assert "patient" in SENSITIVITY_RULES
        assert "diagnosis" in SENSITIVITY_RULES
        assert "citizen" in SENSITIVITY_RULES

    def test_to_dict(self, retail_df):
        mapping = SemanticMappingEngine.analyze(retail_df)
        governance = GovernanceEngine.analyze(mapping)
        d = governance.to_dict()
        assert "glossary" in d
        assert "data_dictionary" in d
        assert "lineage" in d


# ── Integration: Full Pipeline ──


class TestFullPipeline:
    def test_full_analysis_retail(self, retail_df):
        from semantic.service import SemanticIntelligenceService

        result = SemanticIntelligenceService.analyze_dataset(retail_df)
        assert "mapping" in result
        assert "knowledge_graph" in result
        assert "kpis" in result
        assert "dashboard" in result
        assert "governance" in result

    def test_full_analysis_healthcare(self, healthcare_df):
        from semantic.service import SemanticIntelligenceService

        result = SemanticIntelligenceService.analyze_dataset(healthcare_df)
        assert result["mapping"]["industry"] == "healthcare"

    def test_detect_industry_quick(self, retail_df):
        from semantic.service import SemanticIntelligenceService

        result = SemanticIntelligenceService.detect_industry(retail_df)
        assert result["industry"] == "retail"
        assert "confidence" in result

    def test_get_glossary(self):
        from semantic.service import SemanticIntelligenceService

        glossary = SemanticIntelligenceService.get_business_glossary()
        assert len(glossary) > 0

    def test_ai_context(self, healthcare_df):
        from semantic.service import SemanticIntelligenceService

        ctx = SemanticIntelligenceService.get_ai_context(healthcare_df)
        assert ctx["detected_industry"] == "healthcare"
        assert "patient" in ctx["business_entities"]
        assert len(ctx["ai_prompts"]) > 0


# ── API Routes ──


class TestSemanticAPI:
    def test_health(self, client):
        resp = client.get("/semantic/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert len(data["modules"]) == 12

    def test_list_entities(self, client):
        resp = client.get("/semantic/entities")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 40

    def test_list_entities_by_industry(self, client):
        resp = client.get("/semantic/entities/healthcare")
        assert resp.status_code == 200
        data = resp.json()
        assert data["industry"] == "healthcare"
        assert data["total"] > 0

    def test_list_industries(self, client):
        resp = client.get("/semantic/industries")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 12

    def test_industry_detail(self, client):
        resp = client.get("/semantic/industries/healthcare")
        assert resp.status_code == 200
        data = resp.json()
        assert data["display_name"] == "Healthcare"

    def test_semantic_search(self, client):
        resp = client.post("/semantic/search", json={"query": "patient"})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["matched_entities"]) > 0

    def test_glossary(self, client):
        resp = client.get("/semantic/glossary")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] > 0

    def test_knowledge_graph_stats(self, client):
        resp = client.get("/semantic/knowledge-graph/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_entities"] >= 40
        assert data["total_industries"] == 12

    def test_dashboard_registry(self, client):
        resp = client.get("/semantic/dashboard-registry/healthcare")
        assert resp.status_code == 200
        data = resp.json()
        assert data["template"] == "healthcare_executive"
        assert any(widget["key"] == "patients" for widget in data["widgets"])
        assert not any(widget["key"] == "sales" for widget in data["widgets"])

    def test_kpi_registry(self, client):
        resp = client.get("/semantic/kpi-registry/education")
        assert resp.status_code == 200
        data = resp.json()
        assert any(kpi["key"] == "enrollment" for kpi in data["kpis"])

    def test_widget_registry(self, client):
        resp = client.get("/semantic/widget-registry")
        assert resp.status_code == 200
        assert "kpi_card" in resp.json()["widget_types"]

    def test_report_registry(self, client):
        resp = client.get("/semantic/report-registry/church")
        assert resp.status_code == 200
        assert "giving" in resp.json()["reports"]
        assert "sales" not in resp.json()["reports"]


class TestMetadataCatalog:
    def test_build_healthcare_catalog_document(self, healthcare_df):
        document = MetadataCatalogService.build_document(
            healthcare_df, "patient_admissions", organization_id=42
        )
        assert document.organization_id == 42
        assert document.industry == "healthcare"
        assert document.metadata["name"] == "patient_admissions"
        assert any(item["column"] == "patient_id" for item in document.classifications)

    def test_catalog_search_returns_business_terms(self, healthcare_df):
        document = MetadataCatalogService.build_document(healthcare_df)
        results = MetadataCatalogService.search(document, "patient")
        assert any(result["type"] == "business_term" for result in results)


class TestDashboardRegistryIsolation:
    def test_healthcare_uses_healthcare_widgets(self, healthcare_df):
        config = DashboardGenerator.generate(
            healthcare_df, SemanticMappingEngine.analyze(healthcare_df), admin_confirmed=True
        )
        widget_keys = {widget["key"] for widget in config.widgets}
        assert config.template == "healthcare_executive"
        assert "patients" in widget_keys
        assert "sales" not in widget_keys

    def test_education_uses_education_widgets(self, education_df):
        config = DashboardGenerator.generate(
            education_df, SemanticMappingEngine.analyze(education_df), admin_confirmed=True
        )
        widget_keys = {widget["key"] for widget in config.widgets}
        assert config.template == "education_executive"
        assert "enrollment" in widget_keys
        assert "patients" not in widget_keys

    def test_church_uses_church_widgets(self, church_df):
        config = DashboardGenerator.generate(
            church_df, SemanticMappingEngine.analyze(church_df), admin_confirmed=True
        )
        widget_keys = {widget["key"] for widget in config.widgets}
        assert config.template == "church_executive"
        assert "members" in widget_keys
        assert "students" not in widget_keys

    def test_retail_uses_sales_widgets(self, retail_df):
        config = DashboardGenerator.generate(
            retail_df, SemanticMappingEngine.analyze(retail_df), admin_confirmed=True
        )
        widget_keys = {widget["key"] for widget in config.widgets}
        assert config.template == "retail_executive"
        assert "sales" in widget_keys
        assert "patients" not in widget_keys

    def test_government_uses_government_widgets(self):
        df = pd.DataFrame(
            {
                "project_id": range(10),
                "project_name": [f"Project {index}" for index in range(10)],
                "department": ["Works", "Health"] * 5,
                "budget": [1000] * 10,
                "procurement": [f"Tender {index}" for index in range(10)],
            }
        )
        config = DashboardGenerator.generate(
            df, SemanticMappingEngine.analyze(df), admin_confirmed=True
        )
        widget_keys = {widget["key"] for widget in config.widgets}
        assert config.industry == "government"
        assert "projects" in widget_keys
        assert "sales" not in widget_keys
