"""AI Provider Manager — registry, routing, and lifecycle management for all AI providers.

Administrators can configure providers via System Settings or the API.
The manager loads provider configs from the database and environment,
and routes requests to the appropriate provider.
"""

from typing import Optional, Generator
from sqlalchemy.orm import Session as DbSession

from ai.providers.base import BaseProvider, LLMResponse
from ai.providers.openai_provider import OpenAIProvider
from ai.providers.gemini_provider import GeminiProvider
from ai.providers.deepseek_provider import DeepSeekProvider
from ai.providers.glm_provider import GLMProvider
from ai.providers.claude_provider import ClaudeProvider
from ai.providers.local_provider import LocalLLMProvider
from ai.models import AIProviderConfig
from ai.config import AI_DEFAULT_PROVIDER, AI_DEFAULT_MODEL, AI_MAX_TOKENS, AI_TEMPERATURE


# --- Provider Registry ------------------------------------------------------

_PROVIDER_CLASSES: dict[str, type[BaseProvider]] = {
    "openai": OpenAIProvider,
    "gemini": GeminiProvider,
    "deepseek": DeepSeekProvider,
    "glm": GLMProvider,
    "claude": ClaudeProvider,
    "local": LocalLLMProvider,
}


def register_provider_class(name: str, cls: type[BaseProvider]):
    """Register a custom provider class."""
    _PROVIDER_CLASSES[name] = cls


def list_available_provider_types() -> list[dict]:
    """List all provider types that can be configured."""
    return [
        {"name": name, "display_name": cls("").display_name, "is_builtin": True}
        for name, cls in _PROVIDER_CLASSES.items()
    ]


# --- Provider Manager -------------------------------------------------------

class ProviderManager:
    """Manages provider lifecycle, configuration, and request routing."""

    def __init__(self, db: Optional[DbSession] = None):
        self.db = db
        self._cache: dict[str, BaseProvider] = {}

    def _load_config_from_db(self, provider_name: str) -> Optional[AIProviderConfig]:
        """Load provider configuration from the database."""
        if not self.db:
            return None
        return self.db.query(AIProviderConfig).filter(
            AIProviderConfig.provider_name == provider_name,
            AIProviderConfig.is_active == True,
        ).first()

    def get_provider(self, provider_name: Optional[str] = None) -> BaseProvider:
        """Get a configured provider instance.

        Args:
            provider_name: Specific provider to get. If None, uses default.

        Returns:
            Configured BaseProvider instance.

        Raises:
            ValueError if provider is not found or not configured.
        """
        provider_name = provider_name or AI_DEFAULT_PROVIDER

        # Check cache
        cache_key = f"{provider_name}:{id(self.db)}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Get provider class
        cls = _PROVIDER_CLASSES.get(provider_name)
        if not cls:
            raise ValueError(f"Unknown provider: {provider_name}")

        # Try loading config from DB
        db_config = self._load_config_from_db(provider_name)

        if db_config:
            provider = cls(
                api_key=db_config.api_key_encrypted or "",
                base_url=db_config.api_base_url or "",
                model=db_config.default_model or AI_DEFAULT_MODEL,
                max_tokens=db_config.max_tokens,
                temperature=db_config.temperature,
            )
        else:
            # Fall back to environment variables
            provider = cls()

        self._cache[cache_key] = provider
        return provider

    def get_default_provider(self) -> BaseProvider:
        """Get the default configured provider."""
        if self.db:
            default_config = self.db.query(AIProviderConfig).filter(
                AIProviderConfig.is_default == True,
                AIProviderConfig.is_active == True,
            ).first()
            if default_config:
                return self.get_provider(default_config.provider_name)
        return self.get_provider(AI_DEFAULT_PROVIDER)

    def chat(self, messages: list[dict], provider_name: Optional[str] = None,
             model: Optional[str] = None, temperature: Optional[float] = None,
             max_tokens: Optional[int] = None, stream: bool = False
             ) -> LLMResponse | Generator[str, None, None]:
        """Send a chat request through the appropriate provider.

        Args:
            messages: List of message dicts.
            provider_name: Override provider.
            model: Override model.
            temperature: Override temperature.
            max_tokens: Override max tokens.
            stream: If True, returns a generator.

        Returns:
            LLMResponse or Generator.
        """
        provider = self.get_provider(provider_name)
        return provider.chat(
            messages=messages,
            model=model,
            temperature=temperature if temperature is not None else AI_TEMPERATURE,
            max_tokens=max_tokens or AI_MAX_TOKENS,
            stream=stream,
        )

    def list_providers(self) -> list[dict]:
        """List all configured providers with their status."""
        result = []
        for name, cls in _PROVIDER_CLASSES.items():
            provider = cls()
            db_config = self._load_config_from_db(name) if self.db else None
            result.append({
                "name": name,
                "display_name": provider.display_name,
                "is_available": provider.is_available(),
                "is_active": db_config.is_active if db_config else False,
                "is_default": db_config.is_default if db_config else (name == AI_DEFAULT_PROVIDER),
                "default_model": db_config.default_model if db_config else provider.model,
                "available_models": provider.list_models(),
            })
        return result

    def test_provider(self, provider_name: str) -> dict:
        """Test a provider connection with a simple message."""
        try:
            provider = self.get_provider(provider_name)
            if not provider.is_available():
                return {"success": False, "error": "Provider not available (missing API key?)"}
            resp = provider.chat(
                messages=[{"role": "user", "content": "Hello, respond with 'OK'."}],
                max_tokens=10,
            )
            return {
                "success": True,
                "response": resp.content[:100],
                "model": resp.model,
                "tokens_used": resp.total_tokens,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
