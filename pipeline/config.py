"""领域配置加载与环境变量。"""

from __future__ import annotations

import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
DOMAINS_DIR = ROOT / "domains"
DATA_DIR = ROOT / "data"
PROMPTS_DIR = ROOT / "prompts"

load_dotenv(ROOT / ".env")


class DomainConfig:
    """单个领域的配置对象。所有阶段只读本对象，不硬编码领域逻辑。"""

    def __init__(self, data: dict):
        self.data = data
        self.id: str = data["id"]
        self.name: str = data.get("name", self.id)
        self.enabled: bool = data.get("enabled", True)
        self.schedule: dict = data.get("schedule", {})
        self.sources: list = data.get("sources", [])
        self.assess: dict = data.get("assess", {})
        self.llm: dict = data.get("llm", {})
        self.writing: dict = data.get("writing", {})
        self.compliance: dict = data.get("compliance", {})
        self.notify: dict = data.get("notify", {})
        self.dir = DOMAINS_DIR / self.id
        self.persona = self._read("persona.md")
        self.angles = self._read("angles.md")

    def _read(self, name: str) -> str:
        p = self.dir / name
        return p.read_text(encoding="utf-8") if p.exists() else ""

    @property
    def provider(self) -> str:
        return self.llm.get("provider", "deepseek")

    @property
    def model(self) -> str:
        return self.llm.get("model", "deepseek-chat")

    @property
    def temperature(self) -> float:
        return self.llm.get("temperature", 0.6)

    @property
    def assess_weights(self) -> dict:
        return self.assess.get(
            "weights",
            {"heat": 0.3, "controversy": 0.2, "domain_match": 0.25, "writable": 0.15, "risk": 0.1},
        )

    @property
    def min_score(self) -> float:
        return float(self.assess.get("min_score", 6.0))

    @property
    def candidate_budget(self) -> int:
        return int(self.assess.get("candidate_budget", 10))

    @property
    def daily_select_max(self) -> int:
        return int(self.assess.get("daily_select_max", 2))

    @property
    def card_count(self) -> tuple[int, int]:
        w = self.writing
        return int(w.get("card_count_min", 5)), int(w.get("card_count_max", 7))

    # ── 书页式连续排版（cardify.mode = flow）──

    @property
    def cardify_mode(self) -> str:
        """flow = 书页连续排版（默认）；legacy = 旧单卡模板。"""
        return self.data.get("cardify", {}).get("mode", "flow")

    @property
    def use_headings(self) -> bool:
        """True = 分节大标题模式；False = 散文模式。"""
        return bool(self.data.get("cardify", {}).get("use_headings", True))

    @property
    def section_count(self) -> int:
        return int(self.data.get("cardify", {}).get("section_count", 5))

    @property
    def canvas(self) -> tuple[int, int]:
        c = self.data.get("cardify", {}).get("canvas", {})
        return int(c.get("width", 1080)), int(c.get("height", 1800))

    @property
    def flow_layout_overrides(self) -> dict:
        """领域可覆盖排版参数（键同 render.flow_cards.Layout 字段）。"""
        return dict(self.data.get("cardify", {}).get("layout", {}))

    @property
    def writing_min_length(self) -> int:
        return int(self.writing.get("min_length", 2800))

    @property
    def writing_disclaimer(self) -> str:
        return str(self.writing.get("disclaimer", "") or "")

    @property
    def content_type(self) -> str:
        """hotspot = 热点评论（默认）；concept = 概念科普。"""
        return str(self.data.get("content_type", "hotspot"))

    @property
    def max_tokens(self) -> int:
        return int(self.llm.get("max_tokens", 8192))

    @property
    def title_max_chars(self) -> int:
        return int(self.writing.get("title_max_chars", 20))

    @property
    def writing_max_length(self) -> int:
        return int(self.writing.get("max_length", 800))

    @property
    def block_categories(self) -> list:
        return list(self.compliance.get("block_categories", []))

    @property
    def block_keywords(self) -> list:
        return list(self.compliance.get("block_keywords", []))

    @property
    def require_ai_label(self) -> bool:
        return bool(self.compliance.get("require_ai_label", True))


def load_domains() -> list[DomainConfig]:
    out: list[DomainConfig] = []
    if not DOMAINS_DIR.exists():
        return out
    for d in sorted(DOMAINS_DIR.iterdir()):
        cfg = d / "config.yaml"
        if d.is_dir() and cfg.exists():
            try:
                data = yaml.safe_load(cfg.read_text(encoding="utf-8"))
                out.append(DomainConfig(data))
            except Exception as exc:  # noqa: BLE001
                print(f"[config] 跳过 {d.name}: {exc}")
    return out


def load_domain(domain_id: str) -> DomainConfig | None:
    for d in load_domains():
        if d.id == domain_id:
            return d
    return None


def env(key: str, default: str = "") -> str:
    return os.environ.get(key, default)
