"""Tests for the Semantic Model, Business Definitions, and Metric Engine.

Verifies that every dataset gets a structured metadata model with:
  - Domain (industry) classification
  - Business entities with definitions
  - Metrics with computed values, breakdowns, and trends
  - Dimensions with cardinality and sample values
  - Relationships between entities
  - Business rules from industry knowledge
"""

from __future__ import annotations

import pandas as pd
import pytest

from semantic.mapping_engine import SemanticMappingEngine
from semantic.metric_engine import MetricEngine, MetricResultSet
from semantic.semantic_model import (
    BusinessDefinitions,
)


@pytest.fixture
def healthcare_df():
    """Healthcare dataset with patients, doctors, diagnoses, billing."""
    return pd.DataFrame(
        {
            "patient_id": range(1, 21),
            "doctor_name": [f"Dr. {i}" for i in range(20)],
            "department": ["Cardiology"] * 10 + ["Neurology"] * 10,
            "diagnosis_code": [
                "A00.1",
                "B01.0",
                "C50.2",
                "D45.0",
                "E11.9",
                "F32.1",
                "G40.0",
                "H10.0",
                "I10.0",
                "J00.0",
                "K00.0",
                "L00.0",
                "M00.0",
                "N00.0",
                "O00.0",
                "P00.0",
                "Q00.0",
                "R00.0",
                "S00.0",
                "T00.0",
            ],
            "billing_amount": [1000 + i * 50 for i in range(20)],
            "visit_date": pd.date_range("2024-01-01", periods=20, freq="3D"),
            "gender": ["M", "F"] * 10,
        }
    )


@pytest.fixture
def retail_df():
    """Retail dataset with customers, orders, products, revenue."""
    return pd.DataFrame(
        {
            "order_id": range(1, 31),
            "customer_id": [i % 10 + 1 for i in range(30)],
            "product_name": [f"Product_{chr(65 + i % 5)}" for i in range(30)],
            "sales_amount": [100.0 + i * 10 for i in range(30)],
            "order_date": pd.date_range("2024-01-01", periods=30, freq="D"),
            "region": ["North", "South", "East", "West"] * 7 + ["North", "South"],
        }
    )


@pytest.fixture
def banking_df():
    """Banking dataset with accounts, transactions, loans."""
    return pd.DataFrame(
        {
            "account_number": [
                "GB82WEST12345698765432",
                "DE89370400440532013000",
                "FR1420041010050500013M02606",
                "IT60X0542811101000000123456",
                "ES9121000418450200051332",
                "GB29NWBK60161331926819",
                "DE75512108001235119613",
                "FR7630006000011234567890189",
                "IT05Q0542811101000000123456",
                "ES792100081361012345678901",
            ],
            "transaction_id": range(1, 11),
            "loan_id": range(100, 110),
            "amount": [5000, 10000, 15000, 20000, 25000, 30000, 35000, 40000, 45000, 50000],
            "transaction_date": pd.date_range("2024-01-01", periods=10, freq="D"),
        }
    )


