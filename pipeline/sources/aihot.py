"""AIHOT（卡兹克 AI 热点站）数据源适配器。

官方匿名公开 API，免登录免 Key。条款：匿名个人非商业免费；商业用途需书面授权。
本项目初期按「选题灵感来源」使用。
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

from .base import NormalizedItem, SourceAdapter

BASE_URL = "https://aihot.virxact.com"
API = f"{BASE_URL}/api/v1"
CACHE_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "cache"
MIN_INTERVAL_SECONDS = 60


class AIHOTSource(SourceAdapter):
    name = "aihot"

    def __init__(self, domain_id: str, params: dict | None = None):
        super().__init__(domain_id, params)
        self.session = requests.Session()
        self.session.headers["User-Agent"] = "xhs-hotspot-pipeline/0.1 (+personal use)"

    def _get(self, path: str, params: dict | None = None, use_cache: bool = True) -> dict:
        """带 ETag 缓存的 GET；同端点轮询间隔 >= 60s。"""
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cache_key = hashlib.sha256(f"{path}{json.dumps(params or {}, sort_keys=True)}".encode()).hexdigest()[:16]
        cache_file = CACHE_DIR / f"{cache_key}.json"

        if use_cache and cache_file.exists():
            mtime = datetime.fromtimestamp(cache_file.stat().st_mtime, tz=timezone.utc)
            if datetime.now(timezone.utc) - mtime < timedelta(seconds=MIN_INTERVAL_SECONDS):
                return json.loads(cache_file.read_text(encoding="utf-8"))

        resp = self.session.get(f"{API}{path}", params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        cache_file.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        return data

    def fetch(self, since: datetime) -> list[NormalizedItem]:
        items: list[NormalizedItem] = []
        seen: set[str] = set()

        # 1) 精选资讯流
        mode = self.params.get("mode", "selected")
        window = self.params.get("window", "24h")
        data = self._get("/items", {"mode": mode, "window": window})
        for it in data.get("items", []):
            item = self._to_item(it)
            if item.source_item_id not in seen:
                seen.add(item.source_item_id)
                items.append(item)

        # 2) 今日热点 Top
        if self.params.get("extra_endpoints") and "hot-topics" in self.params["extra_endpoints"]:
            hot = self._get("/hot-topics")
            for it in hot.get("items", []):
                item = self._to_item(it)
                if item.source_item_id not in seen:
                    seen.add(item.source_item_id)
                    items.append(item)

        # 3) 按时间过滤
        if since:
            items = [i for i in items if i.published_at is None or i.published_at >= since]

        items.sort(key=lambda i: i.published_at or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
        return items

    def _to_item(self, it: dict) -> NormalizedItem:
        links = it.get("links", {}) or {}
        published = None
        raw = it.get("publishedAt") or it.get("latestAt")
        if raw:
            try:
                published = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            except ValueError:
                published = None
        return NormalizedItem(
            source=self.name,
            source_item_id=it.get("id", ""),
            title=it.get("title", ""),
            summary=it.get("summary", ""),
            url=links.get("original") or links.get("aihot", ""),
            category=it.get("category", ""),
            score=it.get("score"),
            reason=it.get("reason", ""),
            published_at=published,
            extra={
                "aihot_url": links.get("aihot", ""),
                "story_url": links.get("story", ""),
                "source_name": (it.get("source") or {}).get("name", ""),
                "signal_count": it.get("signalCount"),
                "source_count": it.get("sourceCount"),
                "rank": it.get("rank"),
            },
        )

    def fetch_story(self, story_url: str) -> dict:
        """按需拉取事件来龙去脉（stories/{publicId}）。"""
        story_id = story_url.rstrip("/").split("/")[-1]
        data = self._get(f"/stories/{story_id}")
        return data.get("story") or data
