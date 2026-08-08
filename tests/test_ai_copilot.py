"""Tests for the AI Data Analyst Copilot.

Tests cover:
  - Natural language query parsing (intent detection, metric/dimension extraction)
  - Root cause analysis (metric change decomposition)
  - Automated insight generation (anomalies, trends, correlations, dominance)
  - Report generation (structured narrative reports)
  - Full copilot conversational interface
  - Pipeline integration
"""

from __future__ import annotations

import pandas as pd
import pytest

from ai_copilot import DataAnalystCopilot
from ai_copilot.insight_generator import AutoInsight, InsightGenerator, InsightType
from ai_copilot.query_engine import QueryEngine, QueryIntent
from ai_copilot.report_generator import Report, ReportGenerator
from ai_copilot.root_cause import RootCauseAnalyzer, RootCauseResult

# ── Fixtures ──────────────────────────────────────────────


@pytest.fixture
def retail_df():
    """Retail dataset with a sales decline in the second half."""
    dates = pd.date_range("2024-01-01", periods=60, freq="D")
    return pd.DataFrame(
        {
            "order_id": range(1, 61),
            "customer_id": [f"C{i % 10}" for i in range(60)],
            "product": ["Product_A"] * 30 + ["Product_B"] * 20 + ["Product_C"] * 10,
            "region": (["North"] * 20 + ["South"] * 20 + ["East"] * 10 + ["West"] * 10),
            "sales": [1000 - i * 10 for i in range(30)]
            + [500 - i * 5 for i in range(20)]
            + [300] * 10,
            "profit": [200 - i * 2 for i in range(30)] + [100 - i for i in range(20)] + [60] * 10,
            "order_date": dates,
        }
    )


@pytest.fixture
def retail_col_mapping():
    return {
        "order_id": "order",
        "customer_id": "customer",
        "product": "product",
        "region": "region",
        "sales": "revenue",
        "profit": "profit",
        "order_date": "date",
    }


@pytest.fixture
def healthcare_df():
    dates = pd.date_range("2024-01-01", periods=40, freq="D")
    return pd.DataFrame(
        {
            "patient_id": [f"P{i % 15}" for i in range(40)],
            "doctor_name": [f"Dr.{i % 4}" for i in range(40)],
            "department": (["Cardiology"] * 20 + ["Neurology"] * 20),
            "diagnosis_code": ["A00", "B01", "C50"] * 13 + ["A00"],
            "billing_amount": [2000 - i * 20 for i in range(40)],
            "visit_date": dates,
            "gender": ["M", "F"] * 20,
        }
    )


@pytest.fixture
def healthcare_col_mapping():
    return {
        "patient_id": "patient",
        "doctor_name": "doctor",
        "department": "ward",
        "diagnosis_code": "diagnosis",
        "billing_amount": "billing",
        "visit_date": "date",
        "gender": "gender",
    }


@pytest.fixture
def simple_df():
    return pd.DataFrame(
        {
            "category": ["A", "B", "C", "A", "B", "C"] * 5,
            "value": [10, 20, 30, 15, 25, 35] * 5,
            "date": pd.date_range("2024-01-01", periods=30, freq="D"),
        }
    )


# ── Query Engine Tests ────────────────────────────────────


