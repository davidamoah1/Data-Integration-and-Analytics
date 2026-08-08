"""ML evaluation metrics helpers."""

from __future__ import annotations

import contextlib
from typing import Any

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
    roc_auc_score,
)


def classification_metrics(y_true, y_pred, y_proba=None, average="weighted") -> dict[str, float]:
    """Compute common classification metrics."""
    try:
        metrics = {
            "accuracy": float(accuracy_score(y_true, y_pred)),
            "precision": float(precision_score(y_true, y_pred, average=average, zero_division=0)),
            "recall": float(recall_score(y_true, y_pred, average=average, zero_division=0)),
            "f1": float(f1_score(y_true, y_pred, average=average, zero_division=0)),
        }
    except Exception:
        metrics = {
            "accuracy": float(accuracy_score(y_true, y_pred)),
            "precision": 0.0,
            "recall": 0.0,
            "f1": 0.0,
        }

    if y_proba is not None and len(np.unique(y_true)) == 2:
        with contextlib.suppress(Exception):
            metrics["roc_auc"] = float(roc_auc_score(y_true, y_proba[:, 1]))
    return metrics


def regression_metrics(y_true, y_pred) -> dict[str, float]:
    """Compute common regression metrics."""
    mae = float(mean_absolute_error(y_true, y_pred))
    mse = float(mean_squared_error(y_true, y_pred))
    rmse = float(np.sqrt(mse))
    r2 = float(r2_score(y_true, y_pred))
    return {"mae": mae, "mse": mse, "rmse": rmse, "r2": r2}


def forecast_metrics(y_true, y_pred) -> dict[str, float]:
    """Compute forecasting metrics including MAPE."""
    mae = float(mean_absolute_error(y_true, y_pred))
    mse = float(mean_squared_error(y_true, y_pred))
    rmse = float(np.sqrt(mse))
    mape = float(np.mean(np.abs((y_true - y_pred) / np.maximum(np.abs(y_true), 1e-8))) * 100)
    return {"mae": mae, "mse": mse, "rmse": rmse, "mape": mape}


def clustering_metrics(X, labels) -> dict[str, Any]:
    """Compute clustering summary statistics."""
    from sklearn.metrics import silhouette_score

    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    result = {"n_clusters": n_clusters, "noise_points": int(sum(1 for l in labels if l == -1))}
    if n_clusters > 1 and len(set(labels)) > 1 and len(X) > n_clusters:
        try:
            result["silhouette_score"] = float(silhouette_score(X, labels))
        except Exception:
            result["silhouette_score"] = None
    return result


def anomaly_metrics(labels) -> dict[str, int]:
    """Summarize anomaly detection results."""
    total = int(len(labels))
    anomalies = int(sum(1 for l in labels if l == -1))
    return {
        "total": total,
        "anomalies": anomalies,
        "anomaly_rate": round(anomalies / total, 4) if total else 0.0,
    }
