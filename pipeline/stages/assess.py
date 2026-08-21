"""探讨意义判断阶段。"""

from __future__ import annotations

from ..config import DomainConfig, PROMPTS_DIR
from ..db import list_candidates, set_assess
from ..llm import get_provider


def _load_prompt(name: str) -> str:
    return (PROMPTS_DIR / name).read_text(encoding="utf-8")


def run_assess(domain: DomainConfig, date: str) -> list[dict]:
    provider = get_provider(domain.provider, domain.model)
    prompt_tpl = _load_prompt("assess.md")
    w = domain.assess_weights
    kept = []

    for row in list_candidates(domain.id, date):
        if row["decision"] == "blocked":
            continue
        prompt = (
            prompt_tpl.replace("{{domain_name}}", domain.name)
            .replace("{{title}}", row["title"])
            .replace("{{summary}}", row["summary"] or "")
            .replace("{{category}}", row["category"] or "")
            .replace("{{source_score}}", str(row["source_score"] or ""))
            .replace("{{reason}}", row["reason"] or "")
            .replace("{{signal_count}}", "—")
            .replace("{{weight_heat}}", str(w["heat"]))
            .replace("{{weight_controversy}}", str(w["controversy"]))
            .replace("{{weight_domain_match}}", str(w["domain_match"]))
            .replace("{{weight_writable}}", str(w["writable"]))
            .replace("{{weight_risk}}", str(w["risk"]))
            .replace("{{risk_max_for_keep}}", str(domain.assess.get("risk_max_for_keep", 1)))
        )
        try:
            result = provider.chat(prompt, system="你是选题编辑，输出 JSON。", temperature=0.3)
            set_assess(int(row["id"]), result)
            verdict = result.get("verdict", "weak")
            if verdict == "blocked":
                set_assess(int(row["id"]), {**result, "total": 0.0})
                continue
            if verdict != "worth_discussing":
                continue
            total = float(result.get("total") or 0)
            risk = float((result.get("dimensions") or {}).get("risk") or 0)
            if total < domain.min_score:
                continue
            if risk > float(domain.assess.get("risk_max_for_keep", 1)):
                continue
            kept.append({"candidate": dict(row), "assess": result})
        except Exception as exc:  # noqa: BLE001
            print(f"[assess] 候选 {row['id']} 评估失败: {exc}")

    kept.sort(key=lambda x: x["assess"].get("total", 0), reverse=True)
    return kept[: domain.candidate_budget]
