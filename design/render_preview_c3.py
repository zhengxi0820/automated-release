"""设计预览 v3：C3 高密度编辑部版（按用户六条意见修正 C2）。

用法：python design/render_preview_c3.py
输出：design/preview/c3/card_*.html + card_*.png（1080x1440）

排版契约（用户确认）：
- 正文 40px / 行距 62px，左右边距 130px → 每行最多 20 字，text-align: justify
- 内容页除大标题外可容 17-18 行正文，上下留白约 1.5-2 行
- 大标题 68px（正文的 1.7 倍），中文数字编号「一、二、三、」，编号与标题同字号
- 无右侧竖排刊名、无顶部规线
- 标题本身含有效信息，不用英文小标/副介绍
"""

from __future__ import annotations

import subprocess
from pathlib import Path

OUT = Path(__file__).resolve().parent / "preview" / "c3"
CHROME = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")

BRAND = "AI 工具观察"
DATE = "08.21"
TAG = "#AI工具"
TOTAL = 5

FONTS = """<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">"""

# 排版常量（正文 40 / 行距 62 / 边距 130 → 每行 20 字）
F = 40
LH = 62
PAD = 130

STYLE = f"""
:root {{
  --text-primary: #1D1D1F; --text-secondary: #6E6E73; --text-tertiary: #86868B;
  --blue: #0066CC; --hairline: #D2D2D7;
  --hl-blue: rgba(0,102,204,.16); --hl-yellow: rgba(255,204,0,.40);
  --font: "PingFang SC", "Hiragino Sans GB", "Noto Sans SC", "Microsoft YaHei", sans-serif;
}}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
html, body {{ width: 1080px; height: 1440px; overflow: hidden; }}
body {{
  font-family: var(--font); background: #FFFFFF; color: var(--text-primary);
  display: flex; flex-direction: column;
  padding: 93px {PAD}px 44px;   /* 上下留白 ≈ 1.5 行（93px），底部含页脚 */
}}
main {{ flex: 1; display: flex; flex-direction: column; }}

/* 内容页大标题：68px = 正文的 1.7 倍，编号与标题同字号 */
.sec-title {{
  font-size: 68px; line-height: 1.32; font-weight: 900; letter-spacing: .02em;
  margin-bottom: 44px;
}}
.sec-title .no {{ font-variant-numeric: tabular-nums; }}

/* 正文：40px / 62px，每行 20 字，两端对齐 */
.body {{ display: flex; flex-direction: column; gap: 30px; }}  /* 段距 ≈ 半行 */
.para {{ font-size: {F}px; line-height: {LH}px; font-weight: 400; text-align: justify; }}
.para.dim {{ color: var(--text-secondary); }}
.para b {{ font-weight: 800; background: linear-gradient(transparent 68%, var(--hl-blue) 0); }}

/* 引用块：占两行正文的高度节奏 */
.quote {{
  padding: 26px 34px; border-left: 8px solid var(--text-primary);
  background: #F5F5F7; font-size: {F}px; line-height: {LH}px; font-weight: 600;
  border-radius: 0 18px 18px 0; text-align: justify;
}}

.meta-row {{ display: flex; gap: 14px; flex-wrap: wrap; }}
.meta-pill {{
  font-size: 27px; font-weight: 600; color: var(--text-secondary);
  background: #F5F5F7; border-radius: 980px; padding: 10px 26px;
}}

/* 封面 */
.lede {{ font-size: 30px; color: var(--text-secondary); letter-spacing: .12em; font-weight: 600; margin-bottom: 34px; }}
.cover-title {{ font-size: 84px; line-height: 1.28; font-weight: 900; letter-spacing: .02em; }}
.cover-title u {{ text-decoration: none; border-bottom: 12px solid var(--hl-yellow); padding-bottom: 6px; }}
.toc {{ margin-top: 64px; }}
.toc-item {{ display: flex; align-items: baseline; gap: 26px; padding: 21px 0; border-top: 1.5px solid var(--hairline); }}
.toc-item:first-child {{ border-top: none; }}
.toc-item .no {{ font-size: 44px; font-weight: 900; color: var(--blue); }}
.toc-item .what {{ font-size: 40px; font-weight: 700; }}

/* 页脚：贴底，thin 规线 + 一行小字 */
footer {{ margin-top: auto; padding-top: 26px; }}
footer .rule {{ height: 1.5px; background: var(--hairline); }}
.foot-row {{ display: flex; justify-content: space-between; align-items: baseline; margin-top: 20px; }}
.foot-row .tag {{ font-size: 25px; color: var(--blue); font-weight: 600; }}
.foot-row .page {{ font-size: 25px; color: var(--text-tertiary); font-weight: 600; letter-spacing: .08em; }}
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
        ("一", "上线硅基流动，上下文 1M"),
        ("二", "1M 上下文是一本书的量"),
        ("三", "500 页 PDF 不用再分段"),
        ("四", "先小项目试水，别急迁移"),
    ]
    toc_html = "".join(
        f'<div class="toc-item"><span class="no">{n}、</span><span class="what">{w}</span></div>'
        for n, w in toc
    )
    return _page(f"""
