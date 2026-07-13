"""AI Model Router — routes requests to the best provider/model based on task type.

Considers:
- Task complexity (simple chat vs. code generation vs. reasoning)
- Provider availability and configuration
- Cost optimization
- User/admin preferences
"""

from typing import Tuple, Optional
from sqlalchemy.orm import Session as DbSession

from ai.models import AIProviderConfig
from ai.config import AI_DEFAULT_PROVIDER, AI_DEFAULT_MODEL


# Task-to-model mapping recommendations
TASK_MODEL_PREFERENCES: dict[str, list[tuple[str, str]]] = {
    # assistant_type -> list of (provider, model) in priority order
    "data_copilot": [
        ("openai", "gpt-4o-mini"),
        ("gemini", "gemini-1.5-flash"),
        ("deepseek", "deepseek-chat"),
        ("glm", "glm-4-flash"),
        ("claude", "claude-3-haiku-20240307"),
        ("local", "llama3"),
    ],
    "etl_copilot": [
        ("openai", "gpt-4o"),
        ("claude", "claude-3-5-sonnet-20241022"),
        ("gemini", "gemini-1.5-pro"),
        ("deepseek", "deepseek-coder"),
        ("glm", "glm-4"),
        ("local", "llama3"),
    ],
    "dashboard_copilot": [
        ("openai", "gpt-4o-mini"),
        ("gemini", "gemini-1.5-flash"),
        ("deepseek", "deepseek-chat"),
        ("glm", "glm-4-flash"),
        ("claude", "claude-3-haiku-20240307"),
        ("local", "llama3"),
    ],
    "report_copilot": [
        ("openai", "gpt-4o"),
        ("claude", "claude-3-5-sonnet-20241022"),
        ("gemini", "gemini-1.5-pro"),
        ("deepseek", "deepseek-chat"),
        ("glm", "glm-4"),
        ("local", "llama3"),
    ],
    "decision_copilot": [
        ("openai", "gpt-4o"),
        ("claude", "claude-3-5-sonnet-20241022"),
        ("gemini", "gemini-1.5-pro"),
        ("deepseek", "deepseek-reasoner"),
        ("glm", "glm-4"),
        ("local", "llama3"),
    ],
    "forecast_copilot": [
        ("openai", "gpt-4o-mini"),
        ("gemini", "gemini-1.5-flash"),
        ("deepseek", "deepseek-chat"),
        ("glm", "glm-4-flash"),
        ("claude", "claude-3-haiku-20240307"),
        ("local", "llama3"),
    ],
    "quality_copilot": [
        ("openai", "gpt-4o"),
        ("claude", "claude-3-5-sonnet-20241022"),
        ("gemini", "gemini-1.5-pro"),
        ("deepseek", "deepseek-chat"),
        ("glm", "glm-4"),
        ("local", "llama3"),
    ],
    "sql_copilot": [
        ("openai", "gpt-4o"),
        ("claude", "claude-3-5-sonnet-20241022"),
        ("gemini", "gemini-1.5-pro"),
        ("deepseek", "deepseek-coder"),
        ("glm", "glm-4"),
        ("local", "llama3"),
    ],
}


class ModelRouter:
    """Routes AI requests to the best available provider and model."""

    def __init__(self, db: Optional[DbSession] = None):
        self.db = db

    def route(self, assistant_type: str, user_message: str = "") -> tuple[str, str]:
        """Determine the best provider and model for a request.

        Args:
            assistant_type: The type of assistant making the request.
            user_message: The user's message (for complexity analysis).

        Returns:
            Tuple of (provider_name, model_name).
        """
        # Check if admin has configured a default provider in DB
        if self.db:
            default_config = self.db.query(AIProviderConfig).filter(
                AIProviderConfig.is_default == True,
                AIProviderConfig.is_active == True,
            ).first()
            if default_config:
                return default_config.provider_name, default_config.default_model or AI_DEFAULT_MODEL

        # Get preferences for this assistant type
        preferences = TASK_MODEL_PREFERENCES.get(assistant_type, TASK_MODEL_PREFERENCES["data_copilot"])

        # Check which providers are available (have API keys configured)
        if self.db:
            active_providers = {
                p.provider_name for p in self.db.query(AIProviderConfig).filter(
                    AIProviderConfig.is_active == True,
                ).all()
            }
        else:
            # Fall back to environment-based availability
            from ai.config import (
                OPENAI_API_KEY, GEMINI_API_KEY, DEEPSEEK_API_KEY,
                GLM_API_KEY, CLAUDE_API_KEY,
            )
            active_providers = set()
            if OPENAI_API_KEY:
                active_providers.add("openai")
            if GEMINI_API_KEY:
                active_providers.add("gemini")
            if DEEPSEEK_API_KEY:
                active_providers.add("deepseek")
            if GLM_API_KEY:
                active_providers.add("glm")
            if CLAUDE_API_KEY:
                active_providers.add("claude")
            active_providers.add("local")  # Local is always potentially available

        # Find the first available provider from preferences
        for provider_name, model in preferences:
            if provider_name in active_providers or not active_providers:
                return provider_name, model

        # Fall back to default
        return AI_DEFAULT_PROVIDER, AI_DEFAULT_MODEL

    def get_recommendations(self, assistant_type: str) -> list[dict]:
        """Get model recommendations for an assistant type."""
        preferences = TASK_MODEL_PREFERENCES.get(assistant_type, [])
        return [
            {"provider": p, "model": m, "priority": i + 1}
            for i, (p, m) in enumerate(preferences)
        ]
