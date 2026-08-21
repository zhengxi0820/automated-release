"""SQLite 数据访问层。"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from .config import DATA_DIR

DB_PATH = DATA_DIR / "pipeline.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS domains (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    enabled INTEGER NOT NULL DEFAULT 1,
    config_path TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS candidates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    domain_id TEXT NOT NULL,
    date TEXT NOT NULL,
    source TEXT NOT NULL,
    source_item_id TEXT NOT NULL,
    title TEXT NOT NULL,
    summary TEXT,
    category TEXT,
    source_score REAL,
    reason TEXT,
    url TEXT,
    assess_json TEXT,
    decision TEXT NOT NULL DEFAULT 'pending',
    user_note TEXT,
    created_at TEXT NOT NULL,
    UNIQUE(domain_id, date, source, source_item_id)
);

CREATE TABLE IF NOT EXISTS articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    domain_id TEXT NOT NULL,
    candidate_id INTEGER NOT NULL,
    title TEXT,
    status TEXT NOT NULL DEFAULT 'draft',
    angle TEXT,
    steelman_json TEXT,
    research_json TEXT,
    facts_json TEXT,
    todo_verify_json TEXT,
    body_json TEXT,
    version INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS article_feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id INTEGER NOT NULL,
    seq INTEGER NOT NULL,
    scope TEXT NOT NULL DEFAULT 'whole',
    range_start INTEGER,
    range_end INTEGER,
    text TEXT NOT NULL,
    applied_at TEXT
);

CREATE TABLE IF NOT EXISTS cards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id INTEGER NOT NULL,
    seq INTEGER NOT NULL,
    kind TEXT NOT NULL,
    text TEXT,
    image_path TEXT
);

CREATE TABLE IF NOT EXISTS packages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id INTEGER NOT NULL,
    path TEXT,
    size INTEGER,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    domain_id TEXT NOT NULL,
    date TEXT NOT NULL,
    stage TEXT,
    status TEXT NOT NULL DEFAULT 'running',
    log TEXT,
    started_at TEXT NOT NULL,
    finished_at TEXT
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
);

CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event TEXT NOT NULL,
    channel TEXT NOT NULL,
    payload TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    sent_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_candidates_domain_date ON candidates(domain_id, date);
CREATE INDEX IF NOT EXISTS idx_articles_domain_status ON articles(domain_id, status);
"""


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def get_conn() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    with get_conn() as conn:
        conn.executescript(SCHEMA)


def upsert_domain(domain_id: str, name: str, config_path: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO domains(id, name, enabled, config_path, created_at) VALUES(?,?,1,?,?)",
            (domain_id, name, config_path, now_iso()),
        )


