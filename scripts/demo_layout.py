"""演示脚本：从 AIHOT 挑故事链最完整的一篇，走调研→钢人化→成文→卡片→渲染→发布包。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pipeline.config import load_domain  # noqa: E402
from pipeline.sources.aihot import AIHOTSource  # noqa: E402
from pipeline.stages.cardify import run_cardify  # noqa: E402
from pipeline.stages.research import run_research  # noqa: E402
from pipeline.stages.steelman import run_steelman  # noqa: E402
from pipeline.stages.write import run_write  # noqa: E402
from render.package import build_package  # noqa: E402
from render.render_cards import render_article  # noqa: E402


def pick_best_story(src: AIHOTSource):
    hot = src._get("/hot-topics")
    best, best_len = None, 0
    for it in hot.get("items", []):
        story_url = (it.get("links") or {}).get("story", "")
        sid = story_url.rstrip("/").split("/")[-1]
        if not sid:
            continue
        try:
            st = src.fetch_story(f"/stories/{sid}")
            dlen = len(st.get("digest") or "")
            if dlen > best_len:
                best_len, best = dlen, (it, st)
        except Exception:  # noqa: BLE001
            continue
    return best, best_len


def main() -> None:
    domain = load_domain("ai-tools")
    src = AIHOTSource(domain.id, {})
    (it, story), dlen = pick_best_story(src)
    if it is None:
        print("未找到可用故事")
        return

    links = it.get("links", {})
    cand = {
        "title": it.get("title", ""),
        "summary": story.get("digest", "")[:500],
        "reason": f"信号源 {it.get('sourceCount')} 个 · AIHOT 编辑推荐",
        "url": links.get("original", ""),
        "category": "ai-products",
        "extra": {"story_url": links.get("story", "")},
    }
    print(f"选中：{cand['title']}（故事摘要 {dlen} 字）")

    research = run_research(domain, cand)
    steelman = run_steelman(domain, cand, research)
    body = run_write(domain, cand, research, steelman)
    cards = run_cardify(domain, body)

    out_root = ROOT / "data" / "output" / "ai-tools" / "demo"
    out_root.mkdir(parents=True, exist_ok=True)
    tags = body.get("tags", [])
    tag = tags[0] if tags else "#AI工具"
    pngs = render_article(domain.id, "demo", domain.name, cards, tag)
    todo = [t.get("claim", str(t)) if isinstance(t, dict) else str(t) for t in body.get("todo_verify", [])]
    zip_path = build_package(domain.id, "demo", body.get("title", ""), body, tags, todo, pngs)

    print("标题:", body.get("title"))
    print("段落数:", len(body.get("body", [])))
    print("卡片数:", len(cards))
    print("PNG:", [str(p) for p in pngs])
    print("发布包:", zip_path)


if __name__ == "__main__":
    main()
