"""概念科普链路测试：concept_write 阶段 + run_concept 编排（FakeProvider，不触网）。"""

import pytest

from pipeline.config import load_domain
from pipeline.db import get_article, list_candidates
from pipeline.llm.fake import FakeProvider
from pipeline.orchestrator import pop_concept, run_concept
from pipeline.stages.concept_write import run_concept_write

CONCEPT_DRAFT = {
    "title": "越存越穷？借鸡蛋的故事",
    "body": [
        {"type": "hook", "text": "村口的阿婆把鸡蛋存了十年，反而更穷了。"},
        {"type": "story", "text": "从前有个村子，鸡蛋可以借出去生小鸡。"},
        {"type": "reveal", "text": "这就是复利：利息也开始生利息。"},
        {"type": "explain", "text": "故事里的鸡蛋就是本金，借出去的蛋是利息。"},
        {"type": "extend", "text": "懂了这个，你会重新看待长期存款。"},
        {"type": "cta", "text": "你身边有靠复利改变处境的例子吗？"},
    ],
    "tags": ["#理财科普"],
    "self_check": {"zero_jargon": "pass"},
}


@pytest.fixture()
def concept_domain(tmp_db, monkeypatch):
    """给 tmp 数据库造一个 concept 领域配置。"""
    d = load_domain("ai-basics")
    assert d is not None and d.content_type == "concept"
    return d


def test_run_concept_write_shapes_prompt(concept_domain, monkeypatch):
    captured = {}

    def fake_chat(self, prompt, system="", json_mode=True, temperature=0.6, max_tokens=4096):
        captured["prompt"] = prompt
        captured["max_tokens"] = max_tokens
        return CONCEPT_DRAFT

    monkeypatch.setattr("pipeline.llm.deepseek.DeepSeekProvider.chat", fake_chat)
    result = run_concept_write(concept_domain, "复利")
    assert result["title"] == "越存越穷？借鸡蛋的故事"
    assert "复利" in captured["prompt"]
    assert "2800" in captured["prompt"] or "2600" in captured["prompt"]  # 字数契约注入
    assert captured["max_tokens"] == 8192


def test_run_concept_write_rewrites_on_fabrication(concept_domain, monkeypatch):
    calls = []

    def fake_chat(self, prompt, system="", json_mode=True, temperature=0.6, max_tokens=4096):
        calls.append(prompt)
        if len(calls) == 1:
            return {**CONCEPT_DRAFT, "body": [{"type": "hook", "text": "我实测了这个概念，很神奇。"}]}
        return CONCEPT_DRAFT

    monkeypatch.setattr("pipeline.llm.deepseek.DeepSeekProvider.chat", fake_chat)
    result = run_concept_write(concept_domain, "复利")
    assert len(calls) == 2  # 触发纠错重写
    assert result["self_check"]["no_fabricated_experience"] == "pass"


def test_run_concept_end_to_end_draft(tmp_db, concept_domain, monkeypatch):
    monkeypatch.setattr("pipeline.stages.concept_write.get_provider",
                        lambda name, model=None: FakeProvider(CONCEPT_DRAFT))
    result = run_concept(concept_domain.id, concept="复利", date="2026-09-03", until="draft")

    art = get_article(result["article_id"])
    assert art is not None and art["status"] == "draft"
    assert art["title"] == "越存越穷？借鸡蛋的故事"
    rows = list_candidates(concept_domain.id, "2026-09-03")
    assert rows[0]["source"] == "concept"
    assert rows[0]["decision"] == "selected"


def test_pop_concept_pops_from_pool_top(tmp_path, monkeypatch):
    pool = tmp_path / "test-domain.txt"
    pool.write_text("# 注释行\n\n复利\n通货膨胀\n", encoding="utf-8")
    monkeypatch.setattr("pipeline.config.ROOT", tmp_path.parent)

    # pop_concept 用 ROOT / "concepts" 拼路径，把池文件放到 <root>/concepts/
    (tmp_path.parent / "concepts").mkdir(exist_ok=True)
    pool.rename(tmp_path.parent / "concepts" / "test-domain.txt")

    first = pop_concept("test-domain")
    second = pop_concept("test-domain")
    assert first == "复利"
    assert second == "通货膨胀"
    remaining = (tmp_path.parent / "concepts" / "test-domain.txt").read_text(encoding="utf-8")
    assert "复利" not in remaining and "通货膨胀" not in remaining
    used = (tmp_path.parent / "concepts" / "test-domain.used.txt").read_text(encoding="utf-8")
    assert "复利" in used and "通货膨胀" in used


def test_pop_concept_explicit_override():
    assert pop_concept("any-domain", concept="指定概念") == "指定概念"