class TestSemanticModel:
    """Test the SemanticModel data structure and builder."""

    def test_model_has_dataset_name(self, healthcare_df):
        result = SemanticMappingEngine.analyze(healthcare_df, "hospital_data.csv")
        model = result.semantic_model
        assert model is not None
        assert model.dataset == "hospital_data.csv"

    def test_model_has_domain(self, healthcare_df):
        result = SemanticMappingEngine.analyze(healthcare_df)
        model = result.semantic_model
        assert model.domain == "healthcare"
        assert model.domain_confidence > 0

    def test_model_has_entities(self, healthcare_df):
        result = SemanticMappingEngine.analyze(healthcare_df)
        model = result.semantic_model
        entity_keys = model.entity_keys()
        assert "patient" in entity_keys
        assert "doctor" in entity_keys

    def test_entities_have_definitions(self, healthcare_df):
        result = SemanticMappingEngine.analyze(healthcare_df)
        model = result.semantic_model
        patient = model.get_entity("patient")
        assert patient is not None
        assert patient.display_name == "Patient"
        assert len(patient.definition) > 0
        assert "medical care" in patient.definition.lower()
        assert len(patient.columns) > 0

    def test_model_has_metrics(self, healthcare_df):
        result = SemanticMappingEngine.analyze(healthcare_df)
        model = result.semantic_model
        assert len(model.metrics) > 0
        # Should have total revenue / billing
        metric_keys = model.metric_keys()
        assert any("billing" in k or "revenue" in k for k in metric_keys)

    def test_metrics_have_computed_values(self, healthcare_df):
        result = SemanticMappingEngine.analyze(healthcare_df)
        model = result.semantic_model
        for metric in model.metrics:
            assert metric.value is not None
            assert len(metric.formatted) > 0

    def test_model_has_dimensions(self, healthcare_df):
        result = SemanticMappingEngine.analyze(healthcare_df)
        model = result.semantic_model
        dim_keys = model.dimension_keys()
        assert "date" in dim_keys

    def test_dimensions_have_cardinality(self, healthcare_df):
        result = SemanticMappingEngine.analyze(healthcare_df)
        model = result.semantic_model
        for dim in model.dimensions:
            assert dim.cardinality in ("low", "medium", "high")
            assert len(dim.column) > 0

    def test_model_has_relationships(self, healthcare_df):
        result = SemanticMappingEngine.analyze(healthcare_df)
        model = result.semantic_model
        assert len(model.relationships) > 0

    def test_model_has_business_rules(self, healthcare_df):
        result = SemanticMappingEngine.analyze(healthcare_df)
        model = result.semantic_model
        assert len(model.business_rules) > 0
        assert any(
            "occupancy" in rule.lower() or "readmission" in rule.lower()
            for rule in model.business_rules
        )

    def test_model_has_recommended_charts(self, healthcare_df):
        result = SemanticMappingEngine.analyze(healthcare_df)
        model = result.semantic_model
        assert len(model.recommended_charts) > 0

    def test_model_has_ai_insights(self, healthcare_df):
        result = SemanticMappingEngine.analyze(healthcare_df)
        model = result.semantic_model
        assert len(model.ai_insights) > 0

    def test_model_to_dict(self, healthcare_df):
        result = SemanticMappingEngine.analyze(healthcare_df)
        model = result.semantic_model
        d = model.to_dict()
        assert d["dataset"] is not None
        assert d["domain"] == "healthcare"
        assert isinstance(d["entities"], list)
        assert isinstance(d["metrics"], list)
        assert isinstance(d["dimensions"], list)
        assert isinstance(d["relationships"], list)

    def test_model_to_json(self, healthcare_df):
        result = SemanticMappingEngine.analyze(healthcare_df)
        model = result.semantic_model
        import json

        data = json.loads(model.to_json())
        assert data["domain"] == "healthcare"

    def test_model_row_column_count(self, healthcare_df):
        result = SemanticMappingEngine.analyze(healthcare_df)
        model = result.semantic_model
        assert model.row_count == 20
        assert model.column_count == 7

    def test_retail_model(self, retail_df):
        result = SemanticMappingEngine.analyze(retail_df, "sales.csv")
        model = result.semantic_model
        assert model.domain == "retail"
        assert "customer" in model.entity_keys() or "order" in model.entity_keys()

    def test_banking_model(self, banking_df):
        result = SemanticMappingEngine.analyze(banking_df, "transactions.csv")
        model = result.semantic_model
        assert model.domain == "banking"


class TestBusinessDefinitions:
    """Test the business definition layer."""

    def test_entity_definition_patient(self):
        d = BusinessDefinitions.get_entity_definition("patient")
        assert "medical care" in d.lower()

    def test_entity_definition_student(self):
        d = BusinessDefinitions.get_entity_definition("student")
        assert "enrolled" in d.lower() or "education" in d.lower()

    def test_entity_definition_customer(self):
        d = BusinessDefinitions.get_entity_definition("customer")
        assert "purchas" in d.lower()

    def test_entity_definition_unknown(self):
        d = BusinessDefinitions.get_entity_definition("nonexistent_entity")
        assert d == ""

    def test_dimension_definition_date(self):
        d = BusinessDefinitions.get_dimension_definition("date")
        assert "time" in d.lower() or "temporal" in d.lower()

    def test_dimension_definition_region(self):
        d = BusinessDefinitions.get_dimension_definition("region")
        assert "geographic" in d.lower() or "spatial" in d.lower()

    def test_metric_definition_revenue(self):
        d = BusinessDefinitions.get_metric_definition("total_revenue")
        assert "monetary" in d.lower() or "income" in d.lower()

    def test_register_custom_entity(self):
        BusinessDefinitions.register_entity("custom_entity", "A custom test entity.")
        d = BusinessDefinitions.get_entity_definition("custom_entity")
        assert d == "A custom test entity."


