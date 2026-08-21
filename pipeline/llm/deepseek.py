"""DeepSeek API 实现。"""

from __future__ import annotations

import json

import requests

from ..config import env
from .base import LLMProvider

BASE = "https://api.deepseek.com/chat/completions"


class DeepSeekProvider(LLMProvider):
    def __init__(self, model: str = "deepseek-chat"):
        self.model = model
        self.api_key = env("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise RuntimeError("缺少 DEEPSEEK_API_KEY（请在 .env 中配置）")

    def chat(
        self,
        prompt: str,
        system: str = "",
        json_mode: bool = True,
        temperature: float = 0.6,
        max_tokens: int = 4096,
    ) -> str | dict:
        payload = {
            "model": self.model,
            "messages": [
                *([{"role": "system", "content": system}] if system else []),
                {"role": "user", "content": prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        resp = requests.post(
            BASE,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=120,
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        if json_mode:
            return json.loads(content)
        return content
