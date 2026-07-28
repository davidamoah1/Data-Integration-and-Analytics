"""Anomaly detection engine."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor

from ml.metrics import anomaly_metrics


class AnomalyDetectionEngine:
    """Detect anomalies in a numeric DataFrame using supported algorithms."""

    ALGORITHMS = {
        "isolation_forest": IsolationForest,
        "local_outlier_factor": LocalOutlierFactor,
    }

    def __init__(self, algorithm: str = "isolation_forest", **kwargs: Any) -> None:
        if algorithm not in self.ALGORITHMS:
            raise ValueError(f"Unknown anomaly algorithm: {algorithm}")
        self.algorithm = algorithm
        self.kwargs = kwargs
        self.model: Any = None

    def detect(self, df: pd.DataFrame) -> dict[str, Any]:
        """Return anomaly labels, scores, and summary."""
        numeric = df.select_dtypes(include=[np.number]).dropna()
        if numeric.empty:
            return {"status": "failed", "error": "No numeric columns available"}

        defaults = {"random_state": 42, "contamination": "auto"} if self.algorithm == "isolation_forest" else {"n_neighbors": 20, "contamination": "auto"}
        params = {**defaults, **self.kwargs}
        estimator_class = self.ALGORITHMS[self.algorithm]

        self.model = estimator_class(**params)
        if self.algorithm == "local_outlier_factor":
            labels = self.model.fit_predict(numeric)
        else:
            self.model.fit(numeric)
            labels = self.model.predict(numeric)

        scores = self.model.score_samples(numeric) if hasattr(self.model, "score_samples") else [None] * len(numeric)
        summary = anomaly_metrics(labels)
        summary["status"] = "completed"
        summary["algorithm"] = self.algorithm

        result_df = numeric.copy()
        result_df["anomaly"] = labels
        result_df["anomaly_score"] = scores

        return {
            **summary,
            "anomaly_indices": result_df.index[labels == -1].tolist(),
            "anomaly_count": int(summary["anomalies"]),
            "sample": result_df.head(20).to_dict(orient="records"),
        }


def detect_spikes(df: pd.DataFrame, column: str, threshold: float = 3.0) -> dict[str, Any]:
    """Detect points more than `threshold` standard deviations from the mean."""
    values = df[column].dropna()
    if values.empty or values.std() == 0:
        return {"status": "failed", "error": f"Column {column} has no variance"}
    z_scores = (values - values.mean()) / values.std()
    mask = np.abs(z_scores) > threshold
    return {
        "status": "completed",
        "algorithm": "z_score",
        "threshold": threshold,
        "anomaly_count": int(mask.sum()),
        "anomaly_indices": values[mask].index.tolist(),
        "values": values[mask].tolist(),
    }
