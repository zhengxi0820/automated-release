"""设计预览：三版卡片模板对比。

用法：python design/render_preview.py
输出：design/preview/v{1,2,3}/card_*.html + card_*.png（1080x1440，Chrome headless 截图）
文案取自流水线真实产出（article 4，DeepSeek V4 Pro 上线硅基流动）。
"""

from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent / "preview"
CHROME = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")

BRAND = "AI 工具观察"
DATE = "08.21"
TAG = "#AI工具"
TOTAL = 4

CARDS = [
    {
        "kind": "cover",
        "seq": 1,
        "text": "DeepSeek V4 Pro<br>上线硅基流动",
        "sub": "1M 上下文，这波动作有点快",
        "body": "上下文 <b>1M 字符</b>，具体时间和价格未官宣。",
    },
    {
        "kind": "fact",
        "seq": 2,
        "label": "事实",
        "body": "硅基流动已上线 DeepSeek V4 Pro，<b>上下文 1M 字符</b>，具体时间和价格未官宣。",
    },
    {
        "kind": "opinion",
        "seq": 3,
        "label": "观点",
        "body": "1M 上下文<b>能塞进一本书</b>，长文档刚需。但新模型稳不稳、贵不贵，得实测。",
    },
    {
        "kind": "takeaway",
        "seq": 4,
        "label": "启示",
        "body": "想尝鲜可去硅基流动，但别急着迁移核心任务，<b>先小项目试水</b>。",
    },
]

FONTS = """<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@250;300;400;500;600;700;800;900&display=swap" rel="stylesheet">"""

KIND_COLOR = {  # 各卡片类型的强调色（浅底用深色、深底用亮色）
    "fact": ("#0066CC", "#2997FF"),
    "opinion": ("#C25E00", "#FF9F0A"),
    "takeaway": ("#2D8C3C", "#30D158"),
}


