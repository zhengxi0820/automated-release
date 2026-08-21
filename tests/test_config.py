from pipeline.config import load_domain


def test_load_ai_tools_domain():
    d = load_domain("ai-tools")
    assert d is not None
    assert d.name == "AI 工具与效率"
    assert d.enabled is True
    assert d.assess_weights["domain_match"] == 0.25
    assert d.provider == "deepseek"
    assert d.persona
    assert d.angles
    assert "aihot" in [s["name"] for s in d.sources]
