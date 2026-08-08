"""Automated feature engineering.

Provides a scikit-learn-compatible pipeline builder that handles missing values,
encoders, scalers, date extraction, rolling/lag statistics, polynomial features,
interactions, and feature selection.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.feature_selection import SelectKBest, f_classif, f_regression
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MinMaxScaler, OneHotEncoder, PolynomialFeatures, StandardScaler


def build_feature_pipeline(
    numeric_columns: list[str],
    categorical_columns: list[str],
    datetime_columns: list[str] | None = None,
    scaling: str = "standard",
    polynomial_degree: int = 0,
    interaction_only: bool = False,
    k_best: int = 0,
    target_type: str = "regression",
) -> tuple[ColumnTransformer, Pipeline | None]:
    """Build a sklearn ColumnTransformer plus optional feature-selection pipeline.

    Returns:
        A tuple of (transformer, optional_pipeline). The optional pipeline wraps
        the transformer with polynomial expansion and/or k-best selection.
    """
    transformers = []

    if numeric_columns:
        numeric_steps = [("imputer", SimpleImputer(strategy="median"))]
        if scaling == "standard":
            numeric_steps.append(("scaler", StandardScaler()))
        elif scaling == "minmax":
            numeric_steps.append(("scaler", MinMaxScaler()))
        transformers.append(("num", Pipeline(numeric_steps), numeric_columns))

    if categorical_columns:
        transformers.append(
            (
                "cat",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
                    ]
                ),
                categorical_columns,
            )
        )

    # Datetime transformer: extracts date components separately.
    if datetime_columns:
        transformers.append(
            (
                "dt",
                Pipeline(
                    [
                        ("extract", DatetimeFeatureExtractor(datetime_columns)),
                    ]
                ),
                datetime_columns,
            )
        )

    if not transformers:
        raise ValueError("At least one feature column group must be provided")

    transformer = ColumnTransformer(transformers, remainder="drop")
    steps: list[Any] = [("preprocess", transformer)]

    if polynomial_degree and polynomial_degree > 1:
        steps.append(
            (
                "poly",
                PolynomialFeatures(
                    degree=polynomial_degree, interaction_only=interaction_only, include_bias=False
                ),
            )
        )

    if k_best and k_best > 0:
        score_func = f_classif if target_type == "classification" else f_regression
        steps.append(("select", SelectKBest(score_func=score_func, k=min(k_best, 1))))

    pipeline = Pipeline(steps) if len(steps) > 1 else None
    return transformer, pipeline


class DatetimeFeatureExtractor:
    """Custom sklearn-compatible transformer to extract date components."""

    def __init__(self, columns: list[str]) -> None:
        self.columns = columns

    def fit(self, X: pd.DataFrame, y=None):  # noqa: D401, ANN001
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:  # noqa: D401
        if isinstance(X, np.ndarray):
            X = pd.DataFrame(X, columns=self.columns)
        frames = []
        for col in self.columns:
            if col in X.columns:
                s = pd.to_datetime(X[col], errors="coerce")
                frames.append(
                    pd.DataFrame(
                        {
                            f"{col}_year": s.dt.year,
                            f"{col}_month": s.dt.month,
                            f"{col}_day": s.dt.day,
                            f"{col}_dayofweek": s.dt.dayofweek,
                            f"{col}_quarter": s.dt.quarter,
                        }
                    )
                )
        return pd.concat(frames, axis=1)


def create_rolling_features(
    df: pd.DataFrame,
    column: str,
    windows: list[int] = (7, 14, 30),
    aggregations: tuple[str, ...] = ("mean", "std", "min", "max"),
) -> pd.DataFrame:
    """Append rolling-window statistics for a numeric time-series column."""
    result = df.copy()
    for window in windows:
        for agg in aggregations:
            result[f"{column}_roll{window}_{agg}"] = (
                result[column].rolling(window=window, min_periods=1).agg(agg)
            )
    return result


def create_lag_features(
    df: pd.DataFrame, column: str, lags: list[int] = (1, 2, 3, 7)
) -> pd.DataFrame:
    """Append lagged values for a numeric column."""
    result = df.copy()
    for lag in lags:
        result[f"{column}_lag{lag}"] = result[column].shift(lag)
    return result


class FeatureEngineer:
    """High-level feature engineering orchestrator that records metadata."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or {}
        self.transformer: ColumnTransformer | None = None
        self.pipeline: Pipeline | None = None
        self.feature_names_out: list[str] = []
        self.log: list[dict[str, Any]] = []

    def fit_transform(self, df: pd.DataFrame, target: pd.Series | None = None) -> pd.DataFrame:
        """Fit the feature pipeline and transform the data."""
        numeric = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical = df.select_dtypes(include=["object", "category", "bool"]).columns.tolist()
        datetime_cols = df.select_dtypes(include=["datetime"]).columns.tolist()

        if target is not None and target.name in numeric:
            numeric.remove(target.name)

        rolling_col = self.config.get("rolling_column")
        if rolling_col and rolling_col in numeric:
            df = create_rolling_features(
                df,
                rolling_col,
                windows=self.config.get("rolling_windows", [7, 14, 30]),
            )
            self.log.append({"operation": "rolling_features", "column": rolling_col})

        lag_col = self.config.get("lag_column")
        if lag_col and lag_col in numeric:
            df = create_lag_features(
                df,
                lag_col,
                lags=self.config.get("lag_periods", [1, 2, 3, 7]),
            )
            self.log.append({"operation": "lag_features", "column": lag_col})

        # Refresh column lists after derived features
        numeric = df.select_dtypes(include=[np.number]).columns.tolist()
        if target is not None and target.name in numeric:
            numeric.remove(target.name)

        self.transformer, self.pipeline = build_feature_pipeline(
            numeric_columns=numeric,
            categorical_columns=categorical,
            datetime_columns=datetime_cols,
            scaling=self.config.get("scaling", "standard"),
            polynomial_degree=self.config.get("polynomial_degree", 0),
            interaction_only=self.config.get("interaction_only", False),
            k_best=self.config.get("k_best", 0),
            target_type=self.config.get("target_type", "regression"),
        )

        active_pipeline = self.pipeline if self.pipeline else self.transformer
        X_transformed = active_pipeline.fit_transform(df, target)

        # Build feature names from transformers
        self.feature_names_out = self._derive_feature_names(active_pipeline)
        output = pd.DataFrame(X_transformed, columns=self.feature_names_out)
        self.log.append(
            {
                "operation": "fit_transform",
                "input_columns": df.columns.tolist(),
                "output_columns": output.columns.tolist(),
                "transformer": str(active_pipeline),
            }
        )
        return output

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform new data using a fitted pipeline."""
        if self.pipeline is None and self.transformer is None:
            raise RuntimeError("FeatureEngineer has not been fitted")
        active_pipeline = self.pipeline if self.pipeline else self.transformer
        X_transformed = active_pipeline.transform(df)
        return pd.DataFrame(X_transformed, columns=self.feature_names_out)

    def _derive_feature_names(self, active_pipeline) -> list[str]:
        try:
            return active_pipeline.get_feature_names_out().tolist()
        except Exception:
            return [
                f"feature_{i}" for i in range(active_pipeline.transform(pd.DataFrame()).shape[1])
            ]


def auto_clean(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Apply basic automated cleaning and return the cleaned DataFrame plus a log."""
    log = []
    # Drop fully empty rows/columns
    before = df.shape
    df = df.dropna(axis=0, how="all").dropna(axis=1, how="all")
    log.append(
        {"operation": "drop_empty", "shape_before": list(before), "shape_after": list(df.shape)}
    )

    # Impute numeric with median
    numeric = df.select_dtypes(include=[np.number])
    for col in numeric.columns:
        if numeric[col].isna().any():
            median = numeric[col].median()
            df[col] = df[col].fillna(median)
            log.append(
                {
                    "operation": "impute_median",
                    "column": col,
                    "value": float(median) if pd.notna(median) else None,
                }
            )

    # Impute categorical with mode
    categorical = df.select_dtypes(include=["object", "category"])
    for col in categorical.columns:
        if df[col].isna().any():
            mode = df[col].mode().iloc[0] if not df[col].mode().empty else "Unknown"
            df[col] = df[col].fillna(mode)
            log.append({"operation": "impute_mode", "column": col, "value": str(mode)})

    return df, {"operations": log}
