"""角度设计（钢人化）阶段。"""

from __future__ import annotations

import json

from ..config import DomainConfig, PROMPTS_DIR
from ..llm import get_provider


def run_steelman(domain: DomainConfig, candidate: dict, research: dict | None = None) -> dict:
    provider = get_provider(domain.provider, domain.model)
    tpl = (PROMPTS_DIR / "steelman.md").read_text(encoding="utf-8")
    prompt = (
        tpl.replace("{{domain_name}}", domain.name)
        .replace("{{title}}", candidate.get("title", ""))
        .replace("{{summary}}", candidate.get("summary", ""))
        .replace("{{reason}}", candidate.get("reason", ""))
        .replace("{{angles}}", domain.angles or "（无角度库，自行给出合适角度）")
    )
    return provider.chat(prompt, system="你是主笔，输出 JSON。", temperature=0.4)