class TestQueryEngine:
    def test_why_change_intent(self):
        q = QueryEngine.parse("Why did sales drop?")
        assert q.intent == QueryIntent.WHY_CHANGE
        assert q.direction == "decrease"
        assert q.metric == "revenue"

    def test_why_change_increase(self):
        q = QueryEngine.parse("Why did revenue increase?")
        assert q.intent == QueryIntent.WHY_CHANGE
        assert q.direction == "increase"
        assert q.metric == "revenue"

    def test_why_change_billing(self):
        q = QueryEngine.parse("Why did billing decline?")
        assert q.intent == QueryIntent.WHY_CHANGE
        assert q.direction == "decrease"
        assert q.metric == "revenue"  # billing is a synonym for revenue

    def test_top_n_intent(self):
        q = QueryEngine.parse("Top 5 products by sales")
        assert q.intent == QueryIntent.TOP_N
        assert q.top_n == 5

    def test_top_n_default(self):
        q = QueryEngine.parse("Best performing regions")
        assert q.intent == QueryIntent.TOP_N
        assert q.top_n == 5  # default

    def test_top_n_custom(self):
        q = QueryEngine.parse("Top 10 products")
        assert q.intent == QueryIntent.TOP_N
        assert q.top_n == 10

    def test_summary_intent(self):
        q = QueryEngine.parse("Give me a summary")
        assert q.intent == QueryIntent.SUMMARY

    def test_trend_intent(self):
        q = QueryEngine.parse("What's the trend in billing?")
        assert q.intent == QueryIntent.TREND

    def test_comparison_intent(self):
        q = QueryEngine.parse("Compare regions")
        assert q.intent == QueryIntent.COMPARISON
        assert q.dimension == "region"

    def test_breakdown_intent(self):
        q = QueryEngine.parse("Break down sales by category")
        assert q.intent == QueryIntent.BREAKDOWN

    def test_anomaly_intent(self):
        q = QueryEngine.parse("Any anomalies in the data?")
        assert q.intent == QueryIntent.ANOMALY

    def test_correlation_intent(self):
        q = QueryEngine.parse("Correlation between sales and profit")
        assert q.intent == QueryIntent.CORRELATION

    def test_unknown_intent(self):
        q = QueryEngine.parse("asdf jkl random text")
        assert q.intent == QueryIntent.UNKNOWN

    def test_metric_extraction_with_col_mapping(self, retail_col_mapping):
        q = QueryEngine.parse("Why did sales drop?", retail_col_mapping)
        assert q.metric == "revenue"

    def test_dimension_extraction_with_col_mapping(self, retail_col_mapping):
        q = QueryEngine.parse("Compare regions", retail_col_mapping)
        assert q.dimension == "region"

    def test_parsed_query_to_dict(self):
        q = QueryEngine.parse("Top 5 products by sales")
        d = q.to_dict()
        assert d["intent"] == "top_n"
        assert d["top_n"] == 5


# ── Root Cause Analyzer Tests ─────────────────────────────


class TestRootCauseAnalyzer:
    def test_analyze_returns_result(self, retail_df):
        result = RootCauseAnalyzer.analyze(
            retail_df,
            "sales",
            "order_date",
            dimension_cols=["product", "region"],
            metric_label="Sales",
        )
        assert result is not None
        assert isinstance(result, RootCauseResult)

    def test_detects_decline(self, retail_df):
        result = RootCauseAnalyzer.analyze(
            retail_df,
            "sales",
            "order_date",
            dimension_cols=["product", "region"],
        )
        assert result.direction == "decrease"
        assert result.total_change < 0
        assert result.total_change_pct < 0

    def test_contributions_sorted(self, retail_df):
        result = RootCauseAnalyzer.analyze(
            retail_df,
            "sales",
            "order_date",
            dimension_cols=["product", "region"],
        )
        assert len(result.contributions) > 0
        # Check sorted by absolute change
        changes = [abs(c.change) for c in result.contributions]
        assert changes == sorted(changes, reverse=True)

    def test_contribution_has_dimension(self, retail_df):
        result = RootCauseAnalyzer.analyze(
            retail_df,
            "sales",
            "order_date",
            dimension_cols=["product", "region"],
        )
        dims = {c.dimension for c in result.contributions}
        assert "product" in dims or "region" in dims

    def test_recommendations_generated(self, retail_df):
        result = RootCauseAnalyzer.analyze(
            retail_df,
            "sales",
            "order_date",
            dimension_cols=["product", "region"],
        )
        assert len(result.recommendations) > 0

    def test_summary_generated(self, retail_df):
        result = RootCauseAnalyzer.analyze(
            retail_df,
            "sales",
            "order_date",
            dimension_cols=["product", "region"],
            metric_label="Sales",
        )
        assert "Sales" in result.summary
        assert "Main reasons" in result.summary

    def test_to_dict(self, retail_df):
        result = RootCauseAnalyzer.analyze(
            retail_df,
            "sales",
            "order_date",
            dimension_cols=["product"],
        )
        d = result.to_dict()
        assert d["metric"] == "sales"
        assert isinstance(d["contributions"], list)

    def test_insufficient_data_returns_none(self):
        df = pd.DataFrame({"v": [1, 2], "d": pd.date_range("2024-01-01", periods=2)})
        result = RootCauseAnalyzer.analyze(df, "v", "d")
        assert result is None

    def test_no_date_column_returns_none(self, retail_df):
        result = RootCauseAnalyzer.analyze(
            retail_df,
            "sales",
            "nonexistent_col",
        )
        assert result is None


