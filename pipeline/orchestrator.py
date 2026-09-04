"""流水线编排：采集 → 清洗 → 评分 →（闸门）→ 调研 → 成文 →（闸门）→ 卡片 → 成图 → 发布包。"""

from __future__ import annotations

import json
from datetime import date as date_cls
from datetime import datetime, timedelta, timezone

from .config import load_domain
from .db import (
    create_article,
    finish_run,
    init_db,
    insert_candidate,
    list_candidates,
    set_assess,
    set_decision,
    start_run,
    sweep_stale_runs,
    update_article,
)
from .sources import get_source
from .stages.assess import run_assess
from .stages.cardify import run_cardify
from .stages.concept_write import run_concept_write
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
    sweep_stale_runs()
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

        # 4) 逐条：调研 → 成文（成文成功后才建 article，失败不留僵尸草稿）
        for cand in selected:
            research = run_research(domain, cand)
            steelman = run_steelman(domain, cand, research)
            draft = run_write(domain, cand, research, steelman)
            article_id = create_article(int(cand["id"]), domain.id)
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


def pop_concept(domain_id: str, concept: str | None = None) -> str:
    """从概念池 concepts/<domain_id>.txt 取题：显式指定优先，否则取池顶并归档到 used。"""
    from .config import ROOT

    pool = ROOT / "concepts" / f"{domain_id}.txt"
    if concept:
        return concept.strip()
    if not pool.exists():
        raise ValueError(f"概念池不存在: {pool}（先添加概念，一行一个）")
    lines = [ln.strip() for ln in pool.read_text(encoding="utf-8").splitlines()]
    queue = [ln for ln in lines if ln and not ln.startswith("#")]
    if not queue:
        raise ValueError(f"概念池已空: {pool}")
    head = queue[0]
    rest = [ln for ln in lines if ln.strip() != head]
    pool.write_text("\n".join(rest) + ("\n" if rest else ""), encoding="utf-8")
    used = ROOT / "concepts" / f"{domain_id}.used.txt"
    with used.open("a", encoding="utf-8") as f:
        f.write(f"{head}\t{datetime.now(CN_TZ).isoformat(timespec='seconds')}\n")
    return head


def run_concept(domain_id: str, concept: str | None = None, date: str | None = None,
                until: str = "draft") -> dict:
    """概念科普链路：概念池取题 → 成文 →（审核闸门）→ 结构化 → 成图 → 发布包。

    跳过热点链路的 collect/assess/research/steelman。until: draft | package。
    """
    domain = load_domain(domain_id)
    if domain is None:
        raise ValueError(f"领域不存在: {domain_id}")
    if domain.content_type != "concept":
        raise ValueError(f"领域 {domain_id} 不是 concept 类型（content_type={domain.content_type}）")
    date = date or today_cn()
    init_db()
    sweep_stale_runs()
    run_id = start_run(domain.id, date)

    try:
        concept = pop_concept(domain_id, concept)
        print(f"[concept] 本次讲透: {concept}")

        # 候选记录直接置为 selected（概念模式无人工挑题，审核闸门在成文之后）
        insert_candidate({
            "domain_id": domain.id,
            "date": date,
            "source": "concept",
            "source_item_id": f"concept-{concept}",
            "title": concept,
            "summary": f"概念科普：{concept}",
            "category": "concept",
            "source_score": None,
            "reason": "概念池取题",
            "url": "",
            "created_at": datetime.now(CN_TZ).isoformat(timespec="seconds"),
        })
        rows = list_candidates(domain.id, date)
        cand = next(c for c in rows if c["source_item_id"] == f"concept-{concept}")
        set_decision(int(cand["id"]), "selected", "concept")

        draft = run_concept_write(domain, concept)
        article_id = create_article(int(cand["id"]), domain.id)
        update_article(
            article_id,
            {
                "title": draft.get("title", ""),
                "body_json": draft,
                "facts_json": [],
                "todo_verify_json": draft.get("todo_verify", []),
                "status": "draft",
            },
        )
        finish_run(run_id, "ok", "draft")
        if until == "draft":
            return {"run_id": run_id, "stage": "draft", "domain": domain.id, "date": date,
                    "concept": concept, "article_id": article_id}

        if until == "package":
            from .render_api import build_package_for_article

            result = build_package_for_article(domain.id, article_id)
            finish_run(run_id, "ok", "package")
            return {"run_id": run_id, "stage": "package", "domain": domain.id, "date": date,
                    "concept": concept, "article_id": article_id, **result}

        return {"run_id": run_id, "stage": "draft", "domain": domain.id, "date": date,
                "concept": concept, "article_id": article_id}
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
