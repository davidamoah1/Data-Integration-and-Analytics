"""Local LLM provider â€” supports Ollama, LM Studio, vLLM, and other OpenAI-compatible local servers."""

import json
from collections.abc import Generator

import requests

from ai.config import AI_REQUEST_TIMEOUT, LOCAL_LLM_BASE_URL
from ai.providers.base import BaseProvider, LLMResponse


class LocalLLMProvider(BaseProvider):
    """Local LLM provider for self-hosted models (Ollama, LM Studio, vLLM)."""

    def __init__(self, api_key: str = "", base_url: str = "", model: str = "llama3", **kwargs):
        super().__init__(
            api_key=api_key or "local",
            base_url=base_url or LOCAL_LLM_BASE_URL,
            model=model,
            **kwargs,
        )

    @property
    def name(self) -> str:
        return "local"

    @property
    def display_name(self) -> str:
        return "Local LLM"

    def is_available(self) -> bool:
        try:
            resp = requests.get(f"{self.base_url}/models", timeout=5)
            return resp.status_code == 200
        except Exception:
            return False

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
        headers = {"Content-Type": "application/json"}
        if self.api_key and self.api_key != "local":
            headers["Authorization"] = f"Bearer {self.api_key}"
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
        try:
            resp = requests.get(f"{self.base_url}/models", timeout=5)
            resp.raise_for_status()
            data = resp.json()
            return [
                m.get("id", m.get("name", "")) for m in data.get("data", data.get("models", []))
            ]
        except Exception:
            return ["llama3", "mistral", "phi3", "qwen2"]

    def estimate_cost(self, total_tokens: int, model: str) -> float:
        return 0.0
