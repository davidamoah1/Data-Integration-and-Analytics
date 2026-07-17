"""Claude (Anthropic) provider — supports Claude 3.5 Sonnet, Claude 3 Haiku."""

import json
from collections.abc import Generator

import requests

from ai.config import AI_COST_PER_1K, AI_REQUEST_TIMEOUT, CLAUDE_API_KEY, CLAUDE_BASE_URL
from ai.providers.base import BaseProvider, LLMResponse


class ClaudeProvider(BaseProvider):
    """Anthropic Claude AI provider."""

    def __init__(
        self,
        api_key: str = "",
        base_url: str = "",
        model: str = "claude-3-5-sonnet-20241022",
        **kwargs,
    ):
        super().__init__(
            api_key=api_key or CLAUDE_API_KEY,
            base_url=base_url or CLAUDE_BASE_URL,
            model=model,
            **kwargs,
        )

    @property
    def name(self) -> str:
        return "claude"

    @property
    def display_name(self) -> str:
        return "Claude (Anthropic)"

    def is_available(self) -> bool:
        return bool(self.api_key)

    def _convert_messages(self, messages: list[dict]) -> tuple[str, list[dict]]:
        """Convert OpenAI-style messages to Claude format."""
        system_parts = []
        converted = []
        for msg in messages:
            if msg["role"] == "system":
                system_parts.append(msg["content"])
            elif msg["role"] in ("user", "assistant"):
                converted.append({"role": msg["role"], "content": msg["content"]})
        return " ".join(system_parts), converted

    def chat(
        self,
        messages: list[dict],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: bool = False,
    ) -> LLMResponse | Generator[str, None, None]:
        model = model or self.model
        system_prompt, converted_messages = self._convert_messages(messages)
        url = f"{self.base_url}/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": converted_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": stream,
        }
        if system_prompt:
            payload["system"] = system_prompt

        if stream:
            return self._stream_chat(url, headers, payload)

        resp = requests.post(url, headers=headers, json=payload, timeout=AI_REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        content_parts = data.get("content", [])
        content = "".join(p.get("text", "") for p in content_parts if p.get("type") == "text")
        usage = data.get("usage", {})
        return LLMResponse(
            content=content,
            provider=self.name,
            model=model,
            prompt_tokens=usage.get("input_tokens", 0),
            completion_tokens=usage.get("output_tokens", 0),
            total_tokens=usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
            finish_reason=data.get("stop_reason", "stop"),
            raw_response=data,
        )

    def _stream_chat(self, url: str, headers: dict, payload: dict) -> Generator[str, None, None]:
        resp = requests.post(
            url, headers=headers, json=payload, stream=True, timeout=AI_REQUEST_TIMEOUT
        )
        resp.raise_for_status()
        for line in resp.iter_lines():
            if not line:
                continue
            line_str = line.decode("utf-8")
            if line_str.startswith("data: "):
                data_str = line_str[6:]
                try:
                    chunk = json.loads(data_str)
                    if chunk.get("type") == "content_block_delta":
                        delta = chunk.get("delta", {})
                        text = delta.get("text", "")
                        if text:
                            yield text
                except json.JSONDecodeError:
                    continue

    def list_models(self) -> list[str]:
        return [
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
            "claude-3-opus-20240229",
            "claude-3-haiku-20240307",
        ]

    def estimate_cost(self, total_tokens: int, model: str) -> float:
        costs = AI_COST_PER_1K.get("claude", {})
        per_1k = costs.get(model, 0.00025)
        return round((total_tokens / 1000) * per_1k, 6)
