"""Tests for the enterprise ML platform."""

from __future__ import annotations

import os
import tempfile
from datetime import datetime

import numpy as np
import pandas as pd
import pytest

from ml.anomaly import AnomalyDetectionEngine, detect_spikes
from ml.automl import AutoMLEngine
from ml.decision import generate_recommendation, generate_what_if_scenarios
from ml.drift import detect_data_drift
from ml.features import FeatureEngineer, auto_clean
from ml.forecast import ForecastingEngine
from ml.models import ModelType
from ml.readiness import assess_ml_readiness
from ml.service import MLService


def _temp_csv(df, tmp_path):
    path = tmp_path / "data.csv"
    df.to_csv(path, index=False)
    return str(path)


class TestMLReadiness:
    def test_empty_dataset_not_ready(self):
        df = pd.DataFrame()
        report = assess_ml_readiness(df)
        assert report["ready"] is False
        assert report["quality_score"] == 0.0

    def test_classification_suggestions(self):
        df = pd.DataFrame(
            {
                "age": [20, 25, 30, 35, 40],
                "income": [30000, 40000, 50000, 60000, 70000],
                "churn": ["yes", "no", "no", "yes", "no"],
            }
        )
        report = assess_ml_readiness(df, target_column="churn")
        assert report["ready"] is True
        assert any(s["family"] == "classification" for s in report["suggested_algorithms"])


class TestFeatureEngineering:
    def test_auto_clean_and_transform(self):
        df = pd.DataFrame(
            {
                "num1": [1.0, 2.0, np.nan, 4.0],
                "cat1": ["a", "b", np.nan, "a"],
                "target": [0, 1, 0, 1],
            }
        )
        cleaned, log = auto_clean(df)
        assert cleaned.isna().sum().sum() == 0
        engineer = FeatureEngineer({"scaling": "standard"})
        X = engineer.fit_transform(cleaned.drop(columns=["target"]), cleaned["target"])
        assert X.shape[0] == 4
        assert len(engineer.feature_names_out) > 0


class TestAutoML:
    def test_classification_training(self):
        df = pd.DataFrame(
            {
                "x1": np.random.rand(50),
                "x2": np.random.rand(50),
                "y": np.random.choice(["A", "B"], size=50),
            }
        )
        X = df[["x1", "x2"]]
        y = df["y"]
        engine = AutoMLEngine("classification", algorithm="LogisticRegression")
        result = engine.run(X, y)
        assert result["best"] is not None
        assert result["best"]["status"] == "completed"
        assert "accuracy" in result["best"]["metrics"]

    def test_regression_training(self):
        df = pd.DataFrame(
            {
                "x1": np.random.rand(50),
                "x2": np.random.rand(50),
                "y": np.random.rand(50),
            }
        )
        X = df[["x1", "x2"]]
        y = df["y"]
        engine = AutoMLEngine("regression", algorithm="LinearRegression")
        result = engine.run(X, y)
        assert result["best"] is not None
        assert "rmse" in result["best"]["metrics"]


class TestForecasting:
    def test_forecast_engine(self):
        dates = pd.date_range(end=datetime.now(), periods=30)
        df = pd.DataFrame({"date": dates, "value": np.random.rand(30)})
        engine = ForecastingEngine(algorithm="ARIMA")
        fit = engine.fit(df, "date", "value")
        assert fit["status"] == "completed"
        pred = engine.predict(7)
        assert len(pred["values"]) == 7


class TestAnomalyDetection:
    def test_isolation_forest(self):
        df = pd.DataFrame(
            {
                "amount": np.concatenate([np.random.rand(45), np.random.rand(5) * 100]),
            }
        )
        engine = AnomalyDetectionEngine(algorithm="isolation_forest")
        result = engine.detect(df)
        assert result["status"] == "completed"
        assert result["anomaly_rate"] >= 0

    def test_zscore_spikes(self):
        df = pd.DataFrame({"sales": [1, 2, 3, 2, 1, 100]})
        result = detect_spikes(df, "sales", threshold=2.0)
        assert result["status"] == "completed"
        assert result["anomaly_count"] == 1


class TestDecisionIntelligence:
    def test_recommendation(self):
        df = pd.DataFrame(
            {
                "sales": [100, 110, 120, 90],
                "region": ["North", "North", "South", "South"],
            }
        )
        rec = generate_recommendation(df, "sales", segment_column="region")
        assert rec["recommendation"]
        assert rec["confidence"] > 0

    def test_what_if(self):
        df = pd.DataFrame({"sales": [100, 110, 120, 90]})
        scenarios = generate_what_if_scenarios(df, "sales")
        assert len(scenarios) == 4
        assert "projected" in scenarios[0]


class TestDrift:
    def test_numeric_drift(self):
        ref = pd.DataFrame({"x": np.random.normal(0, 1, 100)})
        cur = pd.DataFrame({"x": np.random.normal(5, 1, 100)})
        report = detect_data_drift(ref, cur)
        assert report["drift_detected"] is True
        assert report["drifted_features"] >= 1


class TestMLService:
    def test_readiness_endpoint(self, db_session):
        user = {"id": 1, "organization_id": 1, "roles": ["analyst"]}
        service = MLService(db_session, user)
        df = pd.DataFrame({"x": [1, 2, 3], "y": [0, 1, 0]})
        str(db_session.bind.url).replace("sqlite:///", "")
        # Use a temp CSV independent of session path
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
            df.to_csv(f.name, index=False)
            csv_path = f.name
        report = service.readiness(csv_path, target_column="y")
        assert report["ready"] is True
        os.unlink(csv_path)

    def test_create_model(self, db_session):
        user = {"id": 1, "organization_id": 1, "roles": ["analyst"]}
        service = MLService(db_session, user)
        model = service.create_model(
            {
                "name": "Test Model",
                "description": "",
                "model_type": "classification",
                "dataset_source": os.path.join(tempfile.gettempdir(), "dummy.csv"),
                "target_column": "y",
            }
        )
        assert model.name == "Test Model"
        assert model.model_type == ModelType.CLASSIFICATION


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
