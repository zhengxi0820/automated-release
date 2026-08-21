"""卡片 HTML → 3:4 PNG（Chrome headless 截图）。"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "render" / "templates" / "card.html"
OUTPUT_DIR = ROOT / "data" / "output"
CHROME = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")

KIND_LABELS = {
    "cover": "",
    "hook": "开场",
    "fact": "事实",
    "opinion": "观点",
    "case": "案例",
    "takeaway": "启示",
    "cta": "互动",
}


def _card_html(card: dict, seq: int, total: int, domain_name: str, tag: str) -> str:
    tpl = TEMPLATE.read_text(encoding="utf-8")
    kind = card.get("kind", "opinion")
    text = (card.get("text") or "").strip()
    subtext = (card.get("subtext") or "").strip()

    if kind == "cover":
        body = f'<div class="cover-title">{text}</div>'
        if subtext:
            body += f'<div class="cover-sub">{subtext}</div>'
    else:
        label = KIND_LABELS.get(kind, "")
        label_html = f'<div class="label">{label}</div>' if label else ""
        body = f'{label_html}<div class="body-text">{text}</div>'

    return (
        tpl.replace("{{kicker}}", domain_name)
        .replace("{{body}}", body)
        .replace("{{seq}}", str(seq))
        .replace("{{total}}", str(total))
        .replace("{{tag}}", tag)
    )


def render_article(domain_id: str, article_id: int, domain_name: str, cards: list[dict], tag: str) -> list[Path]:
    """渲染一组卡片，返回 PNG 路径列表。"""
    if not CHROME.exists():
        raise RuntimeError("未找到 Chrome，无法渲染卡片")
    out_dir = OUTPUT_DIR / domain_id / str(article_id)
    out_dir.mkdir(parents=True, exist_ok=True)

    total = len(cards)
    paths: list[Path] = []
    for i, card in enumerate(cards, start=1):
        html = _card_html(card, i, total, domain_name, tag)
        html_path = out_dir / f"card_{i:02d}.html"
        png_path = out_dir / f"card_{i:02d}.png"
        html_path.write_text(html, encoding="utf-8")
        cmd = [
            str(CHROME),
            "--headless=new",
            "--disable-gpu",
            "--hide-scrollbars",
            "--window-size=1080,1440",
            f"--screenshot={png_path}",
            html_path.as_uri(),
        ]
        subprocess.run(cmd, check=True, capture_output=True, timeout=60)
        paths.append(png_path)
    return paths