class TestMetricEngine:
    """Test the MetricEngine computation layer."""

    def test_compute_returns_result_set(self, healthcare_df):
        result = SemanticMappingEngine.analyze(healthcare_df)
        model = result.semantic_model
        metrics = MetricEngine.compute(healthcare_df, model)
        assert isinstance(metrics, MetricResultSet)
        assert len(metrics.metrics) > 0

    def test_metrics_have_values(self, healthcare_df):
        result = SemanticMappingEngine.analyze(healthcare_df)
        metrics = result.metric_results
        assert metrics is not None
        for m in metrics.metrics:
            assert m.value is not None
            assert len(m.formatted) > 0

    def test_derived_metrics_present(self, healthcare_df):
        result = SemanticMappingEngine.analyze(healthcare_df)
        metrics = result.metric_results
        keys = [m.key for m in metrics.metrics]
        assert "record_count" in keys
        assert "column_count" in keys
        assert "data_completeness" in keys

    def test_record_count_correct(self, healthcare_df):
        result = SemanticMappingEngine.analyze(healthcare_df)
        metrics = result.metric_results
        record_count = metrics.get("record_count")
        assert record_count is not None
        assert record_count.value == 20.0

    def test_metrics_categorized(self, healthcare_df):
        result = SemanticMappingEngine.analyze(healthcare_df)
        metrics = result.metric_results
        categories = metrics.categories()
        assert "operational" in categories or "financial" in categories

    def test_by_category_filter(self, healthcare_df):
        result = SemanticMappingEngine.analyze(healthcare_df)
        metrics = result.metric_results
        financial = metrics.by_category("financial")
        assert len(financial) > 0
        for m in financial:
            assert m.category == "financial"

    def test_breakdowns_computed(self, healthcare_df):
        result = SemanticMappingEngine.analyze(healthcare_df)
        metrics = result.metric_results
        # At least one metric should have a breakdown
        has_breakdown = any(m.breakdown is not None for m in metrics.metrics)
        assert has_breakdown

    def test_trend_computed(self, healthcare_df):
        result = SemanticMappingEngine.analyze(healthcare_df)
        metrics = result.metric_results
        # At least one metric should have a trend (data has visit_date)
        has_trend = any(m.trend is not None for m in metrics.metrics)
        assert has_trend

    def test_metric_definitions_present(self, healthcare_df):
        result = SemanticMappingEngine.analyze(healthcare_df)
        metrics = result.metric_results
        for m in metrics.metrics:
            if m.key in ("record_count", "column_count", "data_completeness", "duplicate_rate"):
                assert len(m.definition) > 0

    def test_to_dict(self, healthcare_df):
        result = SemanticMappingEngine.analyze(healthcare_df)
        metrics = result.metric_results
        d = metrics.to_dict()
        assert d["domain"] == "healthcare"
        assert isinstance(d["metrics"], list)
        assert len(d["metrics"]) > 0

    def test_alert_thresholds(self, healthcare_df):
        result = SemanticMappingEngine.analyze(healthcare_df)
        metrics = result.metric_results
        # Metrics with thresholds should have alert field set
        for m in metrics.metrics:
            if m.threshold:
                assert m.alert in ("ok", "warning", "critical", None)

    def test_numeric_column_averages(self, healthcare_df):
        result = SemanticMappingEngine.analyze(healthcare_df)
        metrics = result.metric_results
        # billing_amount should get an average metric
        avg_metrics = [m for m in metrics.metrics if m.key.startswith("avg_")]
        assert len(avg_metrics) > 0


class TestFullPipeline:
    """Test the full pipeline: analyze â†’ model â†’ metrics â†’ to_dict."""

    def test_full_result_has_semantic_model(self, healthcare_df):
        result = SemanticMappingEngine.analyze(healthcare_df)
        assert result.semantic_model is not None
        assert result.metric_results is not None

    def test_full_result_to_dict(self, healthcare_df):
        result = SemanticMappingEngine.analyze(healthcare_df)
        d = result.to_dict()
        assert "semantic_model" in d
        assert "metric_results" in d
        assert d["semantic_model"]["domain"] == "healthcare"
        assert len(d["metric_results"]["metrics"]) > 0

    def test_example_format(self, healthcare_df):
        """Test the example from the user's request:
        Input: patient_id, doctor_name, diagnosis, visit_date
        Output: Industry: Healthcare, Entities: Patient, Doctor, Diagnosis
        """
        result = SemanticMappingEngine.analyze(healthcare_df, "hospital.csv")
        model = result.semantic_model

        assert model.dataset == "hospital.csv"
        assert model.domain == "healthcare"

        entity_keys = model.entity_keys()
        assert "patient" in entity_keys
        assert "doctor" in entity_keys
        assert "diagnosis" in entity_keys

        # Should have KPIs/metrics
        assert len(model.metrics) > 0
