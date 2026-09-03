"""书页式连续排版引擎（生产）。

设计定稿参数见 docs/卡片排版规范.md。流程：
sections（标题+段落）→ em 折行（含避头尾）→ 分页（孤行保护）→ 逐页 HTML → Chrome 截图 PNG。

纯函数部分（em_len/wrap/build_units/paginate）不依赖 Chrome，可直接单测。
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "data" / "output"
CHROME = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")

FORBIDDEN_START = set("，。、；：？！」』）】〉》…,.;:?!)]}")
FORBIDDEN_END = set("（「『【〈《([{“‘")


@dataclass
class Layout:
    """排版参数（默认值 = ai-tools 定稿值），可被领域配置覆盖。"""

    w: int = 1080
    h: int = 1800
    f_body: int = 42
    f_head: int = 50
    w_body: int = 600
    w_head: int = 800
    lh_body: int = 76
    lh_head: int = 80
    para_gap: int = 30        # 段距 106 = lh_body + 30
    head_before: int = 74
    head_after: int = 37
    pad_x: int = 78
    pad_top: int = 80
    pad_bottom: int = 120
    ink: str = "#000000"
    track: float = 0.04       # em
    font_stack: str = '"Noto Serif SC", "Source Han Serif SC", "SimSun", serif'
    google_fonts: bool = True

    def __post_init__(self) -> None:
        adv = self.f_body * (1 + self.track)
        self.line_cap = float(int((self.w - self.pad_x * 2) / adv))
        self.head_cap = float(int((self.w - self.pad_x * 2) / (self.f_head * (1 + self.track))))
        self.content_h = self.h - self.pad_top - self.pad_bottom

    CSS_TEMPLATE = """