def insert_candidate(c: dict) -> int:
    """c 为 NormalizedItem 转 dict + domain_id/date。返回 id。"""
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT OR IGNORE INTO candidates
               (domain_id, date, source, source_item_id, title, summary, category,
                source_score, reason, url, created_at)
               VALUES (:domain_id, :date, :source, :source_item_id, :title, :summary,
                       :category, :source_score, :reason, :url, :created_at)""",
            c,
        )
        if cur.rowcount == 0:
            row = conn.execute(
                "SELECT id FROM candidates WHERE domain_id=? AND date=? AND source=? AND source_item_id=?",
                (c["domain_id"], c["date"], c["source"], c["source_item_id"]),
            ).fetchone()
            return int(row["id"])
        return int(cur.lastrowid)


def set_assess(candidate_id: int, assess: dict) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE candidates SET assess_json=? WHERE id=?",
            (json.dumps(assess, ensure_ascii=False), candidate_id),
        )


def list_candidates(domain_id: str, date: str) -> list[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM candidates WHERE domain_id=? AND date=? ORDER BY id",
            (domain_id, date),
        ).fetchall()


def set_decision(candidate_id: int, decision: str, note: str = "") -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE candidates SET decision=?, user_note=? WHERE id=?",
            (decision, note, candidate_id),
        )


def create_article(candidate_id: int, domain_id: str) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO articles(domain_id, candidate_id, status, created_at, updated_at) VALUES(?,?,'draft',?,?)",
            (domain_id, candidate_id, now_iso(), now_iso()),
        )
        return int(cur.lastrowid)


def get_article(article_id: int) -> sqlite3.Row | None:
    with get_conn() as conn:
        return conn.execute("SELECT * FROM articles WHERE id=?", (article_id,)).fetchone()


def update_article(article_id: int, fields: dict) -> None:
    allowed = {
        "title", "status", "angle", "steelman_json", "research_json",
        "facts_json", "todo_verify_json", "body_json", "version",
    }
    sets = {k: v for k, v in fields.items() if k in allowed}
    if not sets:
        return
    sets = {k: (json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v) for k, v in sets.items()}
    sets["updated_at"] = now_iso()
    cols = ", ".join(f"{k}=?" for k in sets)
    with get_conn() as conn:
        conn.execute(f"UPDATE articles SET {cols} WHERE id=?", (*sets.values(), article_id))


def add_feedback(article_id: int, seq: int, scope: str, text: str, range_start=None, range_end=None) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO article_feedback(article_id, seq, scope, range_start, range_end, text) VALUES(?,?,?,?,?,?)",
            (article_id, seq, scope, range_start, range_end, text),
        )


def list_feedback(article_id: int) -> list[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM article_feedback WHERE article_id=? AND applied_at IS NULL ORDER BY seq",
            (article_id,),
        ).fetchall()


def mark_feedback_applied(article_id: int) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE article_feedback SET applied_at=? WHERE article_id=? AND applied_at IS NULL",
            (now_iso(), article_id),
        )


def insert_cards(article_id: int, cards: list[dict]) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM cards WHERE article_id=?", (article_id,))
        for i, c in enumerate(cards, start=1):
            conn.execute(
                "INSERT INTO cards(article_id, seq, kind, text) VALUES(?,?,?,?)",
                (article_id, i, c.get("kind", ""), c.get("text", "")),
            )


def set_card_image(article_id: int, seq: int, path: str) -> None:
    with get_conn() as conn:
        conn.execute("UPDATE cards SET image_path=? WHERE article_id=? AND seq=?", (path, article_id, seq))


def list_cards(article_id: int) -> list[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute("SELECT * FROM cards WHERE article_id=? ORDER BY seq", (article_id,)).fetchall()


def insert_package(article_id: int, path: str, size: int) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO packages(article_id, path, size, created_at) VALUES(?,?,?,?)",
            (article_id, path, size, now_iso()),
        )
        return int(cur.lastrowid)


def start_run(domain_id: str, date: str) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO runs(domain_id, date, stage, status, started_at) VALUES(?,?,?, 'running', ?)",
            (domain_id, date, "collect", now_iso()),
        )
        return int(cur.lastrowid)


def sweep_stale_runs(max_age_hours: float = 6.0) -> int:
    """把超过 max_age_hours 仍处于 running 的 run 标记为 failed（进程被杀/断电等场景）。"""
    cutoff = (datetime.now().astimezone() - timedelta(hours=max_age_hours)).isoformat(timespec="seconds")
    log = f"运行超时（超过 {max_age_hours:g} 小时），判定为中断"
    with get_conn() as conn:
        cur = conn.execute(
            "UPDATE runs SET status='failed', log=?, finished_at=? WHERE status='running' AND started_at < ?",
            (log, now_iso(), cutoff),
        )
        return cur.rowcount


def finish_run(run_id: int, status: str, stage: str = "", log: str = "") -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE runs SET status=?, stage=?, log=?, finished_at=? WHERE id=?",
            (status, stage, log, now_iso(), run_id),
        )


def get_setting(key: str, default: str = "") -> str:
    with get_conn() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return str(row["value"]) if row else default


def set_setting(key: str, value: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO settings(key, value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )
