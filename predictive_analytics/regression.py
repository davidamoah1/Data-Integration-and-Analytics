"""Regression Predictor.

Predicts continuous values using linear regression.
Used for:
  - Crop yield prediction (based on rainfall, fertilizer, area)
  - Demand prediction (based on price, season, promotions)
  - Revenue prediction (based on multiple features)
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from predictive_analytics.base import PredictionResult


class RegressionPredictor:
    """Linear regression-based prediction engine."""

    @staticmethod
    def predict(
        df: pd.DataFrame,
        target_col: str,
        feature_cols: list[str] | None = None,
        name: str | None = None,
    ) -> PredictionResult | None:
        """Run a linear regression prediction.

        Args:
            df: DataFrame with the data.
            target_col: Column to predict.
            feature_cols: Columns to use as features. If None, uses all
                          numeric columns except target.
            name: Display name.

        Returns:
            PredictionResult with R², feature importance, and sample predictions.
        """
        if target_col not in df.columns:
            return None
        if not pd.api.types.is_numeric_dtype(df[target_col]):
            return None

        if feature_cols is None:
            feature_cols = [
                c for c in df.columns
                if c != target_col and pd.api.types.is_numeric_dtype(df[c])
            ]
        else:
            feature_cols = [c for c in feature_cols if c in df.columns and pd.api.types.is_numeric_dtype(df[c])]

        if len(feature_cols) == 0:
            return None

        # Prepare data
        data = df[[target_col] + feature_cols].dropna()
        if len(data) < 10:
            return None

        y = data[target_col].values
        X = data[feature_cols].values

        # Add intercept
        X_with_intercept = np.column_stack([np.ones(len(X)), X])

        # Solve least squares
        try:
            coeffs, residuals, _, _ = np.linalg.lstsq(X_with_intercept, y, rcond=None)
        except Exception:
            return None

        # R²
        y_pred = X_with_intercept @ coeffs
        ss_res = float(np.sum((y - y_pred) ** 2))
        ss_tot = float(np.sum((y - np.mean(y)) ** 2))
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

        # Feature importance (normalized absolute coefficients)
        feature_coeffs = coeffs[1:]  # exclude intercept
        total_abs = float(np.sum(np.abs(feature_coeffs)))
        if total_abs > 0:
            importance = {
                feature_cols[i]: round(float(abs(feature_coeffs[i]) / total_abs), 4)
                for i in range(len(feature_cols))
            }
        else:
            importance = {col: 0.0 for col in feature_cols}

        # Generate predictions for sample rows
        sample_predictions = []
        sample_size = min(10, len(data))
        sample_idx = np.linspace(0, len(data) - 1, sample_size, dtype=int)
        for idx in sample_idx:
            actual = float(y[idx])
            predicted = float(y_pred[idx])
            sample_predictions.append({
                "index": int(idx),
                "actual": round(actual, 2),
                "predicted": round(predicted, 2),
                "error": round(actual - predicted, 2),
            })

        name = name or f"{target_col.replace('_', ' ').title()} Prediction"

        # Summary
        accuracy_label = "high" if r_squared >= 0.7 else "moderate" if r_squared >= 0.4 else "low"
        top_features = sorted(importance.items(), key=lambda x: x[1], reverse=True)[:3]
        feature_str = ", ".join(f"{k} ({v:.1%})" for k, v in top_features)
        summary = (
            f"{name}: R²={r_squared:.2f} ({accuracy_label} accuracy). "
            f"Key factors: {feature_str}."
        )

        return PredictionResult(
            name=name,
            target=target_col,
            method="linear_regression",
            r_squared=r_squared,
            predictions=sample_predictions,
            feature_importance=importance,
            summary=summary,
        )
