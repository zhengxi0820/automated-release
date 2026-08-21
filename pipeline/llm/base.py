"""模型层统一接口，调用方不感知具体 provider。"""

from __future__ import annotations

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    @abstractmethod
    def chat(
        self,
        prompt: str,
        system: str = "",
        json_mode: bool = True,
        temperature: float = 0.6,
        max_tokens: int = 4096,
    ) -> str | dict:
        """返回 dict（json_mode=True）或文本。"""
