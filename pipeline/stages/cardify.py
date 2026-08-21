"""卡片切分阶段。"""

from __future__ import annotations

import json

from ..config import DomainConfig, PROMPTS_DIR
from ..llm import get_provider


def run_cardify(domain: DomainConfig, body: dict) -> list[dict]:
    provider = get_provider(domain.provider)
    tpl = (PROMPTS_DIR / "cardify.md").read_text(encoding="utf-8")
    lo, hi = domain.card_count
    prompt = (
        tpl.replace("{{body}}", json.dumps(body, ensure_ascii=False))
        .replace("{{card_count}}", f"{lo}-{hi}")
    )
    result = provider.chat(prompt, system="你是小红书图文排版师，输出 JSON。", temperature=0.3)
    return result.get("cards", [])
