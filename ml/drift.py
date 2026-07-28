"""Model drift detection utilities.

Supports data drift (feature distribution shift) and prediction drift.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from scipy import stats


def kolmogorov_smirnov_drift(reference: pd.Series, current: pd.Series, threshold: float = 0.05) -> dict[str, Any]:
    """KS test for numeric feature drift."""
    ref = reference.dropna().astype(float)
    cur = current.dropna().astype(float)
    if len(ref) < 2 or len(cur) < 2:
        return {"drift": False, "p_value": None, "statistic": None, "message": "Insufficient samples"}
    statistic, p_value = stats.ks_2samp(ref, cur)
    return {
        "drift": bool(p_value < threshold),
        "p_value": float(p_value),
        "statistic": float(statistic),
        "threshold": threshold,
    }


def chi_squared_drift(reference: pd.Series, current: pd.Series, threshold: float = 0.05) -> dict[str, Any]:
    """Chi-squared test for categorical feature drift."""
    ref_counts = reference.dropna().astype(str).value_counts()
    cur_counts = current.dropna().astype(str).value_counts()
    all_categories = ref_counts.index.union(cur_counts.index)
    if len(all_categories) < 2:
        return {"drift": False, "p_value": None, "statistic": None, "message": "Single category"}
    observed = [cur_counts.get(cat, 0) for cat in all_categories]
    expected_raw = [ref_counts.get(cat, 0) for cat in all_categories]
    total_expected = sum(expected_raw)
    total_observed = sum(observed)
    if total_expected == 0 or total_observed == 0:
        return {"drift": False, "p_value": None, "statistic": None, "message": "Empty contingency"}
    expected = [e * total_observed / total_expected for e in expected_raw]
    statistic, p_value = stats.chisquare(f_obs=observed, f_exp=expected)
    return {
        "drift": bool(p_value < threshold),
        "p_value": float(p_value),
        "statistic": float(statistic),
        "threshold": threshold,
    }


def detect_data_drift(
    reference_df: pd.DataFrame,
    current_df: pd.DataFrame,
    numeric_threshold: float = 0.05,
    categorical_threshold: float = 0.05,
) -> dict[str, Any]:
    """Run drift detection for every column in the reference vs current data."""
    numeric = reference_df.select_dtypes(include=[np.number])
    categorical = reference_df.select_dtypes(include=["object", "category", "bool"])

    features = []
    drifted = 0
    for col in numeric.columns:
        if col in current_df.columns:
            result = kolmogorov_smirnov_drift(reference_df[col], current_df[col], numeric_threshold)
            features.append({"feature": col, "type": "numeric", **result})
            if result["drift"]:
                drifted += 1
    for col in categorical.columns:
        if col in current_df.columns:
            result = chi_squared_drift(reference_df[col], current_df[col], categorical_threshold)
            features.append({"feature": col, "type": "categorical", **result})
            if result["drift"]:
                drifted += 1

    return {
        "drift_detected": drifted > 0,
        "drifted_features": drifted,
        "total_features": len(features),
        "features": features,
    }


def detect_prediction_drift(reference_preds: np.ndarray, current_preds: np.ndarray, threshold: float = 0.05) -> dict[str, Any]:
    """Run KS drift test on prediction distributions."""
    return kolmogorov_smirnov_drift(pd.Series(reference_preds), pd.Series(current_preds), threshold)


def summarize_drift(drift_report: dict[str, Any]) -> dict[str, Any]:
    """Return a high-level summary suitable for dashboards."""
    return {
        "status": "drift_detected" if drift_report["drift_detected"] else "stable",
        "drifted_features": drift_report["drifted_features"],
        "total_features": drift_report["total_features"],
        "drift_ratio": round(drift_report["drifted_features"] / max(drift_report["total_features"], 1), 2),
    }
