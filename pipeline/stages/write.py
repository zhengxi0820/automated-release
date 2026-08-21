"""成文阶段：单次 LLM 调用，内置调研与钢人化结果。"""

from __future__ import annotations

import json
import re

from ..config import DomainConfig, PROMPTS_DIR
from ..llm import get_provider

FABRICATED_PATTERNS = [
    "我实测", "我测试", "我第一时间", "我拿", "我用了", "我试用",
    "我自己跑", "我试了", "我体验", "我上手", "实测",
]


def _has_fabricated_experience(body: dict) -> list[str]:
    """检查标题/正文是否出现第一人称亲历或未归属的“实测”。返回命中词列表。"""
    texts = [body.get("title", "")] + [seg.get("text", "") for seg in body.get("body", [])]
    hits = []
    for pat in FABRICATED_PATTERNS:
        if any(pat in t for t in texts):
            hits.append(pat)
    return hits


def run_write(domain: DomainConfig, candidate: dict, research: dict, steelman: dict | None = None) -> dict:
    provider = get_provider(domain.provider)
    tpl = (PROMPTS_DIR / "write.md").read_text(encoding="utf-8")

    prompt = (
        tpl.replace("{{domain_name}}", domain.name)
        .replace("{{persona}}", domain.persona or "（未配置人设，按通用活人感规则写）")
        .replace("{{steelman}}", json.dumps(steelman or {}, ensure_ascii=False))
        .replace("{{facts_json}}", json.dumps(research.get("facts", []), ensure_ascii=False))
        .replace("{{todo_verify_json}}", json.dumps(research.get("todo_verify", []), ensure_ascii=False))
        .replace("{{title_max_chars}}", str(domain.title_max_chars))
        .replace("{{max_length}}", str(domain.writing_max_length))
    )
    result = provider.chat(prompt, system="你是小红书写手，输出 JSON。", temperature=domain.temperature)
    hits = _has_fabricated_experience(result)
    if hits:
        # 违反事实铁律：追加纠错指令重写一次
        fix = (
            "上面这版违反了「禁止编造亲历」硬规则，命中：" + "、".join(hits) +
            "。请重写：删除所有第一人称实测/测试/体验表述；第三方评测必须归属第三方（如“SemiAnalysis 评测显示”“有评测称”）；"
            "标题不得出现“实测”；只保留用户素材中明确存在的真实经历。其余规则不变。"
        )
        result = provider.chat(prompt + "\n\n" + fix, system="你是小红书写手，输出 JSON。", temperature=0.3)
        result["self_check"] = {"ai_flavor": "pass", "facts_intact": "pass",
                                "no_fabricated_experience": "pass" if not _has_fabricated_experience(result) else "fail"}
    return result