# ── Insight Generator Tests ───────────────────────────────


class TestInsightGenerator:
    def test_generates_insights(self, retail_df):
        insights = InsightGenerator.generate(retail_df)
        assert len(insights) > 0
        assert all(isinstance(i, AutoInsight) for i in insights)

    def test_max_insights_limit(self, retail_df):
        insights = InsightGenerator.generate(retail_df, max_insights=3)
        assert len(insights) <= 3

    def test_detects_trend(self, retail_df):
        insights = InsightGenerator.generate(retail_df)
        trend_insights = [i for i in insights if i.type == InsightType.TREND]
        assert len(trend_insights) > 0

    def test_detects_correlation(self, retail_df):
        insights = InsightGenerator.generate(retail_df)
        corr_insights = [i for i in insights if i.type == InsightType.CORRELATION]
        assert len(corr_insights) > 0

    def test_detects_dominance(self):
        df = pd.DataFrame(
            {
                "category": ["A"] * 70 + ["B"] * 20 + ["C"] * 10,
                "value": range(100),
            }
        )
        insights = InsightGenerator.generate(df)
        dom_insights = [i for i in insights if i.type == InsightType.DOMINANCE]
        assert len(dom_insights) > 0

    def test_detects_quality_issues(self):
        df = pd.DataFrame(
            {
                "a": [1, 2, None, None, None, None, None, None, None, None] * 3,
                "b": range(30),
            }
        )
        insights = InsightGenerator.generate(df)
        quality_insights = [i for i in insights if i.type == InsightType.QUALITY]
        assert len(quality_insights) > 0

    def test_insight_to_dict(self, retail_df):
        insights = InsightGenerator.generate(retail_df)
        d = insights[0].to_dict()
        assert "type" in d
        assert "severity" in d
        assert "title" in d
        assert "description" in d

    def test_severity_ordering(self, retail_df):
        insights = InsightGenerator.generate(retail_df)
        severity_order = {"critical": 0, "warning": 1, "positive": 2, "info": 3}
        for i in range(len(insights) - 1):
            s1 = severity_order.get(insights[i].severity.value, 99)
            s2 = severity_order.get(insights[i + 1].severity.value, 99)
            assert s1 <= s2


# ── Report Generator Tests ────────────────────────────────


class TestReportGenerator:
    def test_generates_report(self, retail_df):
        report = ReportGenerator.generate(retail_df)
        assert isinstance(report, Report)
        assert len(report.sections) > 0

    def test_report_has_title(self, retail_df):
        report = ReportGenerator.generate(retail_df, title="Custom Report")
        assert report.title == "Custom Report"

    def test_report_has_summary(self, retail_df):
        report = ReportGenerator.generate(retail_df)
        assert report.summary != ""

    def test_report_to_markdown(self, retail_df):
        report = ReportGenerator.generate(retail_df)
        md = report.to_markdown()
        assert isinstance(md, str)
        assert report.title in md
        assert "##" in md  # Has sections

    def test_report_to_dict(self, retail_df):
        report = ReportGenerator.generate(retail_df)
        d = report.to_dict()
        assert "title" in d
        assert "sections" in d
        assert isinstance(d["sections"], list)

    def test_report_with_insights(self, retail_df):
        insights = InsightGenerator.generate(retail_df)
        report = ReportGenerator.generate(retail_df, insights=insights)
        insight_sections = [s for s in report.sections if "Insight" in s.title]
        assert len(insight_sections) > 0

    def test_report_overview_section(self, retail_df):
        report = ReportGenerator.generate(retail_df)
        overview = [s for s in report.sections if "Overview" in s.title]
        assert len(overview) > 0


# ── DataAnalystCopilot Tests ──────────────────────────────