def _page(body: str, style: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
{FONTS}
<style>
:root {{
  --bg-elevated: #FBFBFD; --bg-gray: #F5F5F7; --bg-white: #FFFFFF; --bg-dark: #1D1D1F;
  --text-primary: #1D1D1F; --text-secondary: #6E6E73; --text-tertiary: #86868B;
  --blue: #0066CC; --blue-bright: #2997FF; --cyan: #5AC8FA; --hairline: #D2D2D7;
  --font: "PingFang SC", "Hiragino Sans GB", "Noto Sans SC", "Microsoft YaHei", sans-serif;
}}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
html, body {{ width: 1080px; height: 1440px; overflow: hidden; }}
body {{ font-family: var(--font); }}
{style}
</style>
</head>
<body>
{body}
</body>
</html>"""


# ─────────────────────────── 版本 A：纯白精装 ───────────────────────────

def v1(card: dict) -> str:
    seq, total = card["seq"], TOTAL
    accent = KIND_COLOR.get(card["kind"], ("#0066CC", "#2997FF"))[0]
    if card["kind"] == "cover":
        inner = f"""
    <div class="chip">今日热点 · {DATE}</div>
    <h1 class="title">{card['text']}</h1>
    <p class="sub">{card['sub']}</p>"""
    else:
        inner = f"""
    <div class="chip" style="color:{accent};background:{accent}14">{card['label']}</div>
    <p class="text">{card['body']}</p>"""
    dots = "".join(
        f'<span class="dot{" on" if i == seq else ""}"></span>' for i in range(1, total + 1)
    )
    body = f"""
<div class="ring r1"></div><div class="ring r2"></div>
<header><span class="brand">{BRAND}</span><span class="date">{DATE}</span></header>
<main>{inner}</main>
<footer><div class="dots">{dots}</div><span class="tag">{TAG}</span></footer>"""
    style = """
body {
  background: linear-gradient(180deg, var(--bg-elevated) 0%, var(--bg-gray) 100%);
  color: var(--text-primary);
  display: flex; flex-direction: column; justify-content: space-between;
  padding: 72px 84px 64px; position: relative;
}
.ring { position: absolute; border-radius: 50%; border: 2px solid rgba(0,102,204,.07); }
.r1 { width: 560px; height: 560px; top: -180px; right: -160px; }
.r2 { width: 340px; height: 340px; top: 90px; right: -60px; border-color: rgba(0,102,204,.05); }
header { display: flex; justify-content: space-between; align-items: center; position: relative; }
.brand { font-size: 26px; font-weight: 700; letter-spacing: .04em; }
.date { font-size: 24px; color: var(--text-tertiary); font-weight: 500; letter-spacing: .06em; }
main { flex: 1; display: flex; flex-direction: column; justify-content: center; position: relative; }
.chip {
  display: inline-flex; align-self: flex-start; padding: 12px 28px;
  border-radius: 980px; font-size: 25px; font-weight: 700; letter-spacing: .08em;
  color: var(--blue); background: rgba(0,102,204,.09);
}
.title {
  margin-top: 44px; font-size: 92px; line-height: 1.16; font-weight: 900;
  letter-spacing: .04em;
}
.sub { margin-top: 36px; font-size: 33px; color: var(--text-secondary); line-height: 1.5; }
.text { margin-top: 40px; font-size: 42px; line-height: 1.62; font-weight: 500; letter-spacing: .01em; }
.text b { font-weight: 800; color: var(--blue); }
footer { display: flex; justify-content: space-between; align-items: center; }
.dots { display: flex; gap: 14px; }
.dot { width: 14px; height: 14px; border-radius: 50%; background: rgba(0,0,0,.12); }
.dot.on { background: var(--blue); width: 34px; border-radius: 980px; }
.tag { font-size: 25px; color: var(--blue); font-weight: 600; }"""
    return _page(body, style)


# ─────────────────────────── 版本 B：深夜尊享 ───────────────────────────

def v2(card: dict) -> str:
    seq, total = card["seq"], TOTAL
    accent = KIND_COLOR.get(card["kind"], ("#0066CC", "#2997FF"))[1]
    if card["kind"] == "cover":
        inner = f"""
    <div class="chip">今日热点 · {DATE}</div>
    <h1 class="title">{card['text']}</h1>
    <p class="sub">{card['sub']}</p>"""
    else:
        inner = f"""
    <div class="chip" style="color:{accent};background:{accent}22">{card['label']}</div>
    <p class="text">{card['body']}</p>"""
    dots = "".join(
        f'<span class="dot{" on" if i == seq else ""}"></span>' for i in range(1, total + 1)
    )
    body = f"""
<div class="glow"></div>
<header><span class="brand">{BRAND}</span><span class="date">{DATE}</span></header>
<main>{inner}</main>
<footer><div class="dots">{dots}</div><span class="tag">{TAG}</span></footer>"""
    style = """
body {
  background: linear-gradient(180deg, var(--bg-dark) 0%, #000000 100%);
  color: #F5F5F7;
  display: flex; flex-direction: column; justify-content: space-between;
  padding: 72px 84px 64px; position: relative;
}
.glow {
  position: absolute; top: -220px; left: 50%; transform: translateX(-50%);
  width: 1000px; height: 700px; border-radius: 50%;
  background: radial-gradient(closest-side, rgba(41,151,255,.22), rgba(41,151,255,0));
}
header { display: flex; justify-content: space-between; align-items: center; position: relative; }
.brand { font-size: 26px; font-weight: 700; letter-spacing: .04em; }
.date { font-size: 24px; color: rgba(245,245,247,.45); font-weight: 500; letter-spacing: .06em; }
main { flex: 1; display: flex; flex-direction: column; justify-content: center; position: relative; }
.chip {
  display: inline-flex; align-self: flex-start; padding: 12px 28px;
  border-radius: 980px; font-size: 25px; font-weight: 700; letter-spacing: .08em;
  color: var(--blue-bright); background: rgba(41,151,255,.14);
}
.title {
  margin-top: 44px; font-size: 92px; line-height: 1.16; font-weight: 900;
  letter-spacing: .04em;
}
.title b {
  background: linear-gradient(90deg, var(--blue-bright), var(--cyan));
  -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent;
}
.sub { margin-top: 36px; font-size: 33px; color: rgba(245,245,247,.62); line-height: 1.5; }
.text { margin-top: 40px; font-size: 42px; line-height: 1.62; font-weight: 500; letter-spacing: .01em; color: #F5F5F7; }
.text b { font-weight: 800; color: var(--blue-bright); }
footer { display: flex; justify-content: space-between; align-items: center; }
.dots { display: flex; gap: 14px; }
.dot { width: 14px; height: 14px; border-radius: 50%; background: rgba(255,255,255,.18); }
.dot.on { background: var(--blue-bright); width: 34px; border-radius: 980px; }
.tag { font-size: 25px; color: var(--blue-bright); font-weight: 600; }"""
    return _page(body, style)


# ─────────────────────────── 版本 C：编辑部杂志 ───────────────────────────

def v3(card: dict) -> str:
    seq, total = card["seq"], TOTAL
    accent = KIND_COLOR.get(card["kind"], ("#1D1D1F", "#F5F5F7"))[0]
    if card["kind"] == "cover":
        head = f"""
    <p class="vol">VOL.{DATE} · 今日热点</p>
    <h1 class="title">{card['text']}</h1>
    <p class="sub">{card['sub']}</p>"""
    else:
        head = f"""
    <p class="vol"><b style="color:{accent}">{card['label']}</b> · {BRAND}</p>
    <p class="text">{card['body']}</p>"""
    body = f"""
<div class="index">{seq:02d}</div>
<span class="spine">{BRAND}</span>
<header><div class="rule"></div></header>
<main>{head}</main>
<footer>
  <div class="rule"></div>
  <div class="foot-row"><span class="tag">{TAG}</span><span class="page">{seq:02d} — {total:02d}</span></div>
</footer>"""
    style = """
body {
  background: var(--bg-white); color: var(--text-primary);
  display: flex; flex-direction: column; padding: 88px 96px 76px; position: relative;
}
.index {
  position: absolute; top: 60px; right: 76px; font-size: 300px; font-weight: 250;
  color: #F5F5F7; line-height: 1; letter-spacing: -.02em; user-select: none;
}
.spine {
  position: absolute; right: 40px; top: 50%; transform: translateY(-50%);
  writing-mode: vertical-rl; font-size: 25px; letter-spacing: .5em;
  color: var(--text-tertiary); font-weight: 500;
}
.rule { height: 2px; background: var(--text-primary); }
main { flex: 1; display: flex; flex-direction: column; justify-content: center; }
.vol { font-size: 27px; color: var(--text-secondary); letter-spacing: .14em; font-weight: 600; }
.vol b { font-weight: 800; }
.title { margin-top: 40px; font-size: 96px; line-height: 1.18; font-weight: 900; letter-spacing: .03em; }
.sub { margin-top: 40px; font-size: 33px; color: var(--text-secondary); line-height: 1.5; }
.text { margin-top: 36px; font-size: 42px; line-height: 1.66; font-weight: 400; color: var(--text-primary); }
.text b { font-weight: 800; background: linear-gradient(transparent 68%, rgba(0,102,204,.16) 0); }
footer { margin-top: 40px; }
.foot-row { display: flex; justify-content: space-between; align-items: baseline; margin-top: 26px; }
.tag { font-size: 26px; color: var(--blue); font-weight: 600; }
.page { font-size: 30px; color: var(--text-tertiary); font-weight: 600; letter-spacing: .08em; }"""
    return _page(body, style)


VERSIONS = {"v1": v1, "v2": v2, "v3": v3}


def render() -> None:
    for ver, fn in VERSIONS.items():
        out_dir = OUT / ver
        out_dir.mkdir(parents=True, exist_ok=True)
        for card in CARDS:
            html_path = out_dir / f"card_{card['seq']:02d}.html"
            png_path = out_dir / f"card_{card['seq']:02d}.png"
            html_path.write_text(fn(card), encoding="utf-8")
            cmd = [
                str(CHROME), "--headless=new", "--disable-gpu", "--hide-scrollbars",
                "--window-size=1080,1440", "--virtual-time-budget=10000",
                f"--screenshot={png_path}", html_path.as_uri(),
            ]
            subprocess.run(cmd, check=True, capture_output=True, timeout=60)
            print(f"[{ver}] card_{card['seq']:02d}.png")


if __name__ == "__main__":
    render()
