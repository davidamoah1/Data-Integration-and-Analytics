"""Google Gemini provider — supports Gemini 1.5 Pro and Flash."""

import json
import requests
from typing import Optional, Generator
from ai.providers.base import BaseProvider, LLMResponse
from ai.config import GEMINI_API_KEY, GEMINI_BASE_URL, AI_REQUEST_TIMEOUT
from ai.config import AI_COST_PER_1K


class GeminiProvider(BaseProvider):
    """Google Gemini AI provider."""

    def __init__(self, api_key: str = "", base_url: str = "", model: str = "gemini-1.5-flash", **kwargs):
        super().__init__(
            api_key=api_key or GEMINI_API_KEY,
            base_url=base_url or GEMINI_BASE_URL,
            model=model,
            **kwargs,
        )

    @property
    def name(self) -> str:
        return "gemini"

    @property
    def display_name(self) -> str:
        return "Google Gemini"

    def is_available(self) -> bool:
        return bool(self.api_key)

    def _convert_messages(self, messages: list[dict]) -> tuple[str, list[dict]]:
        """Convert OpenAI-style messages to Gemini format."""
        system_parts = []
        contents = []
        for msg in messages:
            if msg["role"] == "system":
                system_parts.append(msg["content"])
            elif msg["role"] == "user":
                contents.append({"role": "user", "parts": [{"text": msg["content"]}]})
            elif msg["role"] == "assistant":
                contents.append({"role": "model", "parts": [{"text": msg["content"]}]})
        system_instruction = " ".join(system_parts) if system_parts else None
        return system_instruction, contents

    def chat(self, messages: list[dict], model: Optional[str] = None,
             temperature: float = 0.7, max_tokens: int = 4096,
             stream: bool = False) -> LLMResponse | Generator[str, None, None]:
        model = model or self.model
        system_instruction, contents = self._convert_messages(messages)
        url = f"{self.base_url}/models/{model}:generateContent?key={self.api_key}"
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }
        if system_instruction:
            payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

        resp = requests.post(url, json=payload, timeout=AI_REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        candidates = data.get("candidates", [])
        content = ""
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            content = "".join(p.get("text", "") for p in parts)
        usage = data.get("usageMetadata", {})
        return LLMResponse(
            content=content,
            provider=self.name,
            model=model,
            prompt_tokens=usage.get("promptTokenCount", 0),
            completion_tokens=usage.get("candidatesTokenCount", 0),
            total_tokens=usage.get("totalTokenCount", 0),
            finish_reason=candidates[0].get("finishReason", "stop") if candidates else "stop",
            raw_response=data,
        )

    def list_models(self) -> list[str]:
        return ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-1.5-flash-8b"]

    def estimate_cost(self, total_tokens: int, model: str) -> float:
        costs = AI_COST_PER_1K.get("gemini", {})
        per_1k = costs.get(model, 0.000075)
        return round((total_tokens / 1000) * per_1k, 6)
