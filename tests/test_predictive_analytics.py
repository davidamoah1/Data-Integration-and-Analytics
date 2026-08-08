"""Tests for Predictive Analytics Engine.

Tests cover:
  - Time series forecasting (linear, exponential, moving average, seasonal, auto)
  - Regression prediction (R², feature importance, predictions)
  - Risk classification (rule-based, high/medium/low)
  - Industry modules (business, healthcare, education, agriculture)
  - Pipeline integration
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from predictive_analytics import (
    ForecastResult,
    PredictionResult,
    PredictiveAnalyticsRegistry,
    PredictiveIntelligenceResult,
    RegressionPredictor,
    RiskAssessment,
    RiskClassifier,
    TimeSeriesForecaster,
)

# ── Fixtures ──────────────────────────────────────────────


@pytest.fixture
def retail_df():
    """Retail data with sales trend over time."""
    np.random.seed(42)
    dates = pd.date_range("2024-01-01", periods=60, freq="D")
    sales = [1000 + i * 20 + np.random.randint(-50, 50) for i in range(60)]
    profit = [s * 0.2 + np.random.randint(-10, 10) for s in sales]
    return pd.DataFrame(
        {
            "order_id": range(1, 61),
            "product": ["Product_A"] * 30 + ["Product_B"] * 30,
            "region": ["North"] * 20 + ["South"] * 40,
            "sales": sales,
            "profit": profit,
            "quantity": [10 + i for i in range(60)],
            "order_date": dates,
        }
    )


@pytest.fixture
def retail_col_mapping():
    return {
        "order_id": "order",
        "product": "product",
        "region": "region",
        "sales": "revenue",
        "profit": "profit",
        "quantity": "quantity",
        "order_date": "date",
    }


@pytest.fixture
def healthcare_df():
    """Healthcare data with admissions and patient info."""
    np.random.seed(42)
    dates = pd.date_range("2024-01-01", periods=60, freq="D")
    return pd.DataFrame(
        {
            "patient_id": [f"P{i % 20}" for i in range(60)],
            "department": (["Cardiology"] * 30 + ["Neurology"] * 30),
            "age": [30 + i % 50 for i in range(60)],
            "billing_amount": [2000 + i * 50 for i in range(60)],
            "diagnosis_code": ["E11.9", "J45.909", "I10.0"] * 20,
            "visit_date": dates,
        }
    )


@pytest.fixture
def healthcare_col_mapping():
    return {
        "patient_id": "patient",
        "department": "ward",
        "age": "age",
        "billing_amount": "billing",
        "diagnosis_code": "diagnosis",
        "visit_date": "date",
    }


@pytest.fixture
def education_df():
    """Education data with student grades and attendance."""
    np.random.seed(42)
    return pd.DataFrame(
        {
            "student_id": [f"S{i}" for i in range(1, 51)],
            "grade": [40 + i * 1.2 for i in range(50)],
            "attendance_rate": [60 + i * 0.8 for i in range(50)],
            "days_absent": [20 - i * 0.3 for i in range(50)],
            "participation_score": [30 + i * 1.4 for i in range(50)],
            "enrollment_date": pd.date_range("2024-01-01", periods=50, freq="D"),
        }
    )


@pytest.fixture
def education_col_mapping():
    return {
        "student_id": "student",
        "grade": "grade",
        "attendance_rate": "attendance",
        "days_absent": "absent",
        "participation_score": "participation",
        "enrollment_date": "date",
    }


@pytest.fixture
def agriculture_df():
    """Agriculture data with yield and environmental factors."""
    np.random.seed(42)
    return pd.DataFrame(
        {
            "farm_id": [f"F{i}" for i in range(1, 31)],
            "crop": (["Maize"] * 10 + ["Rice"] * 10 + ["Wheat"] * 10),
            "yield_per_hectare": [3 + i * 0.15 for i in range(30)],
            "rainfall_mm": [800 + i * 10 for i in range(30)],
            "fertilizer_kg": [100 + i * 5 for i in range(30)],
            "temperature": [25 + i * 0.2 for i in range(30)],
            "area_hectares": [10 + i * 0.5 for i in range(30)],
            "harvest_date": pd.date_range("2024-01-01", periods=30, freq="D"),
        }
    )


@pytest.fixture
def agriculture_col_mapping():
    return {
        "farm_id": "farm",
        "crop": "crop",
        "yield_per_hectare": "yield",
        "rainfall_mm": "rainfall",
        "fertilizer_kg": "fertilizer",
        "temperature": "temperature",
        "area_hectares": "area",
        "harvest_date": "date",
    }


# ── Time Series Forecaster Tests ──────────────────────────


class TestTimeSeriesForecaster:
    def test_linear_forecast(self, retail_df):
        result = TimeSeriesForecaster.forecast(
            retail_df,
            "sales",
            "order_date",
            horizon=7,
            method="linear",
        )
        assert result is not None
        assert isinstance(result, ForecastResult)
        assert len(result.predictions) == 7
        assert result.method == "linear"

    def test_exponential_forecast(self, retail_df):
        result = TimeSeriesForecaster.forecast(
            retail_df,
            "sales",
            "order_date",
            horizon=7,
            method="exponential",
        )
        assert result is not None
        assert result.method == "exponential"
        assert len(result.predictions) == 7

    def test_moving_average_forecast(self, retail_df):
        result = TimeSeriesForecaster.forecast(
            retail_df,
            "sales",
            "order_date",
            horizon=7,
            method="moving_average",
        )
        assert result is not None
        assert result.method == "moving_average"

    def test_seasonal_forecast(self, retail_df):
        result = TimeSeriesForecaster.forecast(
            retail_df,
            "sales",
            "order_date",
            horizon=7,
            method="seasonal",
        )
        assert result is not None
        assert result.method == "seasonal"

    def test_auto_method_selects(self, retail_df):
        result = TimeSeriesForecaster.forecast(
            retail_df,
            "sales",
            "order_date",
            horizon=7,
            method="auto",
        )
        assert result is not None
        assert result.method in ("linear", "exponential", "moving_average", "seasonal")

    def test_predictions_have_ci(self, retail_df):
        result = TimeSeriesForecaster.forecast(
            retail_df,
            "sales",
            "order_date",
            horizon=7,
            method="linear",
        )
        for p in result.predictions:
            assert p.lower_ci <= p.value <= p.upper_ci

    def test_accuracy_in_range(self, retail_df):
        result = TimeSeriesForecaster.forecast(
            retail_df,
            "sales",
            "order_date",
            horizon=7,
            method="linear",
        )
        assert 0 <= result.accuracy <= 1

    def test_trend_detected(self, retail_df):
        result = TimeSeriesForecaster.forecast(
            retail_df,
            "sales",
            "order_date",
            horizon=7,
            method="linear",
        )
        assert result.trend in ("increasing", "decreasing", "stable")

    def test_summary_generated(self, retail_df):
        result = TimeSeriesForecaster.forecast(
            retail_df,
            "sales",
            "order_date",
            horizon=7,
        )
        assert result.summary != ""
        assert "Accuracy" in result.summary

    def test_to_dict(self, retail_df):
        result = TimeSeriesForecaster.forecast(
            retail_df,
            "sales",
            "order_date",
            horizon=7,
        )
        d = result.to_dict()
        assert "name" in d
        assert "predictions" in d
        assert "method" in d

    def test_insufficient_data_returns_none(self):
        df = pd.DataFrame({"v": [1, 2], "d": pd.date_range("2024-01-01", periods=2)})
        result = TimeSeriesForecaster.forecast(df, "v", "d", horizon=7)
        assert result is None

    def test_non_numeric_metric_returns_none(self):
        df = pd.DataFrame({"v": ["a", "b"] * 10, "d": pd.date_range("2024-01-01", periods=20)})
        result = TimeSeriesForecaster.forecast(df, "v", "d", horizon=7)
        assert result is None


# ── Regression Predictor Tests ────────────────────────────


class TestRegressionPredictor:
    def test_predict_returns_result(self, agriculture_df):
        result = RegressionPredictor.predict(
            agriculture_df,
            "yield_per_hectare",
            feature_cols=["rainfall_mm", "fertilizer_kg", "temperature"],
        )
        assert result is not None
        assert isinstance(result, PredictionResult)

    def test_r_squared_in_range(self, agriculture_df):
        result = RegressionPredictor.predict(
            agriculture_df,
            "yield_per_hectare",
            feature_cols=["rainfall_mm", "fertilizer_kg"],
        )
        assert 0 <= result.r_squared <= 1

    def test_feature_importance(self, agriculture_df):
        result = RegressionPredictor.predict(
            agriculture_df,
            "yield_per_hectare",
            feature_cols=["rainfall_mm", "fertilizer_kg", "temperature"],
        )
        assert len(result.feature_importance) == 3
        assert all(0 <= v <= 1 for v in result.feature_importance.values())

    def test_predictions_generated(self, agriculture_df):
        result = RegressionPredictor.predict(
            agriculture_df,
            "yield_per_hectare",
            feature_cols=["rainfall_mm", "fertilizer_kg"],
        )
        assert len(result.predictions) > 0
        for p in result.predictions:
            assert "actual" in p
            assert "predicted" in p
            assert "error" in p

    def test_summary_generated(self, agriculture_df):
        result = RegressionPredictor.predict(
            agriculture_df,
            "yield_per_hectare",
            feature_cols=["rainfall_mm", "fertilizer_kg"],
        )
        assert result.summary != ""
        assert "R²" in result.summary

    def test_to_dict(self, agriculture_df):
        result = RegressionPredictor.predict(
            agriculture_df,
            "yield_per_hectare",
            feature_cols=["rainfall_mm"],
        )
        d = result.to_dict()
        assert "r_squared" in d
        assert "feature_importance" in d

    def test_insufficient_data_returns_none(self):
        df = pd.DataFrame({"y": [1, 2], "x": [3, 4]})
        result = RegressionPredictor.predict(df, "y", feature_cols=["x"])
        assert result is None

    def test_auto_feature_selection(self, agriculture_df):
        result = RegressionPredictor.predict(
            agriculture_df,
            "yield_per_hectare",
        )
        assert result is not None
        assert len(result.feature_importance) > 0


# ── Risk Classifier Tests ─────────────────────────────────


class TestRiskClassifier:
    def test_classify_returns_result(self, education_df):
        result = RiskClassifier.classify(
            education_df,
            "student_id",
            risk_factors=[
                {
                    "column": "grade",
                    "condition": "below",
                    "threshold": 60,
                    "weight": 0.5,
                    "label": "Low grade",
                },
                {
                    "column": "attendance_rate",
                    "condition": "below",
                    "threshold": 80,
                    "weight": 0.5,
                    "label": "Low attendance",
                },
            ],
        )
        assert isinstance(result, RiskAssessment)

    def test_risk_counts(self, education_df):
        result = RiskClassifier.classify(
            education_df,
            "student_id",
            risk_factors=[
                {
                    "column": "grade",
                    "condition": "below",
                    "threshold": 60,
                    "weight": 0.5,
                    "label": "Low grade",
                },
                {
                    "column": "attendance_rate",
                    "condition": "below",
                    "threshold": 80,
                    "weight": 0.5,
                    "label": "Low attendance",
                },
            ],
        )
        assert result.high_risk_count + result.medium_risk_count + result.low_risk_count == len(
            education_df
        )

    def test_at_risk_items_sorted(self, education_df):
        result = RiskClassifier.classify(
            education_df,
            "student_id",
            risk_factors=[
                {
                    "column": "grade",
                    "condition": "below",
                    "threshold": 60,
                    "weight": 1.0,
                    "label": "Low grade",
                },
            ],
        )
        scores = [i["risk_score"] for i in result.at_risk_items]
        assert scores == sorted(scores, reverse=True)

    def test_risk_factors_listed(self, education_df):
        result = RiskClassifier.classify(
            education_df,
            "student_id",
            risk_factors=[
                {
                    "column": "grade",
                    "condition": "below",
                    "threshold": 60,
                    "weight": 0.5,
                    "label": "Low grade",
                },
                {
                    "column": "attendance_rate",
                    "condition": "below",
                    "threshold": 80,
                    "weight": 0.5,
                    "label": "Low attendance",
                },
            ],
        )
        assert "Low grade" in result.risk_factors
        assert "Low attendance" in result.risk_factors

    def test_summary_generated(self, education_df):
        result = RiskClassifier.classify(
            education_df,
            "student_id",
            risk_factors=[
                {
                    "column": "grade",
                    "condition": "below",
                    "threshold": 60,
                    "weight": 1.0,
                    "label": "Low grade",
                },
            ],
        )
        assert result.summary != ""
        assert "high-risk" in result.summary

    def test_to_dict(self, education_df):
        result = RiskClassifier.classify(
            education_df,
            "student_id",
            risk_factors=[
                {
                    "column": "grade",
                    "condition": "below",
                    "threshold": 60,
                    "weight": 1.0,
                    "label": "Low grade",
                },
            ],
        )
        d = result.to_dict()
        assert "high_risk_count" in d
        assert "at_risk_items" in d

    def test_triggered_factors_in_items(self, education_df):
        result = RiskClassifier.classify(
            education_df,
            "student_id",
            risk_factors=[
                {
                    "column": "grade",
                    "condition": "below",
                    "threshold": 60,
                    "weight": 1.0,
                    "label": "Low grade",
                },
            ],
        )
        for item in result.at_risk_items:
            if item["risk_score"] > 0:
                assert len(item["triggered_factors"]) > 0


# ── Business Predictive Analytics Tests ───────────────────


class TestBusinessPredictiveAnalytics:
    def test_analyze_returns_result(self, retail_df, retail_col_mapping):
        result = PredictiveAnalyticsRegistry.analyze("retail", retail_df, retail_col_mapping)
        assert isinstance(result, PredictiveIntelligenceResult)
        assert result.industry == "retail"

    def test_generates_forecasts(self, retail_df, retail_col_mapping):
        result = PredictiveAnalyticsRegistry.analyze("retail", retail_df, retail_col_mapping)
        assert len(result.forecasts) > 0

    def test_sales_forecast_present(self, retail_df, retail_col_mapping):
        result = PredictiveAnalyticsRegistry.analyze("retail", retail_df, retail_col_mapping)
        sales_forecasts = [f for f in result.forecasts if "Sales" in f.name]
        assert len(sales_forecasts) > 0

    def test_demand_prediction_present(self, retail_df, retail_col_mapping):
        result = PredictiveAnalyticsRegistry.analyze("retail", retail_df, retail_col_mapping)
        assert len(result.predictions) > 0

    def test_summary_generated(self, retail_df, retail_col_mapping):
        result = PredictiveAnalyticsRegistry.analyze("retail", retail_df, retail_col_mapping)
        assert result.summary != ""

    def test_to_dict(self, retail_df, retail_col_mapping):
        result = PredictiveAnalyticsRegistry.analyze("retail", retail_df, retail_col_mapping)
        d = result.to_dict()
        assert "forecasts" in d
        assert "predictions" in d


# ── Healthcare Predictive Analytics Tests ─────────────────


class TestHealthcarePredictiveAnalytics:
    def test_analyze_returns_result(self, healthcare_df, healthcare_col_mapping):
        result = PredictiveAnalyticsRegistry.analyze(
            "healthcare", healthcare_df, healthcare_col_mapping
        )
        assert isinstance(result, PredictiveIntelligenceResult)
        assert result.industry == "healthcare"

    def test_admission_forecast(self, healthcare_df, healthcare_col_mapping):
        result = PredictiveAnalyticsRegistry.analyze(
            "healthcare", healthcare_df, healthcare_col_mapping
        )
        assert len(result.forecasts) > 0

    def test_patient_risk_assessment(self, healthcare_df, healthcare_col_mapping):
        result = PredictiveAnalyticsRegistry.analyze(
            "healthcare", healthcare_df, healthcare_col_mapping
        )
        assert len(result.risk_assessments) > 0
        ra = result.risk_assessments[0]
        assert ra.high_risk_count + ra.medium_risk_count + ra.low_risk_count > 0

    def test_summary_generated(self, healthcare_df, healthcare_col_mapping):
        result = PredictiveAnalyticsRegistry.analyze(
            "healthcare", healthcare_df, healthcare_col_mapping
        )
        assert result.summary != ""


# ── Education Predictive Analytics Tests ──────────────────


class TestEducationPredictiveAnalytics:
    def test_analyze_returns_result(self, education_df, education_col_mapping):
        result = PredictiveAnalyticsRegistry.analyze(
            "education", education_df, education_col_mapping
        )
        assert isinstance(result, PredictiveIntelligenceResult)
        assert result.industry == "education"

    def test_student_risk_prediction(self, education_df, education_col_mapping):
        result = PredictiveAnalyticsRegistry.analyze(
            "education", education_df, education_col_mapping
        )
        assert len(result.risk_assessments) > 0
        ra = result.risk_assessments[0]
        assert "Student Risk" in ra.name

    def test_at_risk_students_identified(self, education_df, education_col_mapping):
        result = PredictiveAnalyticsRegistry.analyze(
            "education", education_df, education_col_mapping
        )
        ra = result.risk_assessments[0]
        assert ra.high_risk_count > 0  # Some students should be high-risk

    def test_summary_generated(self, education_df, education_col_mapping):
        result = PredictiveAnalyticsRegistry.analyze(
            "education", education_df, education_col_mapping
        )
        assert result.summary != ""
        assert "risk" in result.summary.lower()


# ── Agriculture Predictive Analytics Tests ────────────────


class TestAgriculturePredictiveAnalytics:
    def test_analyze_returns_result(self, agriculture_df, agriculture_col_mapping):
        result = PredictiveAnalyticsRegistry.analyze(
            "agriculture", agriculture_df, agriculture_col_mapping
        )
        assert isinstance(result, PredictiveIntelligenceResult)
        assert result.industry == "agriculture"

    def test_yield_prediction(self, agriculture_df, agriculture_col_mapping):
        result = PredictiveAnalyticsRegistry.analyze(
            "agriculture", agriculture_df, agriculture_col_mapping
        )
        assert len(result.predictions) > 0
        pred = result.predictions[0]
        assert "Yield" in pred.name or "Production" in pred.name

    def test_production_forecast(self, agriculture_df, agriculture_col_mapping):
        result = PredictiveAnalyticsRegistry.analyze(
            "agriculture", agriculture_df, agriculture_col_mapping
        )
        assert len(result.forecasts) > 0

    def test_r_squared_computed(self, agriculture_df, agriculture_col_mapping):
        result = PredictiveAnalyticsRegistry.analyze(
            "agriculture", agriculture_df, agriculture_col_mapping
        )
        if result.predictions:
            assert result.predictions[0].r_squared >= 0

    def test_summary_generated(self, agriculture_df, agriculture_col_mapping):
        result = PredictiveAnalyticsRegistry.analyze(
            "agriculture", agriculture_df, agriculture_col_mapping
        )
        assert result.summary != ""


# ── Registry Tests ────────────────────────────────────────


class TestPredictiveAnalyticsRegistry:
    def test_registered_industries(self):
        industries = PredictiveAnalyticsRegistry.registered_industries()
        assert "retail" in industries
        assert "healthcare" in industries
        assert "education" in industries
        assert "agriculture" in industries

    def test_unknown_industry_returns_empty(self):
        df = pd.DataFrame({"a": [1, 2]})
        result = PredictiveAnalyticsRegistry.analyze("unknown_industry", df, {})
        assert result.forecasts == []
        assert result.predictions == []


# ── Pipeline Integration Tests ────────────────────────────


class TestPipelineIntegration:
    def test_predictive_in_mapping_result(self, retail_df):
        from semantic.mapping_engine import SemanticMappingEngine

        result = SemanticMappingEngine.analyze(retail_df, "retail.csv")
        assert result.predictive_intelligence is not None

    def test_predictive_in_to_dict(self, retail_df):
        from semantic.mapping_engine import SemanticMappingEngine

        result = SemanticMappingEngine.analyze(retail_df, "retail.csv")
        d = result.to_dict()
        assert "predictive_intelligence" in d
        assert d["predictive_intelligence"] is not None

    def test_healthcare_pipeline(self, healthcare_df):
        from semantic.mapping_engine import SemanticMappingEngine

        result = SemanticMappingEngine.analyze(healthcare_df, "hospital.csv")
        pi = result.predictive_intelligence
        assert pi is not None
        assert len(pi.forecasts) > 0 or len(pi.risk_assessments) > 0

    def test_education_pipeline(self, education_df):
        from semantic.mapping_engine import SemanticMappingEngine

        result = SemanticMappingEngine.analyze(education_df, "school.csv")
        pi = result.predictive_intelligence
        assert pi is not None
        assert len(pi.risk_assessments) > 0

    def test_agriculture_pipeline(self, agriculture_df):
        from semantic.mapping_engine import SemanticMappingEngine

        result = SemanticMappingEngine.analyze(agriculture_df, "farm.csv")
        pi = result.predictive_intelligence
        assert pi is not None
        assert len(pi.forecasts) > 0 or len(pi.predictions) > 0
