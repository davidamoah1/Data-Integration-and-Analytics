"""AutoML engine.

Trains, evaluates, and compares a configurable set of models for classification,
regression, clustering, anomaly detection, and time-series forecasting.
"""

from __future__ import annotations

import os
import pickle
import tempfile
from typing import Any

import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN, AgglomerativeClustering, KMeans
from sklearn.ensemble import (
    GradientBoostingClassifier,
    GradientBoostingRegressor,
    IsolationForest,
    RandomForestClassifier,
    RandomForestRegressor,
)
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import LabelEncoder

from ml.metrics import (
    anomaly_metrics,
    classification_metrics,
    clustering_metrics,
    regression_metrics,
)

ALGORITHM_REGISTRY: dict[str, dict[str, Any]] = {
    "classification": {
        "LogisticRegression": {
            "class": LogisticRegression,
            "default": {"max_iter": 1000, "random_state": 42},
        },
        "RandomForestClassifier": {
            "class": RandomForestClassifier,
            "default": {"n_estimators": 100, "random_state": 42},
        },
        "GradientBoostingClassifier": {
            "class": GradientBoostingClassifier,
            "default": {"n_estimators": 100, "random_state": 42},
        },
    },
    "regression": {
        "LinearRegression": {"class": LinearRegression, "default": {}},
        "RandomForestRegressor": {
            "class": RandomForestRegressor,
            "default": {"n_estimators": 100, "random_state": 42},
        },
        "GradientBoostingRegressor": {
            "class": GradientBoostingRegressor,
            "default": {"n_estimators": 100, "random_state": 42},
        },
    },
    "clustering": {
        "KMeans": {
            "class": KMeans,
            "default": {"n_clusters": 3, "random_state": 42, "n_init": "auto"},
        },
        "DBSCAN": {"class": DBSCAN, "default": {"eps": 0.5, "min_samples": 5}},
        "AgglomerativeClustering": {"class": AgglomerativeClustering, "default": {"n_clusters": 3}},
    },
    "anomaly_detection": {
        "IsolationForest": {
            "class": IsolationForest,
            "default": {"n_estimators": 100, "random_state": 42, "contamination": "auto"},
        },
        "LocalOutlierFactor": {
            "class": LocalOutlierFactor,
            "default": {"n_neighbors": 20, "contamination": "auto"},
        },
    },
}


def _safe_split(X: pd.DataFrame, y: pd.Series | None, test_size: float = 0.2) -> tuple:
    """Split data safely even for very small datasets."""
    if y is not None and len(y) < 10:
        return X, X, y, y
    if y is None and len(X) < 10:
        return X, X, None, None
    return train_test_split(X, y, test_size=test_size, random_state=42)


