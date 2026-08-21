"""设计预览 v2：C2 高密度编辑部版（参考 Seedance 2.5 笔记的信息密度）。

用法：python design/render_preview_c2.py
输出：design/preview/c2/card_*.html + card_*.png（1080x1440）

密度契约（相对单句卡片的信息量提升约 4 倍）：
- 封面：引导语 + 两行大标题 + 三个看点目录 + 品牌页脚
- 内容页：小节序号 + 小节标题 + 2-3 段正文（每行约 24 字，单卡 120-180 字）
- 强调：加粗 + 荧光笔高亮，标题手工感下划线
"""

from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent / "preview" / "c2"
CHROME = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")

BRAND = "AI 工具观察"
DATE = "08.21"
TAG = "#AI工具"
TOTAL = 5

FONTS = """<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@250;300;400;500;600;700;800;900&display=swap" rel="stylesheet">"""

STYLE = """
:root {
  --bg-white: #FFFFFF; --text-primary: #1D1D1F; --text-secondary: #6E6E73;
  --text-tertiary: #86868B; --blue: #0066CC; --hairline: #D2D2D7;
  --hl-blue: rgba(0,102,204,.16); --hl-yellow: rgba(255,204,0,.38);
  --font: "PingFang SC", "Hiragino Sans GB", "Noto Sans SC", "Microsoft YaHei", sans-serif;
}
* { margin: 0; padding: 0; box-sizing: border-box; }
html, body { width: 1080px; height: 1440px; overflow: hidden; }
body {
  font-family: var(--font); background: var(--bg-white); color: var(--text-primary);
  display: flex; flex-direction: column; padding: 84px 96px 72px; position: relative;
}
.spine {
  position: absolute; right: 38px; top: 50%; transform: translateY(-50%);
  writing-mode: vertical-rl; font-size: 24px; letter-spacing: .5em;
  color: var(--text-tertiary); font-weight: 500;
}
header .rule { height: 2px; background: var(--text-primary); }
main { flex: 1; display: flex; flex-direction: column; justify-content: center; }
footer { margin-top: auto; }
footer .rule { height: 1.5px; background: var(--hairline); }
.foot-row { display: flex; justify-content: space-between; align-items: baseline; margin-top: 24px; }
.foot-row .tag { font-size: 25px; color: var(--blue); font-weight: 600; }
.foot-row .page { font-size: 28px; color: var(--text-tertiary); font-weight: 600; letter-spacing: .08em; }

/* 封面 */
.lede { font-size: 30px; color: var(--text-secondary); letter-spacing: .1em; font-weight: 600; margin-bottom: 36px; }
.cover-title { font-size: 96px; line-height: 1.22; font-weight: 900; letter-spacing: .03em; }
.cover-title u {
  text-decoration: none; border-bottom: 10px solid var(--hl-yellow); padding-bottom: 4px;
}
.toc { margin-top: 56px; padding-top: 40px; border-top: 1.5px solid var(--hairline); }
.toc .toc-title { font-size: 26px; color: var(--text-tertiary); letter-spacing: .16em; font-weight: 600; margin-bottom: 26px; }
.toc-item { display: flex; align-items: baseline; gap: 24px; padding: 14px 0; }
.toc-item .no { font-size: 30px; font-weight: 800; color: var(--blue); font-variant-numeric: tabular-nums; }
.toc-item .what { font-size: 32px; font-weight: 500; color: var(--text-primary); }
.toc-item .why { font-size: 26px; color: var(--text-tertiary); margin-left: auto; text-align: right; }

/* 内容页 */
.sec-head { display: flex; align-items: baseline; gap: 28px; margin-bottom: 12px; }
.sec-no { font-size: 88px; font-weight: 250; color: var(--text-primary); letter-spacing: -.02em; line-height: 1; font-variant-numeric: tabular-nums; }
.sec-title { font-size: 46px; font-weight: 800; letter-spacing: .04em; }
.sec-sub { font-size: 26px; color: var(--text-tertiary); font-weight: 500; margin-bottom: 44px; letter-spacing: .06em; }
.para { font-size: 36px; line-height: 1.72; font-weight: 400; color: var(--text-primary); }
.para + .para { margin-top: 34px; }
.para.dim { color: var(--text-secondary); }
.para b { font-weight: 800; background: linear-gradient(transparent 66%, var(--hl-blue) 0); }
.quote {
  margin-top: 40px; padding: 30px 36px; border-left: 8px solid var(--text-primary);
  background: #F5F5F7; font-size: 34px; line-height: 1.65; font-weight: 500; border-radius: 0 18px 18px 0;
}
.quote b { font-weight: 800; }
.meta-row { display: flex; gap: 16px; margin-top: 40px; flex-wrap: wrap; }
.meta-pill {
  font-size: 25px; font-weight: 600; color: var(--text-secondary);
  background: #F5F5F7; border-radius: 980px; padding: 12px 26px;
}
"""