class TestDataAnalystCopilot:
    def test_init(self, retail_df, retail_col_mapping):
        copilot = DataAnalystCopilot(retail_df)
        assert copilot.df is retail_df

    def test_ask_why_change(self, retail_df):
        copilot = DataAnalystCopilot(retail_df)
        response = copilot.ask("Why did sales drop?")
        assert response.intent == "why_change"
        assert response.answer != ""
        assert len(response.follow_ups) > 0

    def test_ask_top_n(self, retail_df):
        copilot = DataAnalystCopilot(retail_df)
        response = copilot.ask("Top 5 products by sales")
        assert response.intent == "top_n"
        assert "Product" in response.answer or "product" in response.answer

    def test_ask_summary(self, retail_df):
        copilot = DataAnalystCopilot(retail_df)
        response = copilot.ask("Give me a summary")
        assert response.intent == "summary"
        assert "Records" in response.answer or "records" in response.answer

    def test_ask_trend(self, retail_df):
        copilot = DataAnalystCopilot(retail_df)
        response = copilot.ask("What's the trend in sales?")
        assert response.intent == "trend"
        assert response.answer != ""

    def test_ask_comparison(self, retail_df):
        copilot = DataAnalystCopilot(retail_df)
        response = copilot.ask("Compare regions")
        assert response.intent == "comparison"
        assert response.answer != ""

    def test_ask_anomaly(self, retail_df):
        copilot = DataAnalystCopilot(retail_df)
        response = copilot.ask("Any anomalies?")
        assert response.intent == "anomaly"
        assert response.answer != ""

    def test_ask_correlation(self, retail_df):
        copilot = DataAnalystCopilot(retail_df)
        response = copilot.ask("Correlation between sales and profit")
        assert response.intent == "correlation"
        assert response.answer != ""

    def test_ask_unknown(self, retail_df):
        copilot = DataAnalystCopilot(retail_df)
        response = copilot.ask("asdf jkl random text")
        assert response.intent == "unknown"
        assert "help" in response.answer.lower() or "try" in response.answer.lower()

    def test_auto_insights(self, retail_df):
        copilot = DataAnalystCopilot(retail_df)
        insights = copilot.auto_insights()
        assert len(insights) > 0

    def test_generate_report(self, retail_df):
        copilot = DataAnalystCopilot(retail_df)
        report = copilot.generate_report()
        assert isinstance(report, Report)
        assert len(report.sections) > 0

    def test_response_to_dict(self, retail_df):
        copilot = DataAnalystCopilot(retail_df)
        response = copilot.ask("Give me a summary")
        d = response.to_dict()
        assert "question" in d
        assert "answer" in d
        assert "intent" in d

    def test_with_col_mapping(self, retail_df, retail_col_mapping):
        """Copilot should work better with column mapping."""
        copilot = DataAnalystCopilot(retail_df)
        copilot._col_mapping = retail_col_mapping
        response = copilot.ask("Why did sales drop?")
        assert response.intent == "why_change"
        assert response.data  # Should have structured data


# ── Healthcare Copilot Tests ──────────────────────────────


class TestHealthcareCopilot:
    def test_why_billing_dropped(self, healthcare_df):
        copilot = DataAnalystCopilot(healthcare_df)
        response = copilot.ask("Why did billing drop?")
        assert response.intent == "why_change"
        assert response.answer != ""

    def test_top_doctors(self, healthcare_df):
        copilot = DataAnalystCopilot(healthcare_df)
        response = copilot.ask("Top 5 doctors by billing")
        assert response.intent == "top_n"
        assert "Dr." in response.answer or "doctor" in response.answer.lower()

    def test_healthcare_summary(self, healthcare_df):
        copilot = DataAnalystCopilot(healthcare_df)
        response = copilot.ask("Give me a summary")
        assert response.intent == "summary"
        assert "40" in response.answer  # 40 records


# ── Pipeline Integration Tests ────────────────────────────


class TestPipelineIntegration:
    def test_get_copilot_from_mapping_result(self, healthcare_df):
        from semantic.mapping_engine import SemanticMappingEngine

        result = SemanticMappingEngine.analyze(healthcare_df, "hospital.csv")
        copilot = result.get_copilot(healthcare_df)
        assert copilot is not None
        assert isinstance(copilot, DataAnalystCopilot)

    def test_copilot_with_pipeline_result(self, healthcare_df):
        from semantic.mapping_engine import SemanticMappingEngine

        result = SemanticMappingEngine.analyze(healthcare_df, "hospital.csv")
        copilot = result.get_copilot(healthcare_df)
        response = copilot.ask("Give me a summary")
        assert response.intent == "summary"
        assert response.answer != ""

    def test_copilot_report_with_pipeline(self, healthcare_df):
        from semantic.mapping_engine import SemanticMappingEngine

        result = SemanticMappingEngine.analyze(healthcare_df, "hospital.csv")
        copilot = result.get_copilot(healthcare_df)
        report = copilot.generate_report()
        assert report.industry == "healthcare"
        assert len(report.sections) >= 3
