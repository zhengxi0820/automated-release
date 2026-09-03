"""卡片化阶段：LLM 做编辑结构化（分节 + 信息量标题），分页与成图由代码确定性完成。

产出 sections: [{heading, paragraphs}]，交给 render/flow_cards.py 排版。
"""

from __future__ import annotations

from ..config import DomainConfig, PROMPTS_DIR
from ..llm import get_provider


def _fallback_sections(body: dict) -> list[dict]:
    """LLM 输出不可用时的兜底：每个 body 段落自成一节（无标题）。"""
    paras = [seg.get("text", "") for seg in body.get("body", []) if seg.get("text")]
    return [{"heading": "", "paragraphs": paras}] if paras else []


def run_cardify(domain: DomainConfig, body: dict) -> list[dict]:
    """把 write 产出的 body 段落重组为 sections（heading + paragraphs）。"""
    provider = get_provider(domain.provider, domain.model)
    tpl = (PROMPTS_DIR / "cardify.md").read_text(encoding="utf-8")
    import json

    prompt = (
        tpl.replace("{{domain_name}}", domain.name)
        .replace("{{body}}", json.dumps(body.get("body", []), ensure_ascii=False))
        .replace("{{section_count}}", str(domain.section_count))
        .replace("{{title_max_chars}}", str(domain.title_max_chars))
    )
    try:
        result = provider.chat(prompt, system="你是小红书图文排版师，输出 JSON。", temperature=0.3)
        sections = result.get("sections") or []
    except Exception as exc:  # noqa: BLE001
        print(f"[cardify] LLM 结构化失败，使用兜底切分: {exc}")
        sections = []

    # 校验：至少一节、每节有段落文本
    sections = [
        {
            "heading": (s.get("heading") or "").strip(),
            "paragraphs": [p.strip() for p in (s.get("paragraphs") or []) if p and p.strip()],
        }
        for s in sections
    ]
    sections = [s for s in sections if s["paragraphs"]]
    return sections or _fallback_sections(body)
