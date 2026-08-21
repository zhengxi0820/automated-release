"""runs 表过期清理的回归测试。"""

from datetime import datetime, timedelta

import pipeline.db as db


def test_sweep_marks_old_running_as_failed(tmp_db):
    run_id = db.start_run("ai-tools", "2026-08-01")
    old = (datetime.now().astimezone() - timedelta(hours=7)).isoformat(timespec="seconds")
    with db.get_conn() as conn:
        conn.execute("UPDATE runs SET started_at=? WHERE id=?", (old, run_id))

    swept = db.sweep_stale_runs(max_age_hours=6)

    assert swept == 1
    with db.get_conn() as conn:
        row = conn.execute("SELECT status, log FROM runs WHERE id=?", (run_id,)).fetchone()
    assert row["status"] == "failed"
    assert "中断" in row["log"]


def test_sweep_keeps_fresh_running(tmp_db):
    run_id = db.start_run("ai-tools", "2026-08-01")

    assert db.sweep_stale_runs(max_age_hours=6) == 0

    with db.get_conn() as conn:
        row = conn.execute("SELECT status FROM runs WHERE id=?", (run_id,)).fetchone()
    assert row["status"] == "running"
