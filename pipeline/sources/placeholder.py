"""未实现数据源的占位：v1 以 AIHOT 为主源，补充源逐步接入。"""

from __future__ import annotations

from datetime import datetime

from .base import NormalizedItem, SourceAdapter


class NotImplementedSource(SourceAdapter):
    def __init__(self, name: str, domain_id: str, params: dict | None = None):
        super().__init__(domain_id, params)
        self.name = name

    def fetch(self, since: datetime) -> list[NormalizedItem]:
        raise NotImplementedError(f"数据源 {self.name} 尚未实现（v1 先以 AIHOT 为主源）")
