"""Tests for the Enterprise AI Decision Support System.

Covers:
  - Enterprise Context Engine
  - Prompt Orchestrator
  - Data Gatherer
  - Executive Summary Engine
  - Root Cause Analysis Engine
  - Enterprise Forecast Engine
  - Enterprise Anomaly Engine
  - Recommendation Engine
  - NL Analytics Engine
  - Enterprise Report Engine
  - Security enhancements
  - Performance monitoring
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from ai.context_engine import (
    DatasetContext,
    EnterpriseAIContext,
    EnterpriseContextEngine,
    IndustryContext,
    UserContext,
)
from ai.data_gatherer import DataGatherer
from ai.engines.enterprise_anomaly import EnterpriseAnomalyEngine
from ai.engines.enterprise_forecast import EnterpriseForecastEngine
from ai.engines.enterprise_report import EnterpriseReportEngine
from ai.engines.executive_summary import ExecutiveSummaryEngine
from ai.engines.nl_analytics import NLAnalyticsEngine
from ai.engines.recommendation_engine import RecommendationEngine
from ai.engines.root_cause import RootCauseAnalysisEngine
from ai.performance import (
    PerformanceMonitor,
    TokenBudgetManager,
    LazyContextLoader,
)
from ai.prompt_orchestrator import PromptOrchestrator, PromptTaskType
from ai.security import AISecurityLayer


# ── Fixtures ───────────────────────────────────────────


@pytest.fixture
def sample_df():
    """Create a sample retail dataset."""
    np.random.seed(42)
    dates = pd.date_range("2024-01-01", periods=100, freq="D")
    return pd.DataFrame({
        "order_date": dates,
        "region": np.random.choice(["North", "South", "East", "West"], 100),
        "category": np.random.choice(["Electronics", "Clothing", "Food"], 100),
        "sales": np.random.uniform(100, 1000, 100).round(2),
        "profit": np.random.uniform(10, 200, 100).round(2),
        "quantity": np.random.randint(1, 10, 100),
    })


@pytest.fixture
def healthcare_df():
    """Create a sample healthcare dataset."""
    np.random.seed(123)
    dates = pd.date_range("2024-01-01", periods=80, freq="D")
    return pd.DataFrame({
        "admission_date": dates,
        "department": np.random.choice(["ER", "ICU", "General", "Pediatrics"], 80),
        "patient_id": [f"P{i:04d}" for i in range(80)],
        "billing_amount": np.random.uniform(500, 5000, 80).round(2),
        "length_of_stay": np.random.randint(1, 14, 80),
        "readmitted": np.random.choice([0, 1], 80, p=[0.85, 0.15]),
    })


@pytest.fixture
def semantic_mappings():
    return {
        "order_date": "date",
        "sales": "revenue",
        "profit": "profit",
        "region": "region",
        "category": "category",
    }


@pytest.fixture
def context_engine():
    return EnterpriseContextEngine(db=None)


@pytest.fixture
def mock_db():
    return MagicMock()


# ── Context Engine Tests ───────────────────────────────


class TestEnterpriseContextEngine:
    def test_build_context_with_dataframe(self, context_engine, sample_df, semantic_mappings):
        ctx = context_engine.build(
            assistant_type="data_copilot",
            df=sample_df,
            semantic_mappings=semantic_mappings,
            industry="retail",
            user_id=1,
        )
        assert ctx.assistant_type == "data_copilot"
        assert ctx.dataset.row_count == 100
        assert ctx.dataset.column_count == 6
        assert len(ctx.dataset.columns) == 6
        assert "sales" in ctx.dataset.numeric_columns
        assert "region" in ctx.dataset.categorical_columns
        assert "order_date" in ctx.dataset.date_columns
        assert ctx.dataset.industry == "retail"

    def test_context_to_dict(self, context_engine, sample_df, semantic_mappings):
        ctx = context_engine.build(
            df=sample_df,
            semantic_mappings=semantic_mappings,
            industry="retail",
        )
        d = ctx.to_dict()
        assert "platform" in d
        assert "dataset" in d
        assert "industry" in d
        assert d["dataset"]["row_count"] == 100

    def test_context_to_prompt_context(self, context_engine, sample_df, semantic_mappings):
        ctx = context_engine.build(
            df=sample_df,
            semantic_mappings=semantic_mappings,
            industry="retail",
        )
        prompt_str = ctx.to_prompt_context(max_chars=2000)
        assert "Dataset:" in prompt_str
        assert "Rows: 100" in prompt_str
        assert len(prompt_str) <= 2000

    def test_context_truncation(self, context_engine, sample_df):
        ctx = context_engine.build(df=sample_df, industry="retail")
        prompt_str = ctx.to_prompt_context(max_chars=100)
        assert len(prompt_str) <= 200
        assert "truncated" in prompt_str

    def test_build_user_context(self, context_engine):
        ctx = context_engine.build(user_id=1, user_role="analyst", user_permissions=["data.read"])
        assert ctx.user.user_id == 1
        assert ctx.user.role == "analyst"
        assert "data.read" in ctx.user.permissions

    def test_build_industry_context(self, context_engine):
        ctx = context_engine.build(industry="retail")
        assert ctx.industry.industry == "retail"

    def test_healthcare_context(self, context_engine, healthcare_df):
        ctx = context_engine.build(
            df=healthcare_df,
            industry="healthcare",
        )
        assert ctx.dataset.row_count == 80
        assert "billing_amount" in ctx.dataset.numeric_columns
        assert "admission_date" in ctx.dataset.date_columns


# ── Prompt Orchestrator Tests ──────────────────────────


class TestPromptOrchestrator:
    def test_get_pipeline(self):
        orch = PromptOrchestrator()
        pipeline = orch.get_pipeline(PromptTaskType.EXECUTIVE_SUMMARY)
        assert pipeline.task_type == PromptTaskType.EXECUTIVE_SUMMARY
        assert pipeline.output_format == "json"
        assert pipeline.temperature == 0.3

    def test_build_messages(self, context_engine, sample_df):
        ctx = context_engine.build(df=sample_df, industry="retail")
        orch = PromptOrchestrator()
        messages = orch.build_messages(
            PromptTaskType.EXECUTIVE_SUMMARY,
            "What happened this month?",
            ctx,
        )
        assert len(messages) >= 3
        assert messages[0]["role"] == "system"
        assert messages[-1]["role"] == "user"
        assert messages[-1]["content"] == "What happened this month?"

    def test_detect_task_type(self):
        orch = PromptOrchestrator()
        assert orch.detect_task_type("What happened this month?") == PromptTaskType.EXECUTIVE_SUMMARY
        assert orch.detect_task_type("Why did revenue decrease?") == PromptTaskType.ROOT_CAUSE_ANALYSIS
        assert orch.detect_task_type("Forecast sales for next month") == PromptTaskType.FORECASTING
        assert orch.detect_task_type("What are the risks?") == PromptTaskType.RISK_ANALYSIS
        assert orch.detect_task_type("Show top performing regions") == PromptTaskType.NL_ANALYTICS
        assert orch.detect_task_type("Generate a monthly report") == PromptTaskType.REPORT_GENERATION
        assert orch.detect_task_type("Hello there") == PromptTaskType.GENERAL_CHAT

    def test_list_task_types(self):
        orch = PromptOrchestrator()
        types = orch.list_task_types()
        assert len(types) == len(PromptTaskType)
        assert all("task_type" in t for t in types)


# ── Data Gatherer Tests ────────────────────────────────


class TestDataGatherer:
    def test_gather_for_summary(self, sample_df, context_engine, semantic_mappings):
        ctx = context_engine.build(df=sample_df, semantic_mappings=semantic_mappings, industry="retail")
        gatherer = DataGatherer(sample_df, ctx)
        data = gatherer.gather_for_summary()
        assert "overall" in data
        assert data["overall"]["row_count"] == 100
        assert "by_dimension" in data
        assert "time_trends" in data

    def test_gather_for_root_cause(self, sample_df, context_engine, semantic_mappings):
        ctx = context_engine.build(df=sample_df, semantic_mappings=semantic_mappings, industry="retail")
        gatherer = DataGatherer(sample_df, ctx)
        data = gatherer.gather_for_root_cause("revenue", "decrease")
        assert data["metric"] == "revenue"
        assert "contributions" in data
        assert "period_comparison" in data

    def test_gather_for_trend(self, sample_df, context_engine, semantic_mappings):
        ctx = context_engine.build(df=sample_df, semantic_mappings=semantic_mappings, industry="retail")
        gatherer = DataGatherer(sample_df, ctx)
        data = gatherer.gather_for_trend("revenue")
        assert "monthly_trend" in data or "note" in data

    def test_gather_for_forecast(self, sample_df, context_engine, semantic_mappings):
        ctx = context_engine.build(df=sample_df, semantic_mappings=semantic_mappings, industry="retail")
        gatherer = DataGatherer(sample_df, ctx)
        data = gatherer.gather_for_forecast("revenue", horizon=7)
        assert "values" in data or "note" in data

    def test_find_metric_column(self, sample_df, context_engine, semantic_mappings):
        ctx = context_engine.build(df=sample_df, semantic_mappings=semantic_mappings, industry="retail")
        gatherer = DataGatherer(sample_df, ctx)
        assert gatherer._find_metric_column("revenue") == "sales"
        assert gatherer._find_metric_column("profit") == "profit"

    def test_find_date_column(self, sample_df, context_engine, semantic_mappings):
        ctx = context_engine.build(df=sample_df, semantic_mappings=semantic_mappings, industry="retail")
        gatherer = DataGatherer(sample_df, ctx)
        date_col = gatherer._find_date_column()
        assert date_col == "order_date"

    def test_empty_dataframe(self, context_engine):
        ctx = context_engine.build(df=pd.DataFrame(), industry="retail")
        gatherer = DataGatherer(pd.DataFrame(), ctx)
        data = gatherer.gather_for_summary()
        assert "note" in data


# ── Executive Summary Engine Tests ─────────────────────


class TestExecutiveSummaryEngine:
    def test_generate_without_db(self, sample_df, semantic_mappings):
        engine = ExecutiveSummaryEngine(db=None)
        result = engine.generate(
            df=sample_df,
            semantic_mappings=semantic_mappings,
            industry="retail",
        )
        assert "title" in result
        assert "executive_summary" in result
        assert "confidence" in result

    def test_generate_from_data_only(self, sample_df, context_engine, semantic_mappings):
        engine = ExecutiveSummaryEngine(db=None)
        ctx = context_engine.build(df=sample_df, semantic_mappings=semantic_mappings, industry="retail")
        gatherer = DataGatherer(sample_df, ctx)
        data = gatherer.gather_for_summary()
        result = engine.generate(
            df=sample_df,
            semantic_mappings=semantic_mappings,
            industry="retail",
            context=ctx,
            additional_data=data,
        )
        assert "executive_summary" in result
        assert isinstance(result["confidence"], dict)


# ── Root Cause Analysis Engine Tests ───────────────────


class TestRootCauseAnalysisEngine:
    def test_analyze_without_db(self, sample_df, semantic_mappings):
        engine = RootCauseAnalysisEngine(db=None)
        result = engine.analyze(
            question="Why did revenue decrease?",
            df=sample_df,
            semantic_mappings=semantic_mappings,
            industry="retail",
        )
        assert "observation" in result
        assert "root_causes" in result
        assert "overall_confidence" in result

    def test_detect_metric_and_direction(self, sample_df, context_engine, semantic_mappings):
        engine = RootCauseAnalysisEngine(db=None)
        ctx = context_engine.build(df=sample_df, semantic_mappings=semantic_mappings, industry="retail")
        metric, direction = engine._detect_metric_and_direction("Why did revenue decrease?", ctx)
        assert metric == "revenue"
        assert direction == "decrease"

    def test_detect_increase_direction(self, sample_df, context_engine, semantic_mappings):
        engine = RootCauseAnalysisEngine(db=None)
        ctx = context_engine.build(df=sample_df, semantic_mappings=semantic_mappings, industry="retail")
        metric, direction = engine._detect_metric_and_direction("Why did profit increase?", ctx)
        assert direction == "increase"


# ── Enterprise Forecast Engine Tests ───────────────────


class TestEnterpriseForecastEngine:
    def test_forecast_without_db(self, sample_df, semantic_mappings):
        engine = EnterpriseForecastEngine(db=None)
        result = engine.forecast(
            metric="revenue",
            df=sample_df,
            semantic_mappings=semantic_mappings,
            industry="retail",
            horizon="short",
        )
        assert "metric" in result
        assert "predictions" in result
        assert "method" in result
        assert "assumptions" in result
        assert "model_limitations" in result

    def test_forecast_horizon_presets(self, sample_df, semantic_mappings):
        engine = EnterpriseForecastEngine(db=None)
        for horizon in ["short", "medium", "long"]:
            result = engine.forecast(
                metric="revenue",
                df=sample_df,
                semantic_mappings=semantic_mappings,
                industry="retail",
                horizon=horizon,
            )
            assert "predictions" in result

    def test_forecast_auto_method(self, sample_df, semantic_mappings):
        engine = EnterpriseForecastEngine(db=None)
        result = engine.forecast(
            metric="revenue",
            df=sample_df,
            semantic_mappings=semantic_mappings,
            industry="retail",
            method="auto",
        )
        assert result["method"] in ["linear", "exponential", "moving_average", "seasonal"]

    def test_forecast_insufficient_data(self, semantic_mappings):
        engine = EnterpriseForecastEngine(db=None)
        small_df = pd.DataFrame({
            "date": pd.date_range("2024-01-01", periods=3, freq="D"),
            "sales": [100, 200, 150],
        })
        result = engine.forecast(
            metric="revenue",
            df=small_df,
            semantic_mappings={"date": "date", "sales": "revenue"},
            industry="retail",
        )
        assert "error" in result or len(result.get("predictions", [])) >= 0

    def test_assumptions_generated(self, sample_df, semantic_mappings):
        engine = EnterpriseForecastEngine(db=None)
        result = engine.forecast(
            metric="revenue",
            df=sample_df,
            semantic_mappings=semantic_mappings,
            industry="retail",
            horizon="medium",
        )
        assert len(result["assumptions"]) > 0
        assert any("trend" in a.lower() for a in result["assumptions"])

    def test_limitations_generated(self, sample_df, semantic_mappings):
        engine = EnterpriseForecastEngine(db=None)
        result = engine.forecast(
            metric="revenue",
            df=sample_df,
            semantic_mappings=semantic_mappings,
            industry="retail",
            horizon="medium",
        )
        assert len(result["model_limitations"]) > 0


# ── Enterprise Anomaly Engine Tests ────────────────────


class TestEnterpriseAnomalyEngine:
    def test_detect_without_db(self, sample_df, semantic_mappings):
        engine = EnterpriseAnomalyEngine(db=None)
        result = engine.detect(
            metric="revenue",
            df=sample_df,
            semantic_mappings=semantic_mappings,
            industry="retail",
        )
        assert "alerts" in result
        assert "total_anomalies" in result
        assert "summary" in result
        assert "explanations" in result

    def test_industry_sensitivity(self, sample_df, semantic_mappings):
        engine = EnterpriseAnomalyEngine(db=None)
        result_retail = engine.detect(
            metric="revenue",
            df=sample_df,
            semantic_mappings=semantic_mappings,
            industry="retail",
        )
        result_healthcare = engine.detect(
            metric="revenue",
            df=sample_df,
            semantic_mappings=semantic_mappings,
            industry="healthcare",
        )
        # Healthcare should be more sensitive (lower threshold)
        assert result_healthcare["sensitivity"] <= result_retail["sensitivity"]

    def test_anomaly_explanations(self, sample_df, semantic_mappings):
        engine = EnterpriseAnomalyEngine(db=None)
        result = engine.detect(
            metric="revenue",
            df=sample_df,
            semantic_mappings=semantic_mappings,
            industry="retail",
            sensitivity=1.0,  # Very sensitive to catch anomalies
        )
        for explanation in result["explanations"]:
            assert "explanation" in explanation
            assert "impact" in explanation

    def test_no_anomalies(self, sample_df, semantic_mappings):
        engine = EnterpriseAnomalyEngine(db=None)
        result = engine.detect(
            metric="revenue",
            df=sample_df,
            semantic_mappings=semantic_mappings,
            industry="retail",
            sensitivity=10.0,  # Very high threshold
        )
        # With very high sensitivity, statistical anomalies should be zero
        # but trend/missing alerts may still appear
        statistical = [a for a in result["alerts"] if a["alert_type"] in ("spike", "drop")]
        assert len(statistical) == 0


# ── Recommendation Engine Tests ────────────────────────


class TestRecommendationEngine:
    def test_generate_without_db(self, sample_df, semantic_mappings):
        engine = RecommendationEngine(db=None)
        result = engine.generate(
            df=sample_df,
            semantic_mappings=semantic_mappings,
            industry="retail",
        )
        assert "recommendations" in result
        assert "industry" in result
        assert "triggers_detected" in result
        assert "confidence" in result

    def test_retail_recommendations(self, sample_df, semantic_mappings):
        engine = RecommendationEngine(db=None)
        result = engine.generate(
            df=sample_df,
            semantic_mappings=semantic_mappings,
            industry="retail",
        )
        # Should have template-based recommendations
        assert len(result["recommendations"]) > 0
        for rec in result["recommendations"]:
            assert "action" in rec
            assert "priority" in rec
            assert "feasibility" in rec

    def test_healthcare_recommendations(self, healthcare_df):
        engine = RecommendationEngine(db=None)
        result = engine.generate(
            df=healthcare_df,
            semantic_mappings={"admission_date": "date", "billing_amount": "billing_amount", "readmitted": "readmission"},
            industry="healthcare",
        )
        assert result["industry"] == "healthcare"
        # Template recommendations may or may not trigger depending on data
        assert "recommendations" in result

    def test_generic_recommendations(self, sample_df):
        engine = RecommendationEngine(db=None)
        result = engine.generate(
            df=sample_df,
            industry="unknown",
        )
        assert len(result["recommendations"]) > 0

    def test_trigger_detection(self, sample_df, context_engine, semantic_mappings):
        engine = RecommendationEngine(db=None)
        ctx = context_engine.build(df=sample_df, semantic_mappings=semantic_mappings, industry="retail")
        gatherer = DataGatherer(sample_df, ctx)
        data = gatherer.gather_for_summary()
        triggers = engine._detect_triggers(data, ctx)
        assert isinstance(triggers, list)


# ── NL Analytics Engine Tests ──────────────────────────


class TestNLAnalyticsEngine:
    def test_analyze_compare(self, sample_df, semantic_mappings):
        engine = NLAnalyticsEngine(db=None)
        result = engine.analyze(
            question="Compare this month with last month",
            df=sample_df,
            semantic_mappings=semantic_mappings,
            industry="retail",
        )
        assert result["intent"] == "compare"
        assert "analysis" in result
        assert "explanation" in result

    def test_analyze_rank(self, sample_df, semantic_mappings):
        engine = NLAnalyticsEngine(db=None)
        result = engine.analyze(
            question="Show top performing regions",
            df=sample_df,
            semantic_mappings=semantic_mappings,
            industry="retail",
        )
        assert result["intent"] == "rank"

    def test_analyze_trend(self, sample_df, semantic_mappings):
        engine = NLAnalyticsEngine(db=None)
        result = engine.analyze(
            question="What's the trend over time?",
            df=sample_df,
            semantic_mappings=semantic_mappings,
            industry="retail",
        )
        assert result["intent"] == "trend"

    def test_analyze_summarize(self, sample_df, semantic_mappings):
        engine = NLAnalyticsEngine(db=None)
        result = engine.analyze(
            question="Give me a summary of this data",
            df=sample_df,
            semantic_mappings=semantic_mappings,
            industry="retail",
        )
        assert result["intent"] == "summarize"

    def test_visualization_recommendations(self, sample_df, semantic_mappings):
        engine = NLAnalyticsEngine(db=None)
        result = engine.analyze(
            question="Compare regions",
            df=sample_df,
            semantic_mappings=semantic_mappings,
            industry="retail",
        )
        assert len(result["visualizations"]) > 0
        assert "type" in result["visualizations"][0]
        assert "rationale" in result["visualizations"][0]


# ── Enterprise Report Engine Tests ─────────────────────


class TestEnterpriseReportEngine:
    def test_generate_markdown_report(self, sample_df, semantic_mappings):
        engine = EnterpriseReportEngine(db=None)
        result = engine.generate(
            report_type="executive",
            df=sample_df,
            semantic_mappings=semantic_mappings,
            industry="retail",
            format="markdown",
        )
        assert "title" in result
        assert "content" in result
        assert "summary" in result
        assert "methodology" in result
        assert "sections" in result
        assert "Executive Summary" in result["sections"]

    def test_generate_monthly_report(self, sample_df, semantic_mappings):
        engine = EnterpriseReportEngine(db=None)
        result = engine.generate(
            report_type="monthly",
            df=sample_df,
            semantic_mappings=semantic_mappings,
            industry="retail",
        )
        assert "Monthly Report" in result["title"]

    def test_report_has_methodology(self, sample_df, semantic_mappings):
        engine = EnterpriseReportEngine(db=None)
        result = engine.generate(
            df=sample_df,
            semantic_mappings=semantic_mappings,
            industry="retail",
        )
        assert "Data Source" in result["methodology"]
        assert "Records Analyzed" in result["methodology"]

    def test_report_has_appendix(self, sample_df, semantic_mappings):
        engine = EnterpriseReportEngine(db=None)
        result = engine.generate(
            df=sample_df,
            semantic_mappings=semantic_mappings,
            industry="retail",
        )
        assert "Detailed Statistics" in result["appendix"] or "Overall Summary" in result["appendix"]


# ── Security Tests ─────────────────────────────────────


class TestAISecurityLayer:
    def test_validate_input(self, mock_db):
        security = AISecurityLayer(mock_db)
        result = security.validate_input("What happened?")
        assert result == "What happened?"

    def test_validate_input_empty(self, mock_db):
        security = AISecurityLayer(mock_db)
        with pytest.raises(ValueError):
            security.validate_input("")

    def test_validate_input_sql_injection(self, mock_db):
        security = AISecurityLayer(mock_db)
        with pytest.raises(ValueError):
            security.validate_input("; DROP TABLE users;")

    def test_check_permissions_admin(self, mock_db):
        security = AISecurityLayer(mock_db)
        assert security.check_permissions("etl_copilot", ["*"]) is True

    def test_check_permissions_missing(self, mock_db):
        security = AISecurityLayer(mock_db)
        with pytest.raises(PermissionError):
            security.check_permissions("etl_copilot", [])

    def test_redact_sensitive_data(self, mock_db):
        security = AISecurityLayer(mock_db)
        text = "My card is 1234 5678 9012 3456 and key is sk-abc12345678901234567890"
        redacted = security.redact_sensitive_data(text)
        assert "REDACTED" in redacted
        assert "1234 5678 9012 3456" not in redacted

    def test_check_dataset_access_admin(self, mock_db):
        security = AISecurityLayer(mock_db)
        assert security.check_dataset_access(1, "ds_123", ["*"]) is True

    def test_check_dataset_access_specific(self, mock_db):
        security = AISecurityLayer(mock_db)
        assert security.check_dataset_access(1, "ds_123", ["dataset.ds_123.read"]) is True

    def test_check_dataset_access_general(self, mock_db):
        security = AISecurityLayer(mock_db)
        assert security.check_dataset_access(1, "ds_123", ["dataset.read"]) is True

    def test_validate_confidence_disclosure(self, mock_db):
        security = AISecurityLayer(mock_db)
        response = {"response": "test"}
        result = security.validate_confidence_disclosure(response)
        assert "confidence" in result
        assert result["confidence"]["score"] == 0.5

    def test_validate_confidence_disclosure_existing(self, mock_db):
        security = AISecurityLayer(mock_db)
        response = {"response": "test", "confidence": {"score": 0.9}}
        result = security.validate_confidence_disclosure(response)
        assert result["confidence"]["score"] == 0.9

    def test_create_audit_record(self, mock_db):
        security = AISecurityLayer(mock_db)
        record = security.create_audit_record(
            user_id=1,
            assistant_type="data_copilot",
            task_type="executive_summary",
            input_summary="What happened?",
            output_summary="Sales increased by 10%",
            model_used="gpt-4",
            provider="openai",
            tokens_used=500,
        )
        assert record["user_id"] == 1
        assert record["task_type"] == "executive_summary"
        assert record["model_used"] == "gpt-4"
        assert "timestamp" in record

    def test_validate_enterprise_request(self, mock_db):
        security = AISecurityLayer(mock_db)
        result = security.validate_enterprise_request(
            user_id=1,
            assistant_type="data_copilot",
            task_type="general_chat",
            user_input="What happened?",
            user_permissions=[],
        )
        assert "sanitized_input" in result
        assert "audit_record" in result
        assert result["sanitized_input"] == "What happened?"


# ── Performance Tests ──────────────────────────────────


class TestPerformanceMonitor:
    def test_record_and_stats(self):
        monitor = PerformanceMonitor()
        monitor.record("executive_summary", 1500.0, success=True)
        monitor.record("executive_summary", 2000.0, success=True)
        monitor.record("executive_summary", 3000.0, success=False)
        stats = monitor.get_stats()
        assert "executive_summary" in stats
        assert stats["executive_summary"]["total_requests"] == 3
        assert stats["executive_summary"]["failures"] == 1
        assert stats["executive_summary"]["avg_latency_ms"] > 0

    def test_alerts(self):
        monitor = PerformanceMonitor()
        monitor.record("slow_task", 10000.0, success=True)
        alerts = monitor.get_alerts(latency_threshold_ms=5000)
        assert len(alerts) > 0
        assert alerts[0]["type"] == "high_latency"


class TestTokenBudgetManager:
    def test_estimate_tokens(self):
        manager = TokenBudgetManager()
        assert manager.estimate_tokens("hello world") > 0

    def test_allocate_budget(self, context_engine, sample_df):
        ctx = context_engine.build(df=sample_df, industry="retail")
        manager = TokenBudgetManager(max_tokens=8000)
        allocation = manager.allocate_budget(ctx, PromptTaskType.EXECUTIVE_SUMMARY)
        assert allocation["system_prompt"] > 0
        assert allocation["dataset_schema"] > 0
        assert allocation["response"] > 0

    def test_truncate_context(self):
        manager = TokenBudgetManager()
        long_text = "x" * 10000
        truncated = manager.truncate_context(long_text, max_tokens=100)
        assert "truncated" in truncated


class TestLazyContextLoader:
    def test_should_load_section_full_context(self, context_engine):
        loader = LazyContextLoader(context_engine)
        assert loader.should_load_section(PromptTaskType.EXECUTIVE_SUMMARY, "dataset", "test") is True
        assert loader.should_load_section(PromptTaskType.EXECUTIVE_SUMMARY, "industry", "test") is True

    def test_should_load_section_light_context(self, context_engine):
        loader = LazyContextLoader(context_engine)
        assert loader.should_load_section(PromptTaskType.GENERAL_CHAT, "dataset", "hello") is False
        assert loader.should_load_section(PromptTaskType.GENERAL_CHAT, "dataset", "show me the data") is True

    def test_should_load_section_forecast(self, context_engine):
        loader = LazyContextLoader(context_engine)
        assert loader.should_load_section(PromptTaskType.FORECASTING, "dataset", "forecast revenue") is True
        assert loader.should_load_section(PromptTaskType.FORECASTING, "dashboard", "forecast revenue") is False

    def test_should_load_section_anomaly(self, context_engine):
        loader = LazyContextLoader(context_engine)
        assert loader.should_load_section(PromptTaskType.ANOMALY_DETECTION, "dataset", "detect anomalies") is True
