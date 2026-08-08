"""ML readiness assessment.

Analyzes a pandas DataFrame and produces a structured report covering data
quality, missing values, outliers, class imbalance, feature completeness, and
recommended target columns and algorithm families.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def assess_ml_readiness(df: pd.DataFrame, target_column: str | None = None) -> dict[str, Any]:
    """Generate an ML readiness report for a dataset.

    Args:
        df: Input dataset.
        target_column: Optional known target column.

    Returns:
        Dictionary with readiness scores, warnings, and recommendations.
    """
    if df.empty:
        return {
            "ready": False,
            "quality_score": 0.0,
            "row_count": 0,
            "column_count": 0,
            "warnings": ["Dataset is empty"],
            "recommendations": ["Upload a non-empty dataset"],
        }

    numeric = df.select_dtypes(include=[np.number])
    categorical = df.select_dtypes(include=["object", "category", "bool"])
    datetime_cols = df.select_dtypes(include=["datetime"])

    total_cells = df.size
    missing = df.isna().sum().sum()
    missing_pct = (missing / total_cells) * 100 if total_cells else 0.0

    # Outliers (IQR per numeric column)
    outlier_summary = {}
    outlier_rows: set[int] = set()
    for col in numeric.columns:
        q1 = numeric[col].quantile(0.25)
        q3 = numeric[col].quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        mask = (numeric[col] < lower) | (numeric[col] > upper)
        idxs = numeric[col][mask].index.tolist()
        outlier_rows.update(idxs)
        outlier_summary[col] = int(mask.sum())

    # Class imbalance
    imbalance_report = {}
    if target_column and target_column in df.columns:
        if (
            df[target_column].dtype in ("object", "category", "bool")
            or df[target_column].nunique() <= 20
        ):
            ratios = df[target_column].value_counts(normalize=True)
            imbalance_report = {
                "classes": int(df[target_column].nunique()),
                "largest_class_ratio": float(ratios.max()),
                "smallest_class_ratio": float(ratios.min()),
                "imbalanced": bool(ratios.max() > 0.8),
            }

    # Feature completeness
    feature_completeness = {
        col: {
            "missing_pct": float(df[col].isna().mean() * 100),
            "unique_count": int(df[col].nunique()),
            "dtype": str(df[col].dtype),
            "completeness": "complete" if df[col].isna().sum() == 0 else "partial",
        }
        for col in df.columns
    }

    # Forecast suitability
    forecast_suitable = False
    if not datetime_cols.empty:
        for col in datetime_cols.columns:
            if (df[col].diff().dt.total_seconds().dropna() > 0).all():
                forecast_suitable = True
                break

    # Quality score (0-100)
    score = 100.0
    score -= min(missing_pct * 1.5, 40)  # missing values
    score -= min(len(outlier_rows) / max(len(df), 1) * 20, 20)  # outliers
    if target_column and imbalance_report.get("imbalanced"):
        score -= 10
    score = max(0.0, score)

    # Recommendations
    recommendations = []
    warnings = []
    if missing_pct > 5:
        warnings.append(f"High missing-value rate: {missing_pct:.1f}%")
        recommendations.append("Use the feature engineering engine to impute missing values.")
    if len(outlier_rows) / max(len(df), 1) > 0.05:
        warnings.append("Significant outlier presence detected.")
        recommendations.append("Review outliers or apply robust scaling.")
    if target_column and imbalance_report.get("imbalanced"):
        warnings.append("Target variable is imbalanced.")
        recommendations.append("Consider stratified sampling, class weighting, or SMOTE.")

    # Algorithm suggestions
    suggested_algorithms = _suggest_algorithms(df, target_column, forecast_suitable)

    # Suggest target variables if not provided
    recommended_targets = []
    if target_column is None:
        for col in numeric.columns:
            unique_ratio = df[col].nunique() / max(len(df), 1)
            if 0.01 < unique_ratio < 0.9:
                recommended_targets.append(col)
        for col in categorical.columns:
            if 1 < df[col].nunique() <= 20:
                recommended_targets.append(col)
        recommended_targets = recommended_targets[:5]

    return {
        "ready": bool(score >= 60 and missing_pct < 20),
        "quality_score": round(score, 2),
        "row_count": int(len(df)),
        "column_count": int(len(df.columns)),
        "missing_values": {"total": int(missing), "percentage": round(missing_pct, 2)},
        "outliers": {"total_rows": int(len(outlier_rows)), "per_column": outlier_summary},
        "class_imbalance": imbalance_report,
        "feature_completeness": feature_completeness,
        "forecast_suitable": forecast_suitable,
        "suggested_algorithms": suggested_algorithms,
        "recommended_targets": recommended_targets,
        "warnings": warnings,
        "recommendations": recommendations,
    }


def _suggest_algorithms(
    df: pd.DataFrame, target_column: str | None, forecast_suitable: bool
) -> list[dict[str, Any]]:
    suggestions = []
    if forecast_suitable:
        suggestions.append(
            {"family": "forecasting", "algorithms": ["ARIMA", "ExponentialSmoothing", "Prophet"]}
        )

    if target_column and target_column in df.columns:
        target = df[target_column]
        unique_ratio = target.nunique() / max(len(df), 1)
        if target.dtype in ("object", "category", "bool") or target.nunique() <= 20:
            suggestions.append(
                {
                    "family": "classification",
                    "algorithms": [
                        "LogisticRegression",
                        "RandomForestClassifier",
                        "GradientBoostingClassifier",
                    ],
                }
            )
        elif np.issubdtype(target.dtype, np.number) and unique_ratio > 0.01:
            suggestions.append(
                {
                    "family": "regression",
                    "algorithms": [
                        "LinearRegression",
                        "RandomForestRegressor",
                        "GradientBoostingRegressor",
                    ],
                }
            )
    else:
        # No target: suggest unsupervised methods
        suggestions.append(
            {"family": "clustering", "algorithms": ["KMeans", "DBSCAN", "AgglomerativeClustering"]}
        )
        suggestions.append(
            {"family": "anomaly_detection", "algorithms": ["IsolationForest", "LocalOutlierFactor"]}
        )
    return suggestions
