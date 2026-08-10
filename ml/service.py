"""ML platform service layer.

Orchestrates readiness, feature engineering, AutoML, forecasting, anomaly
detection, recommendations, what-if analysis, drift monitoring, and model
registry with tenant isolation.
"""

from __future__ import annotations

import logging
import os
import uuid
from typing import Any

import joblib
import pandas as pd
from sqlalchemy.orm import Session

from audit.service import log_audit_event
from ml.anomaly import AnomalyDetectionEngine, detect_spikes
from ml.automl import AutoMLEngine
from ml.decision import generate_recommendation, generate_what_if_scenarios
from ml.drift import detect_data_drift, summarize_drift
from ml.features import FeatureEngineer, auto_clean
from ml.forecast import ForecastingEngine, forecast_arima, forecast_ets, forecast_prophet
from ml.models import (
    MLAnomalyJob,
    MLDriftRecord,
    MLForecast,
    MLModel,
    MLPrediction,
    MLTrainingRun,
    ModelStatus,
    ModelType,
)
from ml.readiness import assess_ml_readiness
from shared.dependencies import AuthorizationError

logger = logging.getLogger(__name__)


class MLService:
    """Business logic for the enterprise ML platform."""

    def __init__(self, db: Session, current_user: dict[str, Any]) -> None:
        self.db = db
        self.user_id = current_user.get("id")
        self.organization_id = current_user.get("organization_id")
        self.is_super_admin = "super_admin" in current_user.get("roles", [])

    def _org_filter(self, query):
        if self.is_super_admin:
            return query
        return query.filter(MLModel.organization_id == self.organization_id)

    def _load_dataset(self, source: str) -> pd.DataFrame:
        """Resolve a dataset source to a DataFrame.

        Supports:
        - Dataset library registered IDs
        - Local CSV/Excel file paths
        """
        from dataset_library import get_dataset_library

        library = get_dataset_library()
        entry = library.get(source)
        if entry is not None and entry.file_path and os.path.exists(entry.file_path):
            if entry.file_path.lower().endswith(".csv"):
                return pd.read_csv(entry.file_path)
            return pd.read_excel(entry.file_path)

        if os.path.exists(source):
            if source.lower().endswith(".csv"):
                return pd.read_csv(source)
            return pd.read_excel(source)

        raise FileNotFoundError(f"Dataset source not found: {source}")

    def _audit(self, action: str, resource: str, details: dict[str, Any] | None = None) -> None:
        try:
            resource_type, resource_id = (
                resource.split(":", 1) if ":" in resource else (resource, None)
            )
            log_audit_event(
                db=self.db,
                action=action,
                user_id=self.user_id,
                organization_id=self.organization_id,
                resource_type=resource_type,
                resource_id=resource_id,
                new_values=details or {},
            )
        except Exception:
            logger.warning("ML audit logging failed for action '%s' on '%s'", action, resource, exc_info=True)

    # -------------------------------------------------------------------------
    # Readiness
    # -------------------------------------------------------------------------
    def readiness(
        self, source: str, target_column: str | None = None, sample_limit: int = 10000
    ) -> dict[str, Any]:
        df = self._load_dataset(source)
        if len(df) > sample_limit:
            df = df.sample(sample_limit, random_state=42)
        report = assess_ml_readiness(df, target_column)
        self._audit("ml.readiness", f"dataset:{source}", {"target_column": target_column})
        return report

    # -------------------------------------------------------------------------
    # Feature engineering
    # -------------------------------------------------------------------------
    def engineer_features(self, source: str, config: dict[str, Any]) -> dict[str, Any]:
        df = self._load_dataset(source)
        df, clean_log = auto_clean(df)
        target_column = config.get("target_column")
        target = None
        if target_column and target_column in df.columns:
            target = df[target_column]
            df = df.drop(columns=[target_column])

        engineer = FeatureEngineer(config)
        X = engineer.fit_transform(df, target)
        if target is not None:
            X[target_column] = target.values

        self._audit("ml.features", f"dataset:{source}", {"operations": engineer.log})
        return {
            "original_shape": (
                clean_log["operations"][0].get("shape_before")
                if clean_log["operations"]
                else list(df.shape)
            ),
            "transformed_shape": list(X.shape),
            "output_columns": X.columns.tolist(),
            "log": engineer.log + clean_log["operations"],
        }

    # -------------------------------------------------------------------------
    # Model registry
    # -------------------------------------------------------------------------
    def create_model(self, payload: dict[str, Any]) -> MLModel:
        model = MLModel(
            name=payload["name"],
            description=payload.get("description", ""),
            model_type=ModelType(payload["model_type"]),
            target_column=payload.get("target_column"),
            feature_columns=payload.get("feature_columns", []),
            algorithm=payload.get("algorithm"),
            hyperparameters=payload.get("hyperparameters", {}),
            dataset_source=payload["dataset_source"],
            organization_id=self.organization_id,
            created_by=self.user_id,
        )
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        self._audit(
            "ml.model.create",
            f"ml_model:{model.id}",
            {"name": model.name, "type": model.model_type.value},
        )
        return model

    def get_model(self, model_id: str) -> MLModel:
        model = self._org_filter(self.db.query(MLModel)).filter(MLModel.id == model_id).first()
        if not model:
            raise AuthorizationError("Model not found or access denied")
        return model

    def list_models(self, model_type: str | None = None) -> list[MLModel]:
        query = self._org_filter(self.db.query(MLModel))
        if model_type:
            query = query.filter(MLModel.model_type == ModelType(model_type))
        return query.order_by(MLModel.created_at.desc()).all()

    def delete_model(self, model_id: str) -> None:
        model = self.get_model(model_id)
        model.status = ModelStatus.ARCHIVED
        model.deployment_status = "archived"
        self.db.commit()
        self._audit("ml.model.delete", f"ml_model:{model_id}")

    def update_deployment(self, model_id: str, status: str) -> MLModel:
        model = self.get_model(model_id)
        model.deployment_status = status
        self.db.commit()
        self._audit("ml.model.deploy", f"ml_model:{model_id}", {"status": status})
        return model

    # -------------------------------------------------------------------------
    # Training
    # -------------------------------------------------------------------------
    def train_model(self, model_id: str, payload: dict[str, Any]) -> MLTrainingRun:
        model = self.get_model(model_id)
        df = self._load_dataset(model.dataset_source)
        df, _ = auto_clean(df)

        run = MLTrainingRun(
            model_id=model.id,
            algorithm=payload.get("algorithm") or model.algorithm,
            hyperparameters=payload.get("hyperparameters", model.hyperparameters or {}),
            dataset_source=model.dataset_source,
            created_by=self.user_id,
            organization_id=self.organization_id,
            status="training",
            started_at=pd.Timestamp.now(tz="UTC"),
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)

        try:
            feature_config = payload.get("feature_config", {})
            feature_config.setdefault(
                "target_type",
                "regression" if model.model_type == ModelType.REGRESSION else "classification",
            )
            if model.model_type == ModelType.CLASSIFICATION:
                feature_config["target_type"] = "classification"

            engineer = FeatureEngineer(feature_config)
            target_col = model.target_column
            y = None
            X = df.copy()
            if target_col and target_col in X.columns:
                y = X[target_col]
                X = X.drop(columns=[target_col])

            X_transformed = engineer.fit_transform(X, y)
            model.feature_columns = engineer.feature_names_out

            if model.model_type == ModelType.FORECASTING:
                result = self._train_forecasting(model, df, payload, run)
            else:
                automl = AutoMLEngine(
                    model_type=model.model_type.value,
                    algorithm=run.algorithm,
                    hyperparameters=run.hyperparameters,
                )
                result = automl.run(
                    X_transformed,
                    y,
                    test_size=payload.get("test_size", 0.2),
                    include_all=payload.get("include_all", False),
                )
                best = result["best"]
                if best:
                    run.algorithm = best["algorithm"]
                    run.train_metrics = best.get("metrics", {})
                    run.test_metrics = best.get("metrics", {})
                    run.comparison_metrics = {"ranking": result["ranking"]}
                    model.algorithm = best["algorithm"]
                    model.metrics = best.get("metrics", {})
                    artifact_dir = os.environ.get(
                        "ML_ARTIFACT_DIR", os.path.join(os.getcwd(), "ml_artifacts")
                    )
                    os.makedirs(artifact_dir, exist_ok=True)
                    artifact_path = os.path.join(artifact_dir, f"{model.id}.joblib")
                    joblib.dump(
                        {
                            "model": automl.best_model,
                            "label_encoder": automl.label_encoder,
                            "features": model.feature_columns,
                        },
                        artifact_path,
                    )
                    run.artifact_path = artifact_path
                    model.artifact_path = artifact_path

            run.status = "completed"
            model.status = ModelStatus.READY
            run.completed_at = pd.Timestamp.now(tz="UTC")
        except Exception as exc:
            run.status = "failed"
            run.error_message = str(exc)
            model.status = ModelStatus.FAILED
            raise
        finally:
            self.db.commit()
            self.db.refresh(run)
            self.db.refresh(model)
            self._audit(
                "ml.model.train", f"ml_model:{model_id}", {"run_id": run.id, "status": run.status}
            )
        return run

    def _train_forecasting(
        self, model: MLModel, df: pd.DataFrame, payload: dict[str, Any], run: MLTrainingRun
    ) -> dict[str, Any]:
        date_col = payload.get("date_column", "date")
        target_col = model.target_column
        horizon = payload.get("horizon", 30)
        freq = payload.get("frequency", "D")
        algorithm = payload.get("algorithm", "auto")

        engine = ForecastingEngine(algorithm=algorithm, frequency=freq)
        fit_result = engine.fit(df, date_col, target_col)
        if fit_result["status"] == "failed":
            raise RuntimeError(fit_result.get("error", "Forecast training failed"))

        run.algorithm = engine.algorithm
        run.train_metrics = fit_result
        model.algorithm = engine.algorithm

        # Persist simple state for predictions
        artifact_dir = os.environ.get("ML_ARTIFACT_DIR", os.path.join(os.getcwd(), "ml_artifacts"))
        os.makedirs(artifact_dir, exist_ok=True)
        artifact_path = os.path.join(artifact_dir, f"{model.id}.joblib")
        joblib.dump({"engine": engine}, artifact_path)
        run.artifact_path = artifact_path
        model.artifact_path = artifact_path

        # Generate initial forecast
        forecast = engine.predict(horizon)
        forecast_record = MLForecast(
            model_id=model.id,
            horizon=horizon,
            frequency=freq,
            forecast_values=forecast.get("values", []),
            confidence_intervals={"lower": forecast.get("lower"), "upper": forecast.get("upper")},
        )
        self.db.add(forecast_record)
        return {"status": "completed", "algorithm": engine.algorithm}

    def retrain_model(self, model_id: str, payload: dict[str, Any]) -> MLTrainingRun:
        original = self.get_model(model_id)
        # Bump version and create child model
        child = MLModel(
            name=f"{original.name} (retrain v{original.version + 1})",
            description=original.description,
            model_type=original.model_type,
            target_column=original.target_column,
            feature_columns=original.feature_columns,
            algorithm=original.algorithm,
            hyperparameters=original.hyperparameters,
            dataset_source=original.dataset_source,
            organization_id=self.organization_id,
            created_by=self.user_id,
            parent_model_id=original.id,
            version=original.version + 1,
        )
        self.db.add(child)
        self.db.commit()
        self.db.refresh(child)
        return self.train_model(child.id, payload)

    def predict(
        self, model_id: str, features: list[dict[str, Any]], horizon: int = 30
    ) -> list[Any]:
        model = self.get_model(model_id)
        if not model.artifact_path or not os.path.exists(model.artifact_path):
            raise RuntimeError("Model artifact not found")

        artifact = joblib.load(model.artifact_path)
        df = pd.DataFrame(features)
        if model.model_type == ModelType.FORECASTING:
            engine = artifact["engine"]
            result = engine.predict(horizon)
            return result.get("values", [])

        automl = AutoMLEngine(model.model_type.value, algorithm=model.algorithm)
        automl.best_model = artifact["model"]
        automl.label_encoder = artifact.get("label_encoder")
        preds = automl.predict(df)

        prediction_record = MLPrediction(
            model_id=model.id, input_features=features, prediction={"values": preds.tolist()}
        )
        self.db.add(prediction_record)
        self.db.commit()
        return preds.tolist()

    # -------------------------------------------------------------------------
    # Forecasting
    # -------------------------------------------------------------------------
    def forecast(self, payload: dict[str, Any]) -> dict[str, Any]:
        df = self._load_dataset(payload["dataset_source"])
        df, _ = auto_clean(df)
        date_col = payload["date_column"]
        target_col = payload["target_column"]
        horizon = payload["horizon"]
        freq = payload["frequency"]
        algorithm = payload["algorithm"]

        series = df[[date_col, target_col]].copy()

        algorithms = ["ExponentialSmoothing", "ARIMA"] if algorithm == "auto" else [algorithm]

        results = []
        for algo in algorithms:
            if algo == "ARIMA":
                result = forecast_arima(
                    series.set_index(date_col)[target_col].sort_index(), horizon
                )
            elif algo == "ExponentialSmoothing":
                result = forecast_ets(series.set_index(date_col)[target_col].sort_index(), horizon)
            elif algo == "Prophet":
                result = forecast_prophet(df, date_col, target_col, horizon, freq)
            else:
                continue
            results.append(result)

        # Return first successful; if all fail, return errors
        for result in results:
            if "error" not in result:
                self._audit(
                    "ml.forecast",
                    f"dataset:{payload['dataset_source']}",
                    {"algorithm": result["algorithm"], "horizon": horizon},
                )
                return result
        return {"status": "failed", "errors": results}

    # -------------------------------------------------------------------------
    # Anomaly detection
    # -------------------------------------------------------------------------
    def detect_anomalies(self, payload: dict[str, Any]) -> dict[str, Any]:
        df = self._load_dataset(payload["dataset_source"])
        df, _ = auto_clean(df)
        column = payload.get("column")
        if column and column in df.columns:
            result = detect_spikes(df, column, payload.get("threshold", 3.0))
        else:
            engine = AnomalyDetectionEngine(
                algorithm=payload.get("algorithm", "isolation_forest"),
                **payload.get("config", {}),
            )
            result = engine.detect(df)
        self._audit(
            "ml.anomaly",
            f"dataset:{payload['dataset_source']}",
            {"algorithm": result.get("algorithm")},
        )

        # Persist job record
        job = MLAnomalyJob(
            name=payload.get("name", f"Anomaly job {uuid.uuid4().hex[:8]}"),
            dataset_source=payload["dataset_source"],
            algorithm=result.get("algorithm", payload.get("algorithm", "z_score")),
            config=payload.get("config", {}),
            latest_result=result,
            organization_id=self.organization_id,
            created_by=self.user_id,
        )
        self.db.add(job)
        self.db.commit()
        return result

    # -------------------------------------------------------------------------
    # Decision intelligence
    # -------------------------------------------------------------------------
    def recommend(self, payload: dict[str, Any]) -> dict[str, Any]:
        df = self._load_dataset(payload["dataset_source"])
        df, _ = auto_clean(df)
        forecast_values = None
        if payload.get("include_forecast"):
            forecast_result = self.forecast(
                {
                    "dataset_source": payload["dataset_source"],
                    "date_column": payload.get("date_column", "date"),
                    "target_column": payload["metric_column"],
                    "horizon": payload.get("forecast_horizon", 30),
                    "frequency": "D",
                    "algorithm": "auto",
                }
            )
            if "values" in forecast_result:
                forecast_values = forecast_result["values"]
        recommendation = generate_recommendation(
            df,
            payload["metric_column"],
            segment_column=payload.get("segment_column"),
            forecast_values=forecast_values,
        )
        self._audit(
            "ml.recommend",
            f"dataset:{payload['dataset_source']}",
            {"metric": payload["metric_column"]},
        )
        return recommendation

    def what_if(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        df = self._load_dataset(payload["dataset_source"])
        df, _ = auto_clean(df)
        scenarios = generate_what_if_scenarios(
            df,
            payload["metric_column"],
            driver_column=payload.get("driver_column"),
            scenarios=payload.get("scenarios"),
        )
        self._audit(
            "ml.what_if", f"dataset:{payload['dataset_source']}", {"scenarios": len(scenarios)}
        )
        return scenarios

    # -------------------------------------------------------------------------
    # Drift
    # -------------------------------------------------------------------------
    def detect_drift(self, payload: dict[str, Any]) -> dict[str, Any]:
        model = self.get_model(payload["model_id"])
        reference = self._load_dataset(model.dataset_source)
        current = self._load_dataset(payload["current_dataset_source"])
        reference, _ = auto_clean(reference)
        current, _ = auto_clean(current)
        report = detect_data_drift(reference, current, threshold=payload.get("threshold", 0.05))
        summary = summarize_drift(report)
        drift_record = MLDriftRecord(
            model_id=model.id,
            drift_type="data_drift",
            score=summary["drift_ratio"],
            threshold=payload.get("threshold", 0.05),
            details=report,
        )
        self.db.add(drift_record)
        self.db.commit()
        self._audit(
            "ml.drift", f"ml_model:{model.id}", {"drift_detected": report["drift_detected"]}
        )
        return report

    # -------------------------------------------------------------------------
    # Dashboard summaries
    # -------------------------------------------------------------------------
    def dashboard_summary(self) -> dict[str, Any]:
        query = self._org_filter(self.db.query(MLModel))
        models = query.all()
        forecasts = (
            self.db.query(MLForecast)
            .filter(MLForecast.model_id.in_([m.id for m in models]))
            .count()
        )
        training_runs = (
            self.db.query(MLTrainingRun)
            .filter(MLTrainingRun.organization_id == self.organization_id)
            .count()
        )
        drift_records = (
            self.db.query(MLDriftRecord)
            .filter(MLDriftRecord.model_id.in_([m.id for m in models]))
            .count()
        )
        return {
            "active_models": sum(
                1
                for m in models
                if m.status == ModelStatus.READY and m.deployment_status == "deployed"
            ),
            "total_models": len(models),
            "deployed_models": sum(1 for m in models if m.deployment_status == "deployed"),
            "failed_models": sum(1 for m in models if m.status == ModelStatus.FAILED),
            "training_runs": training_runs,
            "forecasts": forecasts,
            "drift_records": drift_records,
            "recent_models": [
                {
                    "id": m.id,
                    "name": m.name,
                    "type": m.model_type.value,
                    "status": m.status.value,
                    "algorithm": m.algorithm,
                }
                for m in models[:10]
            ],
        }

    def compare_models(self, model_ids: list[str]) -> list[dict[str, Any]]:
        models = []
        for mid in model_ids:
            try:
                models.append(self.get_model(mid))
            except Exception:
                continue
        return [
            {
                "id": m.id,
                "name": m.name,
                "version": m.version,
                "algorithm": m.algorithm,
                "metrics": m.metrics,
                "deployment_status": m.deployment_status,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in models
        ]
