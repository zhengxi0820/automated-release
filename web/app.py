"""手机审核界面：候选审核、草稿批注、润色、确认、下载。"""

from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel

from pipeline.config import load_domain, load_domains
from pipeline.db import (
    add_feedback,
    get_article,
    get_conn,
    list_candidates,
    list_feedback,
    set_decision,
    update_article,
)
from pipeline.orchestrator import today_cn
from pipeline.render_api import build_package_for_article
from pipeline.stages.polish import run_polish

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "web" / "static"

app = FastAPI(title="XHS 审核界面", version="0.1.0")


class DecisionBody(BaseModel):
    decision: str
    note: str = ""


class FeedbackBody(BaseModel):
    feedback: list[dict]


class ManualCandidate(BaseModel):
    domain_id: str
    title: str
    url: str = ""
    note: str = ""


def _candidate_out(row) -> dict:
    out = dict(row)
    out["assess"] = json.loads(row["assess_json"]) if row["assess_json"] else None
    return out


@app.get("/", response_class=HTMLResponse)
def index():
    return (STATIC / "app.html").read_text(encoding="utf-8")


@app.get("/api/domains")
def api_domains():
    return [{"id": d.id, "name": d.name, "enabled": d.enabled} for d in load_domains() if d.enabled]


@app.get("/api/today")
def api_today(domain_id: str):
    date_ = today_cn()
    cands = [_candidate_out(r) for r in list_candidates(domain_id, date_)]
    articles = []
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM articles WHERE domain_id=? AND status IN ('draft','confirmed','packaged')",
            (domain_id,),
        ).fetchall()
    for r in rows:
        articles.append({"id": r["id"], "title": r["title"], "status": r["status"]})
    return {"date": date_, "candidates": cands, "articles": articles}


@app.get("/api/candidates")
def api_candidates(domain_id: str, date: str | None = None):
    date_ = date or today_cn()
    return [_candidate_out(r) for r in list_candidates(domain_id, date_)]


@app.post("/api/candidates/{candidate_id}/decision")
def api_decision(candidate_id: int, body: DecisionBody):
    if body.decision not in ("pending", "selected", "rejected", "edited", "blocked"):
        raise HTTPException(400, "无效 decision")
    set_decision(candidate_id, body.decision, body.note)
    return {"ok": True}


@app.post("/api/candidates")
def api_add_candidate(body: ManualCandidate):
    domain = load_domain(body.domain_id)
    if domain is None:
        raise HTTPException(404, "领域不存在")
    from pipeline.db import insert_candidate

    # sha256 保证跨进程稳定（内置 hash 每次启动随机化，会导致重复插入）
    stable_id = hashlib.sha256(body.title.encode("utf-8")).hexdigest()[:16]
    cid = insert_candidate(
        {
            "domain_id": body.domain_id,
            "date": today_cn(),
            "source": "manual",
            "source_item_id": f"manual-{stable_id}",
            "title": body.title,
            "summary": body.note,
            "category": "",
            "source_score": None,
            "reason": body.note,
            "url": body.url,
            "created_at": today_cn(),
        }
    )
    return {"id": cid}


@app.get("/api/articles/{article_id}")
def api_article(article_id: int):
    art = get_article(article_id)
    if art is None:
        raise HTTPException(404, "文章不存在")
    out = dict(art)
    out["body"] = json.loads(art["body_json"]) if art["body_json"] else {}
    out["facts"] = json.loads(art["facts_json"]) if art["facts_json"] else []
    out["todo_verify"] = json.loads(art["todo_verify_json"]) if art["todo_verify_json"] else []
    out["feedback"] = [dict(r) for r in list_feedback(article_id)]
    return out


@app.post("/api/articles/{article_id}/feedback")
def api_feedback(article_id: int, body: FeedbackBody):
    for i, fb in enumerate(body.feedback, start=1):
        add_feedback(
            article_id,
            i,
            fb.get("scope", "whole"),
            fb.get("text", ""),
            fb.get("range_start"),
            fb.get("range_end"),
        )
    return {"ok": True}


@app.post("/api/articles/{article_id}/polish")
def api_polish(article_id: int):
    art = get_article(article_id)
    if art is None:
        raise HTTPException(404, "文章不存在")
    domain = load_domain(art["domain_id"])
    body = json.loads(art["body_json"]) if art["body_json"] else {}
    feedback = [dict(r) for r in list_feedback(article_id)]
    if not feedback:
        raise HTTPException(400, "没有待应用的批注")
    result = run_polish(domain, article_id, body, feedback)
    update_article(article_id, {"body_json": result, "title": result.get("title", art["title"]),
                                "version": art["version"] + 1, "status": "draft"})
    return {"ok": True, "title": result.get("title")}


@app.post("/api/articles/{article_id}/confirm")
def api_confirm(article_id: int):
    art = get_article(article_id)
    if art is None:
        raise HTTPException(404, "文章不存在")
    result = build_package_for_article(art["domain_id"], article_id)
    return result


@app.get("/api/packages/{package_id}/download")
def api_package_download(package_id: int):
    with get_conn() as conn:
        row = conn.execute("SELECT path FROM packages WHERE id=?", (package_id,)).fetchone()
    if row is None:
        raise HTTPException(404, "发布包不存在")
    return FileResponse(row["path"], filename=Path(row["path"]).name)
