"""流水线 → 渲染层桥接：卡片化 → 成图 → 发布包。

cardify.mode = flow（默认）：LLM 结构化分节 → render/flow_cards 确定性分页成图。
cardify.mode = legacy：旧单卡模板路径（render/render_cards）。
"""

from __future__ import annotations

import json

from .config import DomainConfig, load_domain
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


def _flow_layout(domain: DomainConfig):
    from render.flow_cards import Layout

    w, h = domain.canvas
    return Layout(w=w, h=h, **domain.flow_layout_overrides)


def build_package_for_article(domain_id: str, article_id: int) -> dict:
    domain = load_domain(domain_id)
    article = get_article(article_id)
    if article is None:
        raise ValueError(f"文章不存在: {article_id}")

    body = json.loads(article["body_json"]) if article["body_json"] else {}

    if domain.cardify_mode == "flow":
        pngs, article_text = _build_flow_package(domain, article_id, body)
    else:
        pngs, article_text = _build_legacy(domain, article_id, body)

    for i, p in enumerate(pngs, start=1):
        set_card_image(article_id, i, str(p))

    todo = json.loads(article["todo_verify_json"]) if article["todo_verify_json"] else []
    todo_plain = [t.get("claim", str(t)) if isinstance(t, dict) else str(t) for t in todo]
    zip_path = build_package(
        domain.id,
        article_id,
        article["title"] or "",
        article_text,
        body.get("tags", []),
        todo_plain,
        pngs,
    )
    pkg_id = insert_package(article_id, str(zip_path), zip_path.stat().st_size)
    update_article(article_id, {"status": "packaged"})
    return {"article_id": article_id, "package_id": pkg_id, "package_path": str(zip_path), "cards": len(pngs)}


def _build_flow_package(domain: DomainConfig, article_id: int, body: dict):
    """书页式连续排版：LLM 分节 → 代码分页成图。返回 (pngs, 全文文本)。"""
    from render.flow_cards import article_text as flow_article_text
    from render.flow_cards import render_flow_pages

    sections = run_cardify(domain, body)
    use_headings = domain.use_headings

    # cards 表存最终页面（seq/kind/text），审核界面可展示
    L = _flow_layout(domain)
    from render.flow_cards import build_units, paginate

    pages_units = paginate(build_units(sections, L, use_headings), L)
    page_rows = []
    if use_headings:
        page_rows.append({"kind": "cover", "text": body.get("title", "")})
    for i, units in enumerate(pages_units, start=1):
        text = "".join(ln for u in units for ln in (u["lines"] if u["kind"] != "gap" else []))
        page_rows.append({"kind": "page", "text": text})
    insert_cards(article_id, page_rows)

    pngs = render_flow_pages(
        domain.id, article_id, sections,
        title=body.get("title", ""),
        layout=L,
        use_headings=use_headings,
    )
    return pngs, flow_article_text(sections, use_headings)


def _build_legacy(domain: DomainConfig, article_id: int, body: dict):
    """旧单卡模板路径。"""
    from render.render_cards import render_article

    cards = run_cardify(domain, body)
    insert_cards(article_id, cards)
    rows = list_cards(article_id)
    cards_data = [dict(r) for r in rows]
    tag = " ".join(body.get("tags", [])[:1]) or "#AI工具"
    pngs = render_article(domain.id, article_id, domain.name, cards_data, tag)
    text = "\n\n".join(seg.get("text", "") for seg in body.get("body", []))
    return pngs, text


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
