"""DeepSeek provider â€” supports DeepSeek Chat and Coder models."""

import json
from collections.abc import Generator

import requests

from ai.config import AI_COST_PER_1K, AI_REQUEST_TIMEOUT, DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL
from ai.providers.base import BaseProvider, LLMResponse


class DeepSeekProvider(BaseProvider):
    """DeepSeek AI provider â€” OpenAI-compatible API."""

    def __init__(
        self, api_key: str = "", base_url: str = "", model: str = "deepseek-chat", **kwargs
    ):
        super().__init__(
            api_key=api_key or DEEPSEEK_API_KEY,
            base_url=base_url or DEEPSEEK_BASE_URL,
            model=model,
            **kwargs,
        )

    @property
    def name(self) -> str:
        return "deepseek"

    @property
    def display_name(self) -> str:
        return "DeepSeek"

    def is_available(self) -> bool:
        return bool(self.api_key)

    def chat(
        self,
        messages: list[dict],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: bool = False,
    ) -> LLMResponse | Generator[str, None, None]:
        model = model or self.model
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
        }

        if stream:
            return self._stream_chat(url, headers, payload)

        resp = requests.post(url, headers=headers, json=payload, timeout=AI_REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        choice = data.get("choices", [{}])[0]
        usage = data.get("usage", {})
        return LLMResponse(
            content=choice.get("message", {}).get("content", ""),
            provider=self.name,
            model=model,
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
            finish_reason=choice.get("finish_reason", "stop"),
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
                if data_str == "[DONE]":
                    break
                try:
                    chunk = json.loads(data_str)
                    delta = chunk.get("choices", [{}])[0].get("delta", {})
                    content = delta.get("content", "")
                    if content:
                        yield content
                except json.JSONDecodeError:
                    continue

    def list_models(self) -> list[str]:
        return ["deepseek-chat", "deepseek-coder", "deepseek-reasoner"]

    def estimate_cost(self, total_tokens: int, model: str) -> float:
        costs = AI_COST_PER_1K.get("deepseek", {})
        per_1k = costs.get(model, 0.00014)
        return round((total_tokens / 1000) * per_1k, 6)
