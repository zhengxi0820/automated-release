"""数据源适配器统一接口。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class NormalizedItem:
    source: str
    source_item_id: str
    title: str
    summary: str = ""
    url: str = ""
    category: str = ""
    score: float | None = None
    reason: str = ""
    published_at: datetime | None = None
    extra: dict = field(default_factory=dict)


class SourceAdapter(ABC):
    name: str = "base"

    def __init__(self, domain_id: str, params: dict | None = None):
        self.domain_id = domain_id
        self.params = params or {}

    @abstractmethod
    def fetch(self, since: datetime) -> list[NormalizedItem]:
        """拉取热点条目，输出归一化数据。"""
