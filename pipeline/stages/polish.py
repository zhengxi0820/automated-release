"""按批注润色阶段。"""

from __future__ import annotations

import json

from ..config import DomainConfig, PROMPTS_DIR
from ..db import mark_feedback_applied
from ..llm import get_provider


def run_polish(domain: DomainConfig, article_id: int, body: dict, feedback: list[dict]) -> dict:
    provider = get_provider(domain.provider, domain.model)
    tpl = (PROMPTS_DIR / "polish.md").read_text(encoding="utf-8")
    prompt = (
        tpl.replace("{{domain_name}}", domain.name)
        .replace("{{body}}", json.dumps(body, ensure_ascii=False))
        .replace("{{feedback}}", json.dumps(feedback, ensure_ascii=False))
        .replace("{{title_max_chars}}", str(domain.title_max_chars))
    )
    result = provider.chat(prompt, system="你是小红书编辑，输出 JSON。", temperature=0.4)
    mark_feedback_applied(article_id)
    return result
