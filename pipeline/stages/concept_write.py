"""概念科普成文阶段：寓言式讲透一个概念（单次 LLM 调用）。"""

from __future__ import annotations

from ..config import DomainConfig, PROMPTS_DIR
from ..llm import get_provider
from .write import FABRICATED_PATTERNS, _has_fabricated_experience


def run_concept_write(domain: DomainConfig, concept: str) -> dict:
    provider = get_provider(domain.provider, domain.model)
    tpl = (PROMPTS_DIR / "concept_write.md").read_text(encoding="utf-8")

    disclaimer_rule = (
        f"文末最后一段必须自然包含这句免责声明：「{domain.writing_disclaimer}」"
        if domain.writing_disclaimer
        else "（本领域无强制免责声明）"
    )
    prompt = (
        tpl.replace("{{domain_name}}", domain.name)
        .replace("{{persona}}", domain.persona or "（未配置人设，按通用零门槛科普规则写）")
        .replace("{{concept}}", concept)
        .replace("{{title_max_chars}}", str(domain.title_max_chars))
        .replace("{{min_length}}", str(domain.writing_min_length))
        .replace("{{max_length}}", str(domain.writing_max_length))
        .replace("{{disclaimer_rule}}", disclaimer_rule)
    )
    result = provider.chat(prompt, system="你是科普写手，输出 JSON。", temperature=domain.temperature,
                           max_tokens=domain.max_tokens)

    hits = _has_fabricated_experience(result)
    if hits:
        fix = (
            "上面这版违反了「禁止编造亲历」硬规则，命中：" + "、".join(hits) +
            "。请重写：删除所有第一人称实测/体验表述；故事主角用第三人称；其余规则不变。"
        )
        result = provider.chat(prompt + "\n\n" + fix, system="你是科普写手，输出 JSON。", temperature=0.3,
                               max_tokens=domain.max_tokens)
        result["self_check"] = {
            **(result.get("self_check") or {}),
            "no_fabricated_experience": "pass" if not _has_fabricated_experience(result) else "fail",
        }
    return result
