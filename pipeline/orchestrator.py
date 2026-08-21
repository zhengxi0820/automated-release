"""流水线编排：采集 → 清洗 → 评分 →（闸门）→ 调研 → 成文 →（闸门）→ 卡片 → 成图 → 发布包。"""

from __future__ import annotations

import json
from datetime import date as date_cls
from datetime import datetime, timedelta, timezone

from .config import load_domain
from .db import (
    create_article,
    finish_run,
    get_article,
    init_db,
    insert_candidate,
    insert_cards,
    list_candidates,
    set_assess,
    set_decision,
    start_run,
    update_article,
)
from .sources import get_source
from .stages.assess import run_assess
from .stages.cardify import run_cardify
from .stages.research import run_research
from .stages.steelman import run_steelman
from .stages.write import run_write

CN_TZ = timezone(timedelta(hours=8))


def today_cn() -> str:
    return datetime.now(CN_TZ).strftime("%Y-%m-%d")


def _blocked_by_compliance(domain, item: dict) -> bool:
    title = (item.get("title") or "").lower()
    summary = (item.get("summary") or "").lower()
    cat = (item.get("category") or "").lower()
    if cat in domain.block_categories:
        return True
    return any(k.lower() in title or k.lower() in summary for k in domain.block_keywords)


def run_daily(domain_id: str, date: str | None = None, until: str = "assess", auto_select: int = 0) -> dict:
    """until: collect | assess | draft | package。auto_select>0 时跳过人工闸门①自动选前 N 条（用于测试）。"""
    domain = load_domain(domain_id)
    if domain is None:
        raise ValueError(f"领域不存在: {domain_id}")
    date = date or today_cn()
    init_db()
    run_id = start_run(domain.id, date)

    try:
        # 1) 采集 + 清洗 + 合规拦截
        since = datetime.now(CN_TZ) - timedelta(days=2)
        collected = {cfg["name"]: 0 for cfg in domain.sources}
        for cfg in domain.sources:
            src = get_source(cfg["name"], domain.id, cfg.get("params", {}))
            try:
                for item in src.fetch(since):
                    rec = {
                        "domain_id": domain.id,
                        "date": date,
                        "source": item.source,
                        "source_item_id": item.source_item_id,
                        "title": item.title,
                        "summary": item.summary,
                        "category": item.category,
                        "source_score": item.score,
                        "reason": item.reason,
                        "url": item.url,
                        "created_at": datetime.now(CN_TZ).isoformat(timespec="seconds"),
                        "extra": item.extra,
                    }
                    if _blocked_by_compliance(domain, rec):
                        continue
                    insert_candidate(rec)
                    collected[cfg["name"]] += 1
            except NotImplementedError as exc:
                print(f"[collect] 跳过 {cfg['name']}: {exc}")
            except Exception as exc:  # noqa: BLE001
                print(f"[collect] {cfg['name']} 采集失败: {exc}")
        finish_run(run_id, "ok", "collect")
        if until == "collect":
            return {"run_id": run_id, "stage": "collect", "domain": domain.id, "date": date,
                    "collected": collected}

        # 2) 探讨意义判断
        kept = run_assess(domain, date)
        _notify_candidates_ready(domain, date, kept)
        finish_run(run_id, "ok", "assess")
        if until == "assess":
            return {"run_id": run_id, "stage": "assess", "domain": domain.id, "date": date, "candidates": len(kept)}

        # 3) 闸门① 人工挑题；auto_select 用于测试/演示
        rows = list_candidates(domain.id, date)
        if auto_select > 0:
            scored = []
            for c in rows:
                if c["decision"] == "pending":
                    assess = json.loads(c["assess_json"]) if c["assess_json"] else {}
                    scored.append((float(assess.get("total", 0)), c))
            scored.sort(key=lambda x: x[0], reverse=True)
            for _, c in scored[:auto_select]:
                set_decision(int(c["id"]), "selected", "auto")
            rows = list_candidates(domain.id, date)  # 重新读取，拿到最新决策
        selected = []
        for c in rows:
            if c["decision"] == "selected":
                selected.append(dict(c))
        if not selected:
            finish_run(run_id, "ok", "waiting_review")
            return {"run_id": run_id, "stage": "waiting_review", "domain": domain.id, "date": date,
                    "message": "无人选候选，等待审核界面操作"}

        # 4) 逐条：调研 → 成文
        for cand in selected:
            research = run_research(domain, cand)
            steelman = run_steelman(domain, cand, research)
            article_id = create_article(int(cand["id"]), domain.id)
            article = get_article(article_id)
            draft = run_write(domain, cand, research, steelman)
            update_article(
                article_id,
                {
                    "title": draft.get("title", ""),
                    "body_json": draft,
                    "research_json": research,
                    "facts_json": research.get("facts", []),
                    "todo_verify_json": research.get("todo_verify", []),
                    "status": "draft",
                },
            )
        finish_run(run_id, "ok", "draft")
        if until == "draft":
            return {"run_id": run_id, "stage": "draft", "domain": domain.id, "date": date}

        # 5) 卡片化 → 成图 → 发布包（需要 render 模块，见 render/）
        if until == "package":
            from .render_api import build_package_for_domain

            result = build_package_for_domain(domain.id, date)
            finish_run(run_id, "ok", "package")
            return {"run_id": run_id, "stage": "package", "domain": domain.id, "date": date, **result}

        return {"run_id": run_id, "stage": "draft", "domain": domain.id, "date": date}
    except Exception as exc:  # noqa: BLE001
        finish_run(run_id, "failed", log=str(exc))
        raise

def _notify_candidates_ready(domain, date: str, kept: list) -> None:
    """候选就绪推送（PushPlus）。"""
    if "candidates_ready" not in domain.notify.get("events", []):
        return
    try:
        from notify import notify

        lines = [f"今日 {len(kept)} 条候选已就绪（{date}）", ""]
        for k in kept[:5]:
            assess = k.get("assess", {})
            lines.append(f"• {assess.get('total', 0)} 分 {k['candidate']['title']}")
        url = domain.notify.get("review_url") or ""
        if url:
            lines.append("")
            lines.append(f"去审核：{url}")
        notify("candidates_ready", f"{domain.name} · 今日候选 {len(kept)} 条", "<br>".join(lines))
    except Exception as exc:  # noqa: BLE001
        print(f"[notify] 推送失败: {exc}")
