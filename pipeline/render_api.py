"""流水线 → 渲染层桥接：卡片化 → 成图 → 发布包。"""

from __future__ import annotations

import json

from .config import load_domain
from .db import (
    get_article,
    insert_cards,
    insert_package,
    list_candidates,
    list_cards,
    set_card_image,
    update_article,
)
from .stages.cardify import run_cardify
from render.package import build_package
from render.render_cards import render_article


def build_package_for_article(domain_id: str, article_id: int) -> dict:
    domain = load_domain(domain_id)
    article = get_article(article_id)
    if article is None:
        raise ValueError(f"文章不存在: {article_id}")

    body = json.loads(article["body_json"]) if article["body_json"] else {}
    cards = run_cardify(domain, body)
    insert_cards(article_id, cards)

    rows = list_cards(article_id)
    cards_data = [dict(r) for r in rows]
    tag = " ".join(body.get("tags", [])[:1]) or "#AI工具"
    pngs = render_article(domain.id, article_id, domain.name, cards_data, tag)
    for i, p in enumerate(pngs, start=1):
        set_card_image(article_id, i, str(p))

    todo = json.loads(article["todo_verify_json"]) if article["todo_verify_json"] else []
    todo_plain = [t.get("claim", str(t)) if isinstance(t, dict) else str(t) for t in todo]
    zip_path = build_package(
        domain.id,
        article_id,
        article["title"] or "",
        body,
        body.get("tags", []),
        todo_plain,
        pngs,
    )
    pkg_id = insert_package(article_id, str(zip_path), zip_path.stat().st_size)
    update_article(article_id, {"status": "packaged"})
    return {"article_id": article_id, "package_id": pkg_id, "package_path": str(zip_path), "cards": len(pngs)}


def build_package_for_domain(domain_id: str, date: str) -> dict:
    """为当天所有 draft 文章打包（闸门③ 由用户发布时执行）。"""
    results = []
    for cand in list_candidates(domain_id, date):
        if cand["decision"] != "selected":
            continue
        # 找到该候选对应的文章
        from .db import get_conn

        with get_conn() as conn:
            rows = conn.execute("SELECT id FROM articles WHERE candidate_id=? AND status IN ('draft','confirmed')",
                                (cand["id"],)).fetchall()
        for r in rows:
            results.append(build_package_for_article(domain_id, int(r["id"])))
    return {"packages": results}
