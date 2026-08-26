"""ML Lab service â€” no-code and professional machine learning."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from studios.models import MLExperiment, ModelComparison


class MLLabService:
    """No-code and professional ML experiment service."""

    def __init__(self, db: DbSession):
        self.db = db

    # â”€â”€â”€ Experiment Management â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def create_experiment(
        self,
        org_id: int,
        dataset_id: int,
        user_id: int,
        name: str,
        task_type: str,
        features: list[str] | None = None,
        target: str | None = None,
        algorithm: str | None = None,
        hyperparameters: dict | None = None,
        is_no_code: bool = True,
    ) -> MLExperiment:
        exp = MLExperiment(
            organization_id=org_id,
            dataset_id=dataset_id,
            name=name,
            task_type=task_type,
            algorithm=algorithm,
            features=features,
            target=target,
            hyperparameters=hyperparameters or {},
            is_no_code=is_no_code,
            created_by=user_id,
            status="created",
        )
        self.db.add(exp)
        self.db.commit()
        return exp

    def list_experiments(self, org_id: int, dataset_id: int | None = None) -> list[MLExperiment]:
        query = select(MLExperiment).where(MLExperiment.organization_id == org_id)
        if dataset_id:
            query = query.where(MLExperiment.dataset_id == dataset_id)
        return self.db.execute(query.order_by(MLExperiment.created_at.desc())).scalars().all()

    def get_experiment(self, exp_id: int, org_id: int) -> MLExperiment | None:
        return self.db.execute(
            select(MLExperiment).where(
                MLExperiment.id == exp_id,
                MLExperiment.organization_id == org_id,
            )
        ).scalar_one_or_none()

    # â”€â”€â”€ Training â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    @staticmethod
    def train_classification(
        df: pd.DataFrame, features: list[str], target: str, algorithm: str = "random_forest"
    ) -> dict:
        """Train a classification model."""
        from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
        from sklearn.linear_model import LogisticRegression
        from sklearn.metrics import (
            accuracy_score,
            classification_report,
            f1_score,
            precision_score,
            recall_score,
        )
        from sklearn.model_selection import cross_val_score, train_test_split
        from sklearn.preprocessing import LabelEncoder

        X = df[features].dropna()
        y = df.loc[X.index, target].dropna()
        X = X.loc[y.index]

        # Encode categorical features
        encoders = {}
        for col in X.select_dtypes(include=["object"]).columns:
            le = LabelEncoder()
            X[col] = le.fit_transform(X[col].astype(str))
            encoders[col] = le

        # Encode target if needed
        target_encoder = None
        if y.dtype == "object":
            target_encoder = LabelEncoder()
            y = target_encoder.fit_transform(y)

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        models = {
            "random_forest": RandomForestClassifier(n_estimators=100, random_state=42),
            "logistic_regression": LogisticRegression(max_iter=1000, random_state=42),
            "gradient_boosting": GradientBoostingClassifier(random_state=42),
        }

        model = models.get(algorithm, models["random_forest"])
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)

        # Metrics
        metrics = {
            "accuracy": float(accuracy_score(y_test, y_pred)),
            "precision": float(
                precision_score(y_test, y_pred, average="weighted", zero_division=0)
            ),
            "recall": float(recall_score(y_test, y_pred, average="weighted", zero_division=0)),
            "f1": float(f1_score(y_test, y_pred, average="weighted", zero_division=0)),
        }

        # Cross-validation
        cv_scores = cross_val_score(model, X, y, cv=5, scoring="accuracy")
        metrics["cv_mean"] = float(cv_scores.mean())
        metrics["cv_std"] = float(cv_scores.std())

        # Feature importance
        feature_importance = {}
        if hasattr(model, "feature_importances_"):
            for f, imp in sorted(
                zip(features, model.feature_importances_, strict=False), key=lambda x: -x[1]
            ):
                feature_importance[f] = float(imp)
        elif hasattr(model, "coef_"):
            for f, coef in zip(
                features, model.coef_[0] if len(model.coef_) > 1 else model.coef_, strict=False
            ):
                feature_importance[f] = float(abs(coef))

        # Classification report
        target_encoder.classes_ if target_encoder else sorted(y.unique())
        report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)

        return {
            "algorithm": algorithm,
            "task_type": "classification",
            "metrics": metrics,
            "feature_importance": feature_importance,
            "classification_report": report,
            "n_features": len(features),
            "n_samples": int(len(X)),
            "n_train": int(len(X_train)),
            "n_test": int(len(X_test)),
            "model_summary": (
                f"{algorithm.replace('_', ' ').title()} classifier achieved "
                f"{metrics['accuracy']*100:.1f}% accuracy with F1={metrics['f1']:.4f}. "
                f"Cross-validation: {metrics['cv_mean']*100:.1f}% Â± {metrics['cv_std']*100:.1f}%."
            ),
            "explanation": (
                f"The model was trained on {len(X_train)} samples and tested on {len(X_test)} samples. "
                f"{'Top feature: ' + list(feature_importance.keys())[0] if feature_importance else 'No feature importance available.'}"
            ),
        }

    @staticmethod
    def train_regression(
        df: pd.DataFrame, features: list[str], target: str, algorithm: str = "random_forest"
    ) -> dict:
        """Train a regression model."""
        from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
        from sklearn.linear_model import LinearRegression
        from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
        from sklearn.model_selection import cross_val_score, train_test_split
        from sklearn.preprocessing import LabelEncoder

        X = df[features].dropna()
        y = df.loc[X.index, target].dropna()
        X = X.loc[y.index]

        # Encode categorical features
        for col in X.select_dtypes(include=["object"]).columns:
            le = LabelEncoder()
            X[col] = le.fit_transform(X[col].astype(str))

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        models = {
            "random_forest": RandomForestRegressor(n_estimators=100, random_state=42),
            "linear_regression": LinearRegression(),
            "gradient_boosting": GradientBoostingRegressor(random_state=42),
        }

        model = models.get(algorithm, models["random_forest"])
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)

        mse = mean_squared_error(y_test, y_pred)
        rmse = math.sqrt(mse)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)

        cv_scores = cross_val_score(model, X, y, cv=5, scoring="r2")

        # Feature importance
        feature_importance = {}
        if hasattr(model, "feature_importances_"):
            for f, imp in sorted(
                zip(features, model.feature_importances_, strict=False), key=lambda x: -x[1]
            ):
                feature_importance[f] = float(imp)

        return {
            "algorithm": algorithm,
            "task_type": "regression",
            "metrics": {
                "r2": float(r2),
                "rmse": float(rmse),
                "mse": float(mse),
                "mae": float(mae),
                "cv_r2_mean": float(cv_scores.mean()),
                "cv_r2_std": float(cv_scores.std()),
            },
            "feature_importance": feature_importance,
            "n_features": len(features),
            "n_samples": int(len(X)),
            "model_summary": (
                f"{algorithm.replace('_', ' ').title()} regressor achieved RÂ²={r2:.4f} "
                f"with RMSE={rmse:.4f} and MAE={mae:.4f}."
            ),
            "explanation": (
                f"The model explains {r2*100:.1f}% of variance in {target}. "
                f"{'Top feature: ' + list(feature_importance.keys())[0] if feature_importance else 'No feature importance available.'}"
            ),
        }

    @staticmethod
    def train_clustering(
        df: pd.DataFrame, features: list[str], n_clusters: int = 3, algorithm: str = "kmeans"
    ) -> dict:
        """Train a clustering model."""
        from sklearn.cluster import AgglomerativeClustering, KMeans
        from sklearn.metrics import silhouette_score
        from sklearn.preprocessing import LabelEncoder, StandardScaler

        X = df[features].dropna()

        # Encode categorical features
        for col in X.select_dtypes(include=["object"]).columns:
            le = LabelEncoder()
            X[col] = le.fit_transform(X[col].astype(str))

        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        models = {
            "kmeans": KMeans(n_clusters=n_clusters, random_state=42, n_init=10),
            "agglomerative": AgglomerativeClustering(n_clusters=n_clusters),
        }

        model = models.get(algorithm, models["kmeans"])
        labels = model.fit_predict(X_scaled)

        silhouette = silhouette_score(X_scaled, labels) if len(set(labels)) > 1 else 0

        # Cluster profiles
        df_with_labels = X.copy()
        df_with_labels["cluster"] = labels
        cluster_profiles = {}
        for c in range(n_clusters):
            cluster_data = df_with_labels[df_with_labels["cluster"] == c]
            cluster_profiles[f"cluster_{c}"] = {
                "size": int(len(cluster_data)),
                "percentage": round(len(cluster_data) / len(X) * 100, 1),
                "mean": {col: float(cluster_data[col].mean()) for col in features},
            }

        return {
            "algorithm": algorithm,
            "task_type": "clustering",
            "metrics": {
                "silhouette_score": float(silhouette),
                "n_clusters": n_clusters,
            },
            "cluster_profiles": cluster_profiles,
            "n_samples": int(len(X)),
            "model_summary": (
                f"{algorithm.replace('_', ' ').title()} identified {n_clusters} clusters "
                f"with silhouette score {silhouette:.4f}. "
                f"{'Good cluster separation.' if silhouette > 0.5 else 'Moderate separation.' if silhouette > 0.25 else 'Poor separation.'}"
            ),
            "explanation": (
                f"Each cluster represents a group of similar data points. "
                f"Cluster sizes: {', '.join(str(p['size']) for p in cluster_profiles.values())}."
            ),
        }

    @staticmethod
    def auto_select_algorithm(df: pd.DataFrame, task_type: str, target: str | None = None) -> dict:
        """AI-recommended algorithm and configuration for the task."""
        recommendations = {
            "classification": [
                {
                    "algorithm": "random_forest",
                    "reason": "Robust, handles non-linear relationships, provides feature importance",
                },
                {
                    "algorithm": "gradient_boosting",
                    "reason": "High accuracy, handles complex patterns",
                },
                {
                    "algorithm": "logistic_regression",
                    "reason": "Interpretable, fast, good baseline",
                },
            ],
            "regression": [
                {"algorithm": "random_forest", "reason": "Robust, non-linear, feature importance"},
                {
                    "algorithm": "gradient_boosting",
                    "reason": "High accuracy for complex relationships",
                },
                {"algorithm": "linear_regression", "reason": "Interpretable, fast, good baseline"},
            ],
            "clustering": [
                {"algorithm": "kmeans", "reason": "Fast, scalable, easy to interpret"},
                {
                    "algorithm": "agglomerative",
                    "reason": "Hierarchical structure, no need to specify k in advance",
                },
            ],
        }

        recs = recommendations.get(task_type, [])
        n_samples = len(df)
        n_features = len(df.select_dtypes(include=[np.number]).columns)

        # Adjust based on data size
        if n_samples > 10000 and task_type == "classification":
            recs[0]["note"] = "For large datasets, consider subsampling or using SGDClassifier"

        return {
            "task_type": task_type,
            "recommendations": recs,
            "data_profile": {
                "n_samples": n_samples,
                "n_features": n_features,
                "has_target": target is not None,
            },
        }

    # â”€â”€â”€ Model Comparison â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def create_comparison(
        self,
        org_id: int,
        dataset_id: int,
        user_id: int,
        name: str,
        task_type: str,
        experiment_ids: list[int],
    ) -> ModelComparison:
        comp = ModelComparison(
            organization_id=org_id,
            dataset_id=dataset_id,
            name=name,
            task_type=task_type,
            experiment_ids=experiment_ids,
            created_by=user_id,
        )
        self.db.add(comp)
        self.db.commit()
        return comp

    def list_comparisons(self, org_id: int) -> list[ModelComparison]:
        return (
            self.db.execute(
                select(ModelComparison)
                .where(ModelComparison.organization_id == org_id)
                .order_by(ModelComparison.created_at.desc())
            )
            .scalars()
            .all()
        )
