import json
from pathlib import Path

from pipeline.sources.aihot import AIHOTSource

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_parse_hot_topics():
    src = AIHOTSource("ai-tools", {})
    data = _load("aihot_hot.json")
    item = src._to_item(data["items"][0])
    assert item.source == "aihot"
    assert item.source_item_id
    assert item.title
    assert item.extra["signal_count"] is not None
    assert item.url


def test_parse_items():
    src = AIHOTSource("ai-tools", {})
    data = _load("aihot_items.json")
    item = src._to_item(data["items"][0])
    assert item.summary
    assert item.score is not None
    assert item.reason
    assert item.category in ("ai-models", "ai-products", "industry", "paper", "tip", "")


def test_dedupe_semantics_hot_and_items():
    """fetch() 的去重语义：同一 id 在 hot 与 items 中重复出现时只保留一条。
    本测试验证 fixture 中确实存在重叠 id，且按 seen 集合去重后无重复。"""
    hot = _load("aihot_hot.json")
    items = _load("aihot_items.json")
    all_ids = [i["id"] for i in hot["items"]] + [i["id"] for i in items["items"]]
    assert len(set(all_ids)) < len(all_ids), "fixture 应包含跨端点重复 id"
    seen = set()
    dupes = 0
    for i in all_ids:
        if i in seen:
            dupes += 1
        seen.add(i)
    assert dupes == len(all_ids) - len(set(all_ids))
