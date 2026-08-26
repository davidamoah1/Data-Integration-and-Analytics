"""AI-ready hooks architecture â€” interfaces for future AI features.

These are abstract interfaces that future AI implementations can plug into.
No AI logic is implemented here â€” only the architecture and data contracts.
"""

from abc import ABC, abstractmethod

import pandas as pd


class AIHook(ABC):
    """Base interface for all AI hooks."""

    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if the AI backend is configured and available."""
        ...


class AICleaningSuggestionsHook(AIHook):
    """Suggests cleaning operations for a dirty dataset."""

    @property
    def name(self) -> str:
        return "ai_cleaning_suggestions"

    def is_available(self) -> bool:
        return False

    def suggest(self, df: pd.DataFrame, quality_report: dict) -> list[dict]:
        """Return a list of cleaning suggestions.

        Each suggestion: {"action": str, "column": str, "description": str, "confidence": float}
        """
        return []


class AIColumnMappingHook(AIHook):
    """Suggests column mappings between source and target schemas."""

    @property
    def name(self) -> str:
        return "ai_column_mapping"

    def is_available(self) -> bool:
        return False

    def suggest_mapping(self, source_columns: list[str], target_columns: list[str]) -> dict:
        """Return {"source_col": "target_col", ...} mapping."""
        return {}


class AIDataClassificationHook(AIHook):
    """Classifies columns by data type and sensitivity."""

    @property
    def name(self) -> str:
        return "ai_data_classification"

    def is_available(self) -> bool:
        return False

    def classify(self, df: pd.DataFrame) -> dict:
        """Return {"column": {"type": str, "sensitivity": str, "description": str}}"""
        return {}


class AIPipelineSuggestionsHook(AIHook):
    """Suggests pipeline configurations based on data characteristics."""

    @property
    def name(self) -> str:
        return "ai_pipeline_suggestions"

    def is_available(self) -> bool:
        return False

    def suggest(self, df: pd.DataFrame, source_type: str) -> list[dict]:
        """Return list of suggested pipeline steps."""
        return []


class AIErrorExplanationHook(AIHook):
    """Explains ETL errors in human-readable terms."""

    @property
    def name(self) -> str:
        return "ai_error_explanation"

    def is_available(self) -> bool:
        return False

    def explain(self, error: str, context: dict) -> str:
        """Return a human-readable explanation of the error."""
        return ""


class AITransformationRecommendationsHook(AIHook):
    """Recommends transformations based on data profiling results."""

    @property
    def name(self) -> str:
        return "ai_transformation_recommendations"

    def is_available(self) -> bool:
        return False

    def recommend(self, profile: dict) -> list[dict]:
        """Return list of recommended transformations."""
        return []


# --- Registry ---------------------------------------------------------------

AI_HOOKS: dict[str, AIHook] = {
    "cleaning_suggestions": AICleaningSuggestionsHook(),
    "column_mapping": AIColumnMappingHook(),
    "data_classification": AIDataClassificationHook(),
    "pipeline_suggestions": AIPipelineSuggestionsHook(),
    "error_explanation": AIErrorExplanationHook(),
    "transformation_recommendations": AITransformationRecommendationsHook(),
}


def get_ai_hook(name: str) -> AIHook | None:
    """Get an AI hook by name. Returns None if not found."""
    return AI_HOOKS.get(name)


def register_ai_hook(name: str, hook: AIHook):
    """Register a custom AI hook implementation."""
    AI_HOOKS[name] = hook


def list_ai_hooks() -> list[dict]:
    """List all available AI hooks and their availability status."""
    return [{"name": k, "available": h.is_available()} for k, h in AI_HOOKS.items()]
