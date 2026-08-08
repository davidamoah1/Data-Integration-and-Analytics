"""Base classes for Predictive Analytics.

Defines the core data structures and registry pattern for
industry-specific prediction modules.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd


@dataclass
class ForecastPoint:
    """A single forecast prediction point."""

    date: str
    value: float
    lower_ci: float
    upper_ci: float

    def to_dict(self) -> dict:
        return {
            "date": self.date,
            "value": round(self.value, 2),
            "lower_ci": round(self.lower_ci, 2),
            "upper_ci": round(self.upper_ci, 2),
        }


@dataclass
class ForecastResult:
    """Result of a time series forecast."""

    name: str
    metric: str
    method: str  # "linear", "exponential", "moving_average", "seasonal"
    horizon: int
    predictions: list[ForecastPoint] = field(default_factory=list)
    accuracy: float = 0.0
    accuracy_label: str = "unknown"  # "high", "moderate", "low"
    trend: str = "stable"  # "increasing", "decreasing", "stable"
    trend_pct: float = 0.0
    summary: str = ""
    input_summary: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "metric": self.metric,
            "method": self.method,
            "horizon": self.horizon,
            "predictions": [p.to_dict() for p in self.predictions],
            "accuracy": round(self.accuracy, 4),
            "accuracy_label": self.accuracy_label,
            "trend": self.trend,
            "trend_pct": round(self.trend_pct, 2),
            "summary": self.summary,
            "input_summary": self.input_summary,
        }


@dataclass
class PredictionResult:
    """Result of a regression-based prediction."""

    name: str
    target: str
    method: str  # "linear_regression", "multivariate"
    r_squared: float = 0.0
    predictions: list[dict] = field(default_factory=list)
    feature_importance: dict = field(default_factory=dict)
    summary: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "target": self.target,
            "method": self.method,
            "r_squared": round(self.r_squared, 4),
            "predictions": self.predictions,
            "feature_importance": self.feature_importance,
            "summary": self.summary,
        }


@dataclass
class RiskAssessment:
    """Result of a risk classification."""

    name: str
    target: str
    method: str  # "rule_based", "logistic"
    high_risk_count: int = 0
    medium_risk_count: int = 0
    low_risk_count: int = 0
    risk_factors: list[str] = field(default_factory=list)
    at_risk_items: list[dict] = field(default_factory=list)
    summary: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "target": self.target,
            "method": self.method,
            "high_risk_count": self.high_risk_count,
            "medium_risk_count": self.medium_risk_count,
            "low_risk_count": self.low_risk_count,
            "risk_factors": self.risk_factors,
            "at_risk_items": self.at_risk_items[:20],
            "summary": self.summary,
        }


@dataclass
class PredictiveIntelligenceResult:
    """Complete predictive analytics result for a dataset."""

    industry: str
    forecasts: list[ForecastResult] = field(default_factory=list)
    predictions: list[PredictionResult] = field(default_factory=list)
    risk_assessments: list[RiskAssessment] = field(default_factory=list)
    summary: str = ""

    def to_dict(self) -> dict:
        return {
            "industry": self.industry,
            "forecasts": [f.to_dict() for f in self.forecasts],
            "predictions": [p.to_dict() for p in self.predictions],
            "risk_assessments": [r.to_dict() for r in self.risk_assessments],
            "summary": self.summary,
        }


class PredictiveAnalyticsBase:
    """Base class for industry-specific predictive analytics."""

    def analyze(self, df: pd.DataFrame, col_mapping: dict) -> PredictiveIntelligenceResult:
        """Run predictive analytics. Override in subclasses."""
        raise NotImplementedError

    # ── Helpers ──────────────────────────────────────────

    @staticmethod
    def _find_col(df: pd.DataFrame, col_mapping: dict, entity_keys: list[str]) -> str | None:
        """Find a column by entity key mapping or name."""
        for col, entity in col_mapping.items():
            if entity in entity_keys and col in df.columns:
                return col
        lower_map = {c.lower(): c for c in df.columns}
        for key in entity_keys:
            if key in lower_map:
                return lower_map[key]
            for col_lower, col in lower_map.items():
                if key in col_lower:
                    return col
        return None

    @staticmethod
    def _find_numeric_col(
        df: pd.DataFrame, col_mapping: dict, entity_keys: list[str]
    ) -> str | None:
        """Find a numeric column by entity key or name."""
        for col, entity in col_mapping.items():
            if (
                entity in entity_keys
                and col in df.columns
                and pd.api.types.is_numeric_dtype(df[col])
            ):
                return col
        lower_map = {c.lower(): c for c in df.columns}
        for key in entity_keys:
            if key in lower_map and pd.api.types.is_numeric_dtype(df[lower_map[key]]):
                return lower_map[key]
            for col_lower, col in lower_map.items():
                if key in col_lower and pd.api.types.is_numeric_dtype(df[col]):
                    return col
        return None

    @staticmethod
    def _find_date_col(df: pd.DataFrame, col_mapping: dict) -> str | None:
        """Find the date column."""
        for col, entity in col_mapping.items():
            if entity == "date" and col in df.columns:
                return col
        for c in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[c]):
                return c
        lower_map = {c.lower(): c for c in df.columns}
        for name in (
            "date",
            "order_date",
            "visit_date",
            "admission_date",
            "created_at",
            "record_date",
        ):
            if name in lower_map:
                return lower_map[name]
        return None


class PredictiveAnalyticsRegistry:
    """Registry for industry-specific predictive analytics modules."""

    _registry: dict[str, type[PredictiveAnalyticsBase]] = {}

    @classmethod
    def register(cls, industry: str, module_class: type[PredictiveAnalyticsBase]) -> None:
        cls._registry[industry] = module_class

    @classmethod
    def get(cls, industry: str) -> PredictiveAnalyticsBase | None:
        module_class = cls._registry.get(industry)
        if module_class:
            return module_class()
        return None

    @classmethod
    def analyze(
        cls, industry: str, df: pd.DataFrame, col_mapping: dict
    ) -> PredictiveIntelligenceResult:
        module = cls.get(industry)
        if module:
            return module.analyze(df, col_mapping)
        return PredictiveIntelligenceResult(
            industry=industry, summary="No predictive module for this industry."
        )

    @classmethod
    def registered_industries(cls) -> list[str]:
        return list(cls._registry.keys())