class AutoMLEngine:
    """Train and compare models for a given problem type."""

    def __init__(
        self,
        model_type: str,
        algorithm: str | None = None,
        hyperparameters: dict[str, Any] | None = None,
    ) -> None:
        self.model_type = model_type
        self.algorithm = algorithm
        self.hyperparameters = hyperparameters or {}
        self.results: list[dict[str, Any]] = []
        self.best_model: Any = None
        self.best_algorithm: str | None = None
        self.label_encoder: LabelEncoder | None = None

    def run(
        self,
        X: pd.DataFrame,
        y: pd.Series | None = None,
        test_size: float = 0.2,
        include_all: bool = False,
    ) -> dict[str, Any]:
        """Run AutoML training.

        Args:
            X: Feature matrix.
            y: Target vector (required for classification/regression).
            test_size: Fraction held out for evaluation.
            include_all: If True, evaluate all candidate algorithms and return ranking.

        Returns:
            Training summary with best result and optional comparison table.
        """
        if self.model_type in ("classification", "regression") and y is None:
            raise ValueError(f"Target column required for {self.model_type}")

        candidates = self._get_candidate_algorithms(include_all)
        self.results = []

        X_train, X_test, y_train, y_test = _safe_split(X, y, test_size)

        for name in candidates:
            try:
                result = self._train_single(name, X_train, X_test, y_train, y_test)
                self.results.append(result)
            except Exception as exc:
                self.results.append({"algorithm": name, "status": "failed", "error": str(exc)})

        successful = [r for r in self.results if r.get("status") == "completed"]
        best = self._pick_best(successful)
        if best:
            self.best_algorithm = best["algorithm"]

        return {
            "model_type": self.model_type,
            "best": best,
            "ranking": successful,
            "all_results": self.results,
        }

    def _get_candidate_algorithms(self, include_all: bool) -> list[str]:
        family = ALGORITHM_REGISTRY.get(self.model_type, {})
        if self.algorithm and self.algorithm in family:
            return [self.algorithm]
        if include_all:
            return list(family.keys())
        if self.algorithm:
            raise ValueError(f"Unknown algorithm '{self.algorithm}' for {self.model_type}")
        return [self._default_algorithm()]

    def _default_algorithm(self) -> str:
        defaults = {
            "classification": "RandomForestClassifier",
            "regression": "RandomForestRegressor",
            "clustering": "KMeans",
            "anomaly_detection": "IsolationForest",
        }
        return defaults.get(self.model_type, list(ALGORITHM_REGISTRY[self.model_type].keys())[0])

    def _train_single(self, name: str, X_train, X_test, y_train, y_test) -> dict[str, Any]:
        spec = ALGORITHM_REGISTRY[self.model_type][name]
        params = {**spec["default"], **self.hyperparameters}
        estimator = spec["class"](**params)

        if self.model_type == "classification":
            y_train_enc, y_test_enc = self._encode_target(y_train, y_test)
            estimator.fit(X_train, y_train_enc)
            y_pred = estimator.predict(X_test)
            y_pred = self.label_encoder.inverse_transform(y_pred)
            y_proba = (
                estimator.predict_proba(X_test) if hasattr(estimator, "predict_proba") else None
            )
            metrics = classification_metrics(y_test, y_pred, y_proba)
        elif self.model_type == "regression":
            estimator.fit(X_train, y_train)
            y_pred = estimator.predict(X_test)
            metrics = regression_metrics(y_test, y_pred)
        elif self.model_type == "clustering":
            estimator.fit(X_train)
            labels_train = (
                estimator.labels_ if hasattr(estimator, "labels_") else estimator.predict(X_train)
            )
            labels_test = (
                estimator.predict(X_test)
                if hasattr(estimator, "predict")
                else labels_train[: len(X_test)]
            )
            metrics = clustering_metrics(X_train, labels_train)
            metrics["test_labels"] = labels_test.tolist()[:5]
        elif self.model_type == "anomaly_detection":
            estimator.fit(X_train)
            if hasattr(estimator, "predict"):
                labels = estimator.predict(X_test)
            else:
                labels = estimator.fit_predict(X_test)
            metrics = anomaly_metrics(labels)
        else:
            raise ValueError(f"Unsupported model_type: {self.model_type}")

        self.best_model = estimator
        return {
            "algorithm": name,
            "status": "completed",
            "metrics": metrics,
            "hyperparameters": params,
        }

    def _encode_target(self, y_train, y_test):
        self.label_encoder = LabelEncoder()
        y_train_enc = self.label_encoder.fit_transform(y_train.astype(str))
        y_test_enc = self.label_encoder.transform(y_test.astype(str))
        return y_train_enc, y_test_enc

    def _pick_best(self, results: list[dict[str, Any]]) -> dict[str, Any] | None:
        if not results:
            return None
        if self.model_type == "classification":
            return max(results, key=lambda r: r["metrics"].get("f1", 0))
        if self.model_type == "regression":
            return min(results, key=lambda r: r["metrics"].get("rmse", float("inf")))
        if self.model_type == "clustering":
            return max(results, key=lambda r: r["metrics"].get("silhouette_score") or -1)
        if self.model_type == "anomaly_detection":
            return results[0]
        return results[0]

    def predict(self, X: pd.DataFrame) -> np.ndarray | pd.Series:
        if self.best_model is None:
            raise RuntimeError("Model has not been trained")
        preds = self.best_model.predict(X)
        if self.model_type == "classification" and self.label_encoder is not None:
            return self.label_encoder.inverse_transform(preds)
        return preds

    def save_artifact(self, path: str | None = None) -> str:
        if self.best_model is None:
            raise RuntimeError("No trained model to save")
        if path is None:
            path = os.path.join(tempfile.gettempdir(), f"model_{os.urandom(4).hex}.pkl")
        with open(path, "wb") as fh:
            pickle.dump({"model": self.best_model, "label_encoder": self.label_encoder}, fh)
        return path

    @staticmethod
    def load_artifact(path: str) -> dict[str, Any]:
        """Load a model artifact from a trusted path.

        Security:
            - Path must be within the designated artifact directory
              (tempdir for dev, or a configured ARTIFACT_DIR for production).
            - Path traversal is rejected.
            - The unpickler is restricted to known-safe ML classes.
        """
        artifact_dir = os.path.realpath(
            os.getenv("ML_ARTIFACT_DIR")
            or os.getenv("ARTIFACT_DIR")
            or os.path.join(os.getcwd(), "ml_artifacts")
        )
        real_path = os.path.realpath(path)
        if not real_path.startswith(artifact_dir + os.sep) and real_path != artifact_dir:
            raise ValueError(
                f"Artifact path must be within the designated artifact directory "
                f"({artifact_dir}). Got: {real_path}"
            )
        allowed_modules = {
            "sklearn",
            "sklearn.",
            "numpy",
            "numpy.",
            "pandas",
            "pandas.",
            "scipy",
            "scipy.",
            "joblib",
            "joblib.",
            "ml.forecast",
            "ml.",
        }

        class _RestrictedUnpickler(pickle.Unpickler):
            def find_class(self, module: str, name: str) -> Any:
                if any(module.startswith(m) for m in allowed_modules):
                    return super().find_class(module, name)
                raise pickle.UnpicklingError(
                    f"Blocked unsafe import during unpickling: {module}.{name}"
                )

        with open(real_path, "rb") as fh:
            data = _RestrictedUnpickler(fh).load()
        if not isinstance(data, dict) or "model" not in data:
            raise ValueError("Invalid artifact: expected dict with 'model' key")
        return data