def _page(body: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
{FONTS}
<style>{STYLE}</style>
</head>
<body>
{body}
</body>
</html>"""


def cover() -> str:
    toc = [
        ("01", "已经上线了什么", "1M 上下文"),
        ("02", "为什么值得看", "一本书的量"),
        ("03", "普通人怎么用", "先小项目试水"),
    ]
    toc_html = "".join(
        f'<div class="toc-item"><span class="no">{n}</span><span class="what">{w}</span><span class="why">{y}</span></div>'
        for n, w, y in toc
    )
    return _page(f"""
<span class="spine">{BRAND}</span>
<header><div class="rule"></div></header>
<main>
  <p class="lede">AI 圈疯传的 DeepSeek 更新</p>
  <h1 class="cover-title">V4 Pro <u>悄悄上线</u>，<br>先别急着换</h1>
  <div class="toc">
    <p class="toc-title">本 期 看 点</p>
    {toc_html}
  </div>
</main>
<footer>
  <div class="rule"></div>
  <div class="foot-row"><span class="tag">{TAG} · {DATE}</span><span class="page">01 — 05</span></div>
</footer>""")


def section(no: str, title: str, sub: str, inner: str) -> str:
    return _page(f"""
<span class="spine">{BRAND}</span>
<header><div class="rule"></div></header>
<main>
  <div class="sec-head"><span class="sec-no">{no}</span><span class="sec-title">{title}</span></div>
  <p class="sec-sub">{sub}</p>
  {inner}
</main>
<footer>
  <div class="rule"></div>
  <div class="foot-row"><span class="tag">{TAG}</span><span class="page">{no} — 05</span></div>
</footer>""")


def fact() -> str:
    return section(
        "02", "发生了什么", "WHAT HAPPENED · 事实核查",
        """
  <p class="para">根据硅基流动平台的信息，DeepSeek V4 Pro <b>已经可以访问</b>，上下文长度达到 <b>1M 字符</b>，大约能一次塞下一本书。</p>
  <p class="para dim">截至发稿，官方还没有确认具体的发布时间和价格，以下判断都基于平台现有信息。</p>
  <div class="meta-row"><span class="meta-pill">上下文 1M 字符</span><span class="meta-pill">渠道：硅基流动</span><span class="meta-pill">价格未官宣</span></div>""",
    )


def opinion() -> str:
    return section(
        "03", "怎么理解", "MY TAKE · 观点",
        """
  <p class="para">1M 上下文对长文档处理是<b>实打实的刚需</b>：一次性塞进一本书的量，不用再手动切分。但新模型刚上，性能稳不稳、收费贵不贵，都得实测才知道。</p>
  <div class="quote">当上下文不再是瓶颈，<b>你怎么提问</b>反而成了新的瓶颈。</div>""",
    )


def case() -> str:
    return section(
        "04", "一个真实场景", "USE CASE · 亲历",
        """
  <p class="para">之前用其他模型处理 500 页 PDF，经常截断，得手动分段，一段段喂。如果 V4 Pro 真能扛住 1M，<b>整个工作流能省掉一大步</b>。</p>
  <p class="para dim">说明：我没有实测过 V4 Pro，以上是基于参数的推断，等周末跑完测试再来更新。</p>""",
    )


def takeaway() -> str:
    return section(
        "05", "现在要做什么", "TAKEAWAY · 行动建议",
        """
  <p class="para">想尝鲜的可以去硅基流动看看，但<b>别急着迁移核心任务</b>，先拿小项目试水，跑通再说。</p>
  <div class="quote">你会为了 1M 上下文换模型吗？评论区聊聊。</div>""",
    )


CARDS = [cover, fact, opinion, case, takeaway]


def render() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for i, fn in enumerate(CARDS, start=1):
        html_path = OUT / f"card_{i:02d}.html"
        png_path = OUT / f"card_{i:02d}.png"
        html_path.write_text(fn(), encoding="utf-8")
        cmd = [
            str(CHROME), "--headless=new", "--disable-gpu", "--hide-scrollbars",
            "--window-size=1080,1440", "--virtual-time-budget=10000",
            f"--screenshot={png_path}", html_path.as_uri(),
        ]
        subprocess.run(cmd, check=True, capture_output=True, timeout=60)
        print(f"[c2] card_{i:02d}.png")


if __name__ == "__main__":
    render()
