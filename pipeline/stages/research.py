"""内置调研阶段：AIHOT story + 原文抓取 → 事实账本。"""

from __future__ import annotations

import html
import json
import re

import requests

from ..config import DomainConfig, PROMPTS_DIR
from ..llm import get_provider


def _fetch_text(url: str, limit: int = 4000) -> str:
    if not url:
        return ""
    try:
        resp = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        if resp.status_code != 200:
            return ""
        text = re.sub(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>", "", resp.text)
        text = re.sub(r"<[^>]+>", " ", text)
        text = html.unescape(re.sub(r"\s+", " ", text))
        return text[:limit]
    except Exception:  # noqa: BLE001
        return ""


def run_research(domain: DomainConfig, candidate: dict) -> dict:
    provider = get_provider(domain.provider, domain.model)
    prompt_tpl = (PROMPTS_DIR / "research.md").read_text(encoding="utf-8")

    materials = []
    if candidate.get("summary"):
        materials.append(f"[AIHOT 摘要]\n{candidate['summary']}")
    if candidate.get("reason"):
        materials.append(f"[推荐理由]\n{candidate['reason']}")

    extra = candidate.get("extra") or {}
    story_url = extra.get("story_url", "")
    if story_url:
        try:
            from ..sources.aihot import AIHOTSource

            story = AIHOTSource(domain.id, {}).fetch_story(story_url)
            digest = story.get("digest") or story.get("summary") or ""
            if digest:
                materials.append(f"[AIHOT 事件综述]\n{digest[:4000]}")
            storyline = story.get("storyline") or []
            if storyline:
                try:
                    materials.append(f"[事件时间线]\n{json.dumps(storyline[:5], ensure_ascii=False)[:1500]}")
                except Exception:  # noqa: BLE001
                    pass
        except Exception as exc:  # noqa: BLE001
            print(f"[research] story 获取失败: {exc}")

    if candidate.get("url"):
        body = _fetch_text(candidate["url"])
        if body:
            materials.append(f"[原文节选]\n{body}")

    prompt = (
        prompt_tpl.replace("{{domain_name}}", domain.name)
        .replace("{{materials}}", "\n\n".join(materials) if materials else "（无额外材料，仅标题：" + candidate.get("title", "") + "）")
    )
    return provider.chat(prompt, system="你是事实核查编辑，输出 JSON。", temperature=0.2)
