"""设计预览 v5：C5 参考图对齐版——同排版参数、双画幅对比（3:4 vs 3:5）。

用法：python design/render_preview_c5.py
输出：design/preview/c5_34/page_*.png（1080x1440）
      design/preview/c5_35/page_*.png（1080x1800）

排版参数（像素测量参考图得出，两版共用）：
- 思源宋体，正文 42px/600、标题 50px/800
- 行距 74px（1.76 倍字号，与参考图一致）
- 段间 29px（段落首尾距 103px = 1.4 倍行距，非整行空行）
- 标题前 74px / 标题后 37px
- 边距 78px，版心 22 字/行，两端对齐
- 无页码页脚；标题跨卡内联接力 + 孤行保护

文章正文复用 render_preview_c4.SECTIONS（3032 字）。
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from render_preview_c4 import PROSE_PARAS, SECTIONS  # noqa: E402

OUT_ROOT = Path(__file__).resolve().parent / "preview"
CHROME = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")

BRAND = "AI 工具观察"
DATE = "08.21"

FONTS = """<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">"""


class Layout:
    def __init__(self, w: int, h: int):
        self.w, self.h = w, h
        self.f_body, self.f_head = 42, 50
        self.lh_body, self.lh_head = 76, 80   # 行距 76（用户定稿）
        self.para_gap = 30        # 段距 106 = 76 + 30（用户定稿）
        self.head_before, self.head_after = 74, 37
        self.pad_x = 78
        self.pad_top = 82         # 上留白 82 = 92-5-5（用户定稿）
        self.pad_bottom = 79      # 下留白 79 = 64+5+10（用户定稿）
        self.ink = "#000000"      # 纯黑（参考图墨色灰度值 5，#1D1D1F 偏灰发软）
        self.w_body, self.w_head = 600, 800   # 正文 600（用户定稿）
        self.track = 0.04         # 微字距：字间透光的呼吸感
        self.line_cap = float(int((w - self.pad_x * 2) / (self.f_body * (1 + self.track))))  # 21
        self.head_cap = float(int((w - self.pad_x * 2) / (self.f_head * (1 + self.track))))  # 17
        self.content_h = h - self.pad_top - self.pad_bottom

    CSS = """
:root {{
  --ink: {ink}; --ink-2: #6E6E73; --ink-3: #86868B;
  --hairline: #D2D2D7; --hl-yellow: rgba(255,204,0,.40);
  --serif: "Noto Serif SC", "Source Han Serif SC", "SimSun", serif;
}}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
html, body {{ width: {w}px; height: {h}px; overflow: hidden; }}
body {{
  font-family: var(--serif); background: #FFFFFF; color: var(--ink);
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


FORBIDDEN_START = set("，。、；：？！」』）】〉》…,.;:?!)]}")
FORBIDDEN_END = set("（「『【〈《([{“‘")


def em_len(ch: str) -> float:
    o = ord(ch)
    if o < 128:
        if ch == " ":
            return 0.32
        if ch in ".,:;!?'\"()":
            return 0.36
        if ch in "mwMW":
            return 0.85
        return 0.62  # 宋体拉丁小写在 0.55-0.7em 之间，取保守值防溢出
    return 1.0


def wrap(text: str, cap: float) -> list[str]:
    """折行 + 避头尾：新行首若是禁则标点，把上一行末字符推下来；
    推下来的字若仍是标点（如「说。】）则连锁下推；破折号成对不拆行。"""
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
                    # 行末不能悬开引号/开括号，推到下一行
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


def build_units(L: Layout, sections, use_headings=True) -> list[dict]:
    units: list[dict] = []
    for i, (head, paras) in enumerate(sections):
        if use_headings and i > 0:
            units.append({"kind": "gap", "h": L.head_before})
        if use_headings:
            units.append({"kind": "h", "lines": wrap(head, L.head_cap - 0.3)})
            units.append({"kind": "gap", "h": L.head_after})
        for j, p in enumerate(paras):
            if j > 0:
                units.append({"kind": "gap", "h": L.para_gap})
            units.append({"kind": "p", "lines": wrap(p, L.line_cap)})
    return units


def unit_height(L: Layout, u: dict) -> int:
    if u["kind"] == "h":
        return len(u["lines"]) * L.lh_head
    if u["kind"] == "p":
        return len(u["lines"]) * L.lh_body
    return u["h"]


def paginate(L: Layout, units: list[dict]) -> list[list[dict]]:
    pages, cur, used = [], [], 0

    def flush():
        nonlocal cur, used
        if cur:
            pages.append(cur)
        cur, used = [], 0

    i = 0
    while i < len(units):
        u = units[i]
        hgt = unit_height(L, u)
        if u["kind"] == "h":
            lookahead = hgt + L.head_after + 2 * L.lh_body  # 标题后至少 2 行正文
            if cur and used + lookahead > L.content_h:
                flush()
                continue
        if not cur:
            cur, used = [u], hgt
        elif used + hgt <= L.content_h:
            cur.append(u)
            used += hgt
        else:
            flush()
            continue  # 放不下：翻页重试，不丢弃
        i += 1
    flush()
    return pages


def page_html(L: Layout, body: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
{FONTS}
<style>{L.CSS.format(w=L.w, h=L.h, px=L.pad_x, pt=L.pad_top, pb=L.pad_bottom,
                      fb=L.f_body, fh=L.f_head, lhb=L.lh_body, lhh=L.lh_head,
                      ink=L.ink, wb=L.w_body, wh=L.w_head, tr=L.track)}</style>
</head>
<body>
{body}
</body>
</html>"""


