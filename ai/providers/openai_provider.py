"""OpenAI provider â€” supports GPT-4o, GPT-4, GPT-3.5-turbo and compatible APIs."""

import json
from collections.abc import Generator

import requests

from ai.config import AI_COST_PER_1K, AI_REQUEST_TIMEOUT, OPENAI_API_KEY, OPENAI_BASE_URL
from ai.providers.base import BaseProvider, LLMResponse


class OpenAIProvider(BaseProvider):
    """OpenAI-compatible API provider (also works with Azure OpenAI, proxies)."""

    def __init__(self, api_key: str = "", base_url: str = "", model: str = "gpt-4o-mini", **kwargs):
        super().__init__(
            api_key=api_key or OPENAI_API_KEY,
            base_url=base_url or OPENAI_BASE_URL,
            model=model,
            **kwargs,
        )

    @property
    def name(self) -> str:
        return "openai"

    @property
    def display_name(self) -> str:
        return "OpenAI"

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

    def _stream_chat(self, url: str, headers: str, payload: dict) -> Generator[str, None, None]:
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
        if not self.api_key:
            return ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"]
        try:
            url = f"{self.base_url}/models"
            headers = {"Authorization": f"Bearer {self.api_key}"}
            resp = requests.get(url, headers=headers, timeout=AI_REQUEST_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
            return [m["id"] for m in data.get("data", []) if "gpt" in m.get("id", "")]
        except Exception:
            return ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"]

    def estimate_cost(self, total_tokens: int, model: str) -> float:
        costs = AI_COST_PER_1K.get("openai", {})
        per_1k = costs.get(model, 0.00015)
        return round((total_tokens / 1000) * per_1k, 6)
