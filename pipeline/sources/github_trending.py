"""GitHub Trending 适配器（v1 用 Search API 近似：近 7 天创建 + 高 star 的仓库）。"""

from __future__ import annotations

from datetime import datetime, timezone

import requests

from .base import NormalizedItem, SourceAdapter


class GitHubTrendingSource(SourceAdapter):
    name = "github_trending"

    def fetch(self, since: datetime) -> list[NormalizedItem]:
        keywords = self.params.get("keywords", ["ai"])
        min_stars = int(self.params.get("min_stars", 200))
        since_str = since.strftime("%Y-%m-%d")
        items: list[NormalizedItem] = []

        for kw in keywords[:4]:
            query = f"{kw} created:>{since_str} stars:>{min_stars}"
            resp = requests.get(
                "https://api.github.com/search/repositories",
                params={"q": query, "sort": "stars", "order": "desc", "per_page": 10},
                headers={"Accept": "application/vnd.github+json", "User-Agent": "xhs-hotspot-pipeline/0.1"},
                timeout=30,
            )
            if resp.status_code != 200:
                continue
            for repo in resp.json().get("items", []):
                created = None
                try:
                    created = datetime.fromisoformat(repo.get("created_at", "").replace("Z", "+00:00"))
                except ValueError:
                    created = None
                stars = int(repo.get("stargazers_count") or 0)
                items.append(
                    NormalizedItem(
                        source=self.name,
                        source_item_id=str(repo.get("id", "")),
                        title=f"GitHub 热门：{repo.get('full_name', '')}",
                        summary=(repo.get("description") or "")[:300],
                        url=repo.get("html_url", ""),
                        category="tool",
                        score=float(stars),
                        reason=f"{stars} stars · {repo.get('language') or '未知语言'}",
                        published_at=created,
                        extra={"full_name": repo.get("full_name", ""), "stars": stars},
                    )
                )
        # 按 star 排序去重
        seen: set[str] = set()
        out = []
        for it in sorted(items, key=lambda i: i.score or 0, reverse=True):
            if it.source_item_id not in seen:
                seen.add(it.source_item_id)
                out.append(it)
        return out