def flow_page_html(L: Layout, units: list[dict]) -> str:
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
    return page_html(L, "\n".join(out))


def cover_html(L: Layout) -> str:
    items = "".join(
        f'<div class="toc-item"><span class="no">{h.split("、")[0]}、</span><span class="what">{h.split("、", 1)[1]}</span></div>'
        for h, _ in SECTIONS
    )
    body = f"""
<main style="flex:1;display:flex;flex-direction:column;justify-content:center">
  <p class="lede">AI 圈疯传的 DeepSeek 更新 · {DATE}</p>
  <h1 class="cover-title">V4 Pro <u>悄悄上线</u>，<br>普通人先别急着换</h1>
  <div class="toc">{items}</div>
</main>"""
    return page_html(L, body)


def render_version(tag: str, w: int, h: int) -> None:
    L = Layout(w, h)
    out_dir = OUT_ROOT / tag
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("*.png"):
        old.unlink()

    pages = paginate(L, build_units(L, SECTIONS, use_headings=True))
    shots = [("page_01", cover_html(L))]
    for i, units in enumerate(pages, start=2):
        shots.append((f"page_{i:02d}", flow_page_html(L, units)))
    # 散文模式样本（无标题）
    prose_units = paginate(L, build_units(L, [("", PROSE_PARAS[:5])], use_headings=False))[0]
    shots.append(("prose_mode", flow_page_html(L, prose_units)))

    for name, html in shots:
        html_path = out_dir / f"{name}.html"
        html_path.write_text(html, encoding="utf-8")
        png_path = out_dir / f"{name}.png"
        cmd = [
            str(CHROME), "--headless=new", "--disable-gpu", "--hide-scrollbars",
            f"--window-size={w},{h}", "--virtual-time-budget=10000",
            f"--screenshot={png_path}", html_path.as_uri(),
        ]
        subprocess.run(cmd, check=True, capture_output=True, timeout=60)
        # 内嵌 sRGB 配置：防止看图器按显示器配置渲染导致白底偏色
        from PIL import Image, ImageCms
        im = Image.open(png_path)
        im.save(png_path, icc_profile=ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes())
    print(f"[{tag}] {w}x{h}  封面 + {len(pages)} 页正文  (+ prose_mode)")


def render() -> None:
    render_version("c5_34", 1080, 1440)
    render_version("c5_35", 1080, 1800)


if __name__ == "__main__":
    render()
