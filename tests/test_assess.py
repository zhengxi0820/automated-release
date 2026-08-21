from pipeline.config import load_domain
from pipeline.db import insert_candidate, list_candidates, set_assess
from pipeline.llm.fake import FakeProvider
from pipeline.stages.assess import run_assess

RESP = {
    "total": 7.4,
    "dimensions": {"heat": 2, "controversy": 1, "domain_match": 2, "writable": 1, "risk": 0},
    "verdict": "worth_discussing",
    "one_line": "GLM-5.3 发布，对普通人换模型成本有实际影响",
    "suggested_angle": "普通人要不要换？",
    "risk_note": "",
}


def _patch_provider(monkeypatch, resp):
    monkeypatch.setattr("pipeline.stages.assess.get_provider", lambda name, model=None: FakeProvider(resp))


def _insert(d, item_id, **over):
    rec = {
        "domain_id": d.id,
        "date": "2026-08-15",
        "source": "aihot",
        "source_item_id": item_id,
        "title": "GLM-5.3 发布",
        "summary": "编程能力开源第一",
        "category": "ai-models",
        "source_score": 82,
        "reason": "值得关注",
        "url": "https://example.com",
        "created_at": "2026-08-15T08:00:00+08:00",
    }
    rec.update(over)
    insert_candidate(rec)


def test_assess_worth_discussing(tmp_db, monkeypatch):
    _patch_provider(monkeypatch, RESP)
    d = load_domain("ai-tools")
    _insert(d, "test-1")
    kept = run_assess(d, "2026-08-15")
    assert len(kept) == 1
    assert kept[0]["assess"]["total"] == 7.4
    rows = list_candidates(d.id, "2026-08-15")
    assert rows[0]["assess_json"] is not None


def test_assess_blocked(tmp_db, monkeypatch):
    blocked = {**RESP, "verdict": "blocked", "total": 0.0}
    _patch_provider(monkeypatch, blocked)
    d = load_domain("ai-tools")
    _insert(d, "test-2", title="某医疗 AI 事件", category="health")
    kept = run_assess(d, "2026-08-15")
    assert kept == []


def test_assess_below_min_score_dropped(tmp_db, monkeypatch):
    low = {**RESP, "total": 5.0}  # ai-tools min_score=6.0
    _patch_provider(monkeypatch, low)
    d = load_domain("ai-tools")
    _insert(d, "test-3")
    assert run_assess(d, "2026-08-15") == []


def test_assess_high_risk_dropped(tmp_db, monkeypatch):
    risky = {**RESP, "dimensions": {**RESP["dimensions"], "risk": 2}}  # risk_max_for_keep=1
    _patch_provider(monkeypatch, risky)
    d = load_domain("ai-tools")
    _insert(d, "test-4")
    assert run_assess(d, "2026-08-15") == []
