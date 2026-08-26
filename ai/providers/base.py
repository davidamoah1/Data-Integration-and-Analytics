"""Base AI provider interface â€” all providers implement this contract."""

from abc import ABC, abstractmethod
from collections.abc import Generator
from dataclasses import dataclass, field


@dataclass
class LLMResponse:
    """Standardized response from any LLM provider."""

    content: str
    provider: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    finish_reason: str = "stop"
    raw_response: dict = field(default_factory=dict)


class BaseProvider(ABC):
    """Abstract base class for all AI providers."""

    def __init__(self, api_key: str = "", base_url: str = "", model: str = "", **kwargs):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.config = kwargs

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider identifier (e.g., 'openai', 'gemini')."""
        ...

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable provider name."""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is configured and reachable."""
        ...

    @abstractmethod
    def chat(
        self,
        messages: list[dict],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: bool = False,
    ) -> LLMResponse | Generator[str, None, None]:
        """Send a chat completion request.

        Args:
            messages: List of {"role": "user|assistant|system", "content": "..."} dicts.
            model: Model to use (falls back to default).
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.
            stream: If True, returns a generator yielding text chunks.

        Returns:
            LLMResponse if stream=False, or Generator yielding str chunks if stream=True.
        """
        ...

    @abstractmethod
    def list_models(self) -> list[str]:
        """List available models for this provider."""
        ...

    def estimate_cost(self, total_tokens: int, model: str) -> float:
        """Estimate cost for a request. Override in subclasses for accuracy."""
        return 0.0