:root {{
  --ink: {ink}; --ink-2: #6E6E73; --ink-3: #86868B;
  --hairline: #D2D2D7; --hl-yellow: rgba(255,204,0,.40);
  --serif: {font_stack};
}}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
html, body {{ width: {w}px; height: {h}px; overflow: hidden; background: #FFFFFF; }}
body {{
  font-family: var(--serif); color: var(--ink);
  display: flex; flex-direction: column;
  padding: {pt}px {px}px {pb}px;
}}
main {{ flex: 1; }}
.hln {{ font-size: {fh}px; line-height: {lhh}px; font-weight: {wh}; letter-spacing: {tr}em; }}
.pln {{ font-size: {fb}px; line-height: {lhb}px; font-weight: {wb}; letter-spacing: {tr}em; text-align: justify; text-align-last: justify; }}
.pln.last {{ text-align-last: auto; }}
.lede {{ font-size: 30px; color: #6E6E73; letter-spacing: .12em; font-weight: 400; margin-bottom: 40px; }}
.cover-title {{ font-size: 84px; line-height: 1.34; font-weight: 900; letter-spacing: .02em; }}
.cover-title u {{ text-decoration: none; border-bottom: 14px solid var(--hl-yellow); padding-bottom: 8px; }}
.toc {{ margin-top: 70px; }}
.toc-item {{ display: flex; align-items: baseline; gap: 26px; padding: 26px 0; border-top: 1.5px solid var(--hairline); }}
.toc-item:first-child {{ border-top: none; }}
.toc-item .no {{ font-size: 42px; font-weight: 700; color: var(--ink); }}
.toc-item .what {{ font-size: 40px; font-weight: 600; }}
"""

    def css(self) -> str:
        return self.CSS_TEMPLATE.format(
            ink=self.ink, font_stack=self.font_stack, w=self.w, h=self.h,
            px=self.pad_x, pt=self.pad_top, pb=self.pad_bottom,
            fb=self.f_body, fh=self.f_head, lhb=self.lh_body, lhh=self.lh_head,
            wb=self.w_body, wh=self.w_head, tr=self.track,
        )


CN_NUM = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十"]


def em_len(ch: str) -> float:
    """字符 em 宽度保守估计（拉丁取偏宽值，防止浏览器二次折行）。"""
    o = ord(ch)
    if o < 128:
        if ch == " ":
            return 0.32
        if ch in ".,:;!?'\"()":
            return 0.36
        if ch in "mwMW":
            return 0.85
        return 0.62
    return 1.0


def wrap(text: str, cap: float) -> list[str]:
    """折行 + 避头尾：行首禁则标点连锁下推（最多 3 字），行末不悬开引号，破折号成对不拆。"""
    lines: list[str] = []
    cur, curw = "", 0.0
    for ch in text:
        wch = em_len(ch)
        if cur and curw + wch > cap:
            if ch in FORBIDDEN_START and len(cur) >= 2:
                push, k = "", 0
                while cur and k < 3 and (k == 0 or push[0] in FORBIDDEN_START):
                    push = cur[-1] + push
                    cur = cur[:-1]
                    k += 1
                if cur:
                    lines.append(cur)
                cur, curw = push + ch, sum(em_len(c) for c in push) + wch
            elif ch == "—" and cur.endswith("—"):
                lines.append(cur[:-1])
                cur, curw = "——", 2.0
            else:
                if cur[-1] in FORBIDDEN_END:
                    lines.append(cur[:-1])
                    cur, curw = cur[-1] + ch, em_len(cur[-1]) + wch
                else:
                    lines.append(cur)
                    cur, curw = ch, wch
        else:
            cur += ch
            curw += wch
    if cur:
        lines.append(cur)
    return lines


def build_units(sections: list[dict], L: Layout, use_headings: bool = True) -> list[dict]:
    """sections: [{heading: str, paragraphs: [str]}] → 排版单元流。"""
    units: list[dict] = []
    for i, sec in enumerate(sections):
        if use_headings and i > 0:
            units.append({"kind": "gap", "h": L.head_before})
        if use_headings:
            head = sec.get("heading") or ""
            if head:
                no = CN_NUM[i] + "、" if i < len(CN_NUM) else f"{i + 1}."
                head_text = head if head.startswith(no) else f"{no}{head}"
                units.append({"kind": "h", "lines": wrap(head_text, L.head_cap - 0.3)})
                units.append({"kind": "gap", "h": L.head_after})
        for j, p in enumerate(sec.get("paragraphs") or []):
            if j > 0:
                units.append({"kind": "gap", "h": L.para_gap})
            units.append({"kind": "p", "lines": wrap(p, L.line_cap)})
    return units


def unit_height(u: dict, L: Layout) -> int:
    if u["kind"] == "h":
        return len(u["lines"]) * L.lh_head
    if u["kind"] == "p":
        return len(u["lines"]) * L.lh_body
    return u["h"]


def paginate(units: list[dict], L: Layout) -> list[list[dict]]:
    """行级连续流分页：段落可跨页续排（真书页流）；页首不带段前距；
    标题不落卡底（后随至少 2 行）；段落首行不孤悬页底（至少 2 行同页）。"""
    items: list[dict] = []
    for u in units:
        if u["kind"] == "gap":
            items.append({"t": "gap", "h": u["h"]})
        elif u["kind"] == "h":
            for ln in u["lines"]:
                items.append({"t": "h", "ln": ln})
        else:
            n = len(u["lines"])
            for k, ln in enumerate(u["lines"]):
                items.append({"t": "p", "ln": ln, "first": k == 0})

    pages: list[list[dict]] = []
    cur: list[dict] = []
    used = 0
    pending_gap = 0

    def flush() -> None:
        nonlocal cur, used, pending_gap
        if cur:
            pages.append(cur)
        cur, used = [], 0
        pending_gap = 0

    i, n = 0, len(items)
    while i < n:
        it = items[i]
        if it["t"] == "gap":
            pending_gap += it["h"]
            i += 1
            continue
        h = L.lh_head if it["t"] == "h" else L.lh_body
        need_gap = pending_gap if cur else 0  # 页首不带段前距
        if it["t"] == "h":
            if cur and used + need_gap + h + L.head_after + 2 * L.lh_body > L.content_h:
                flush()
                continue
        elif it["first"] and cur and used + need_gap + 2 * L.lh_body > L.content_h:
            flush()  # 段落首行放不下 2 行：整段从下页起
            continue
        if used + need_gap + h <= L.content_h:
            if need_gap:
                cur.append({"kind": "gap", "h": need_gap})
                used += need_gap
            cur.append({"kind": it["t"], "lines": [it["ln"]]})
            used += h
            pending_gap = 0
        else:
            flush()
            continue
        i += 1
    flush()

    # 合并相邻同类条目（gap 分隔不同段落/标题）
    merged: list[list[dict]] = []
    for pg in pages:
        out: list[dict] = []
        for it in pg:
            if it["kind"] == "gap":
                out.append({"kind": "gap", "h": it["h"]})
                continue
            if out and out[-1]["kind"] == it["kind"]:
                out[-1]["lines"].extend(it["lines"])
            else:
                out.append({"kind": it["kind"], "lines": list(it["lines"])})
        merged.append(out)
    return merged


def _page_html(L: Layout, body: str, font_link: str) -> str:
    fonts = (
        '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
        '<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">'
    ) if font_link else ""
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
{fonts}
<style>{L.css()}</style>
</head>
<body>
{body}
</body>
</html>"""


def cover_html(L: Layout, title: str, headings: list[str], lede: str = "") -> str:
    items = ""
    for i, h in enumerate(headings):
        h = h.strip()
        if h.startswith(CN_NUM[i] + "、" if i < len(CN_NUM) else f"{i + 1}."):
            no, what = h.split("、", 1)[0] + "、", h.split("、", 1)[1]
        else:
            no = (CN_NUM[i] + "、") if i < len(CN_NUM) else f"{i + 1}."
            what = h
        items += f'<div class="toc-item"><span class="no">{no}</span><span class="what">{what}</span></div>'
    lede_html = f'<p class="lede">{lede}</p>' if lede else ""
    title_lines = title.split("\n")[:2]
    title_html = "<br>".join(title_lines)
    body = f"""
<main style="flex:1;display:flex;flex-direction:column;justify-content:center">
  {lede_html}
  <h1 class="cover-title">{title_html}</h1>
  <div class="toc">{items}</div>
</main>"""
    return _page_html(L, body, L.google_fonts)


def flow_page_html(L: Layout, units: list[dict], font_link: bool = True) -> str:
    out: list[str] = ["<main>"]
    for u in units:
        if u["kind"] == "gap":
            out.append(f'<div style="height:{u["h"]}px"></div>')
        elif u["kind"] == "h":
            for ln in u["lines"]:
                out.append(f'<div class="hln">{ln}</div>')
        else:
            n = len(u["lines"])
            for k, ln in enumerate(u["lines"]):
                out.append(f'<div class="{"pln last" if k == n - 1 else "pln"}">{ln}</div>')
    out.append("</main>")
    return _page_html(L, "\n".join(out), font_link)


def render_flow_pages(
    domain_id: str,
    article_id: int,
    sections: list[dict],
    title: str,
    layout: Layout,
    use_headings: bool = True,
) -> list[Path]:
    """分页 + 渲染 PNG，返回图片路径列表。纯 HTML 生成失败不涉及 Chrome。"""
    if not CHROME.exists():
        raise RuntimeError("未找到 Chrome，无法渲染卡片")
    headings = [s.get("heading", "") for s in sections if s.get("heading")]
    pages_units = paginate(build_units(sections, layout, use_headings), layout)

    out_dir = OUTPUT_DIR / domain_id / str(article_id)
    out_dir.mkdir(parents=True, exist_ok=True)

    shots: list[tuple[str, str]] = []
    if use_headings and headings:
        shots.append(("page_01", cover_html(layout, title, headings)))
        start = 2
    else:
        shots.append(("page_01", flow_page_html(layout, pages_units[0] if pages_units else [])))
        pages_units = pages_units[1:]
        start = 2
    for i, units in enumerate(pages_units, start=start):
        shots.append((f"page_{i:02d}", flow_page_html(layout, units)))

    paths: list[Path] = []
    for name, html in shots:
        html_path = out_dir / f"{name}.html"
        html_path.write_text(html, encoding="utf-8")
        png_path = out_dir / f"{name}.png"
        if png_path.exists():
            png_path.unlink()
        cmd = [
            str(CHROME), "--headless=new", "--disable-gpu", "--hide-scrollbars",
            f"--window-size={layout.w},{layout.h}", "--virtual-time-budget=10000",
            f"--screenshot={png_path}", html_path.as_uri(),
        ]
        subprocess.run(cmd, check=True, capture_output=True, timeout=90)
        if not png_path.exists():
            raise RuntimeError(f"Chrome 未产出截图: {png_path.name}")
        from PIL import Image, ImageCms
        im = Image.open(png_path)
        im.save(png_path, icc_profile=ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes())
        paths.append(png_path)
    return paths


def article_text(sections: list[dict], use_headings: bool = True) -> str:
    """sections → 纯文本（publish.txt 用）。"""
    parts: list[str] = []
    for i, sec in enumerate(sections):
        head = sec.get("heading") or ""
        if head and use_headings:
            no = CN_NUM[i] + "、" if i < len(CN_NUM) else f"{i + 1}."
            parts.append(head if head.startswith(no) else f"{no}{head}")
        parts.extend(sec.get("paragraphs") or [])
    return "\n\n".join(parts)