<main>
  <p class="lede">AI 圈疯传的 DeepSeek 更新 · {DATE}</p>
  <h1 class="cover-title">V4 Pro <u>悄悄上线</u>，<br>普通人先别急着换</h1>
  <div class="toc">{toc_html}</div>
</main>
<footer>
  <div class="rule"></div>
  <div class="foot-row"><span class="tag">{TAG}</span><span class="page">1 / {TOTAL}</span></div>
</footer>""")


def section(no: str, title: str, inner: str, page: int) -> str:
    return _page(f"""
<main>
  <h1 class="sec-title"><span class="no">{no}、</span>{title}</h1>
  <div class="body">{inner}</div>
</main>
<footer>
  <div class="rule"></div>
  <div class="foot-row"><span class="tag">{TAG}</span><span class="page">{page} / {TOTAL}</span></div>
</footer>""")


def s1() -> str:
    return section("一", "上线硅基流动，上下文 1M", """
    <p class="para">DeepSeek V4 Pro 已经在硅基流动上线，普通注册用户就能直接调用。这次更新最值得关注的是上下文窗口：<b>一次对话能塞进 1M 字符</b>，也就是一部长篇小说的体量。</p>
    <p class="para">放在半年前，主流模型的上下文还停在 12.8 万到 20 万字符，长资料必须切块、分段、按顺序喂。1M 意味着大部分人的资料库可以<b>整包丢进去</b>，不再需要预处理。</p>
    <p class="para dim">截至发稿，官方还没有确认发布时间和定价，以上信息以硅基流动平台页面为准。第三方平台先行上线、官方后补公告，在这家公司的历史上不是第一次，急着下结论容易被打脸。</p>
    <div class="meta-row"><span class="meta-pill">上下文 1M 字符</span><span class="meta-pill">渠道 硅基流动</span><span class="meta-pill">价格未官宣</span></div>""", 2)


def s2() -> str:
    return section("二", "1M 上下文是一本书的量", """
    <p class="para">上下文决定模型一次能「记住」多少内容。1M 字符大约等于一整本书，或者 20 份左右的年度报告。对写论文、看合同、啃技术文档的人来说，这是<b>实打实的刚需</b>，不是参数内卷。</p>
    <p class="para">但也要泼一盆冷水：上下文变长，不等于长文中间的内容都能被准确利用。业内一直有「中间遗忘」的说法——开头和结尾记得牢，中段容易糊。V4 Pro 有没有这个问题、长输入的响应速度如何，都要等实测数据，参数表上看不出来。</p>
    <p class="para">另一个容易被忽略的点：上下文越长，对话里积累的偏好、术语表、示例就越不用重复贴。对做重复性工作流的人来说，这是<b>隐性的提速</b>，比跑分实在。</p>
    <p class="para">我的判断是：<b>长文档场景立刻受益</b>，其他场景先别激动，等第一批评测出来再说。</p>""", 3)


def s3() -> str:
    return section("三", "500 页 PDF 不用再分段", """
    <p class="para">说个我自己的场景：之前处理一份 500 页的行业 PDF，模型每轮只能吃几十页，我只能手动切成十几段，一段段喂，还得自己维护一份「前面说过什么」的摘要，<b>流程又慢又容易漏</b>。</p>
    <p class="para">如果 V4 Pro 的 1M 上下文真的稳定，这类活儿就是<b>整份文件直接扔进去</b>，让它自己读完整本再回答。省掉的不只是时间，还有分段导致的信息丢失——很多时候结论就藏在第 12 页和第 300 页的对照里，切块喂的时候根本对不上。</p>
    <p class="para dim">说明：我还没有对 V4 Pro 做过实测，以上是基于参数的推断，周末跑完测试会在这里更新结论。</p>""", 4)


def s4() -> str:
    return section("四", "先小项目试水，别急迁移", """
    <p class="para">给普通人的建议很简单：想尝鲜，去硅基流动把玩一下没问题；但<b>核心工作流别急着迁移</b>。新模型刚上线，稳定性、并发限制、实际价格都是未知数，把吃饭的家伙押上去，赌注太大。</p>
    <p class="para">稳妥的路径是：先拿一个<b>不重要的小项目</b>完整跑一遍，对比旧模型的输出质量和成本，跑通了、满意了，再考虑把主力任务切过来。迁移这件事，永远让证据说话。</p>
    <p class="para">另外留意成本：长上下文通常按输入量计费，1M 全喂满，<b>账单可能比想象中好看不了多少</b>，尝鲜的时候记得先看一眼定价再放量跑。</p>
    <div class="quote">你会为了 1M 上下文换模型吗？评论区聊聊你的用法。</div>""", 5)


CARDS = [cover, s1, s2, s3, s4]


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
        print(f"[c3] card_{i:02d}.png")


if __name__ == "__main__":
    render()
