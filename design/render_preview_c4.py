"""设计预览 v4：C4 书页连续排版（思源宋体、跨卡接力、可选标题模式）。

用法：python design/render_preview_c4.py
输出：design/preview/c4/page_*.png（1080x1440）

排版契约（用户确认）：
- 思源宋体（Noto Serif SC），正文 400 / 标题 500
- 正文 30px（参考图 15px × 2 逻辑缩放），标题 40px（4/3 倍）
- 行距 1.5 倍，段间额外空一行；两端对齐
- 连续流排版：标题内联，卡片排满即接力到下一张，仅做孤行保护
- 无页脚标签，仅右下角小页码；文章体量 3000+ 字
- 支持无标题散文模式（use_headings=False）
"""

from __future__ import annotations

import subprocess
from pathlib import Path

OUT = Path(__file__).resolve().parent / "preview" / "c4"
CHROME = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")

# ── 排版常量（1080x1440 画布）──
F_BODY = 37          # 正文
F_HEAD = 45          # 标题
LH_BODY = F_BODY * 2          # 行距 2 倍字体高度 = 74
LH_HEAD = F_HEAD * 2          # 标题行距 = 90
PARA_GAP = LH_BODY           # 段间空一行 = 74
PAD_X = 130
PAD_TOP = 90
PAD_BOTTOM = 50
LINE_CAP = float(int((1080 - PAD_X * 2) / F_BODY))   # 22 字/行
HEAD_CAP = float(int((1080 - PAD_X * 2) / F_HEAD))   # 18 字/行
CONTENT_H = 1440 - PAD_TOP - PAD_BOTTOM   # 1300

BRAND = "AI 工具观察"
DATE = "08.21"

FONTS = """<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;500;600;700;900&display=swap" rel="stylesheet">"""

# ── 文章（约 3200 字，事实纪律：仅使用流水线已有事实 + 观点推演）──
SECTIONS = [
    ("一、上线硅基流动，上下文 1M", [
        "DeepSeek V4 Pro 已经悄悄出现在硅基流动的模型列表里，普通注册用户就能直接调用，不需要申请，也不需要排队。这次更新最扎眼的参数只有一个：上下文窗口 1M 字符。没有发布会，没有倒计时，就这么静悄悄地上线了。",
        "先说人话。上下文窗口，决定的是模型一次对话里能「捧着读」的内容总量。之前的公开主流水平，大致在十几万到二十几万字符这个档位。资料超过这个量，要么截断扔掉一部分，要么让模型先做一次有损压缩，细节就在这一步悄悄丢掉了。",
        "1M 字符是什么概念？一部长篇小说的体量，或者二十份上下的年度报告。换句话说，多数人电脑里那个「资料文件夹」，从此有机会一次性装进同一场对话。",
        "顺带交代背景：硅基流动是第三方推理平台，聚合托管了多家的开源模型，新模型先在这类平台出现、官方渠道后发，在开源圈是常见路径。看到「已上线」三个字，先别急着当成官宣，这是这两年用真金白银换来的经验。",
        "还有个小细节值得玩味：这次上架没配任何宣传物料，模型介绍页都还很简陋。要么是准备不足，要么是故意低调让社区自己发酵。无论哪种，都说明现在下任何结论都太早。",
        "要说明的是：截至发稿，官方还没有确认发布时间和定价，以上信息以硅基流动平台页面为准。最后交代本文的信息源：平台页面、社区讨论，加上我自己的使用经验。凡是没核实的地方，文中都标了「未官宣」「待实测」。这不是免责声明，是阅读习惯——看 AI 资讯，先看信源，再看结论。",
    ]),
    ("二、1M 上下文是一本书的量", [
        "把 1M 拆到具体场景里看。写论文的同学，参考文献加正文加笔记，往往几十万字起步；看合同的人，一个项目的合同组加上补充协议，轻松过百页；写代码的人，一个中型仓库的源码加文档，也是几十万字符的量级。这些活儿，以前都得先切块。",
        "还有一个容易被忽略的隐性收益：上下文越长，对话里沉淀下来的偏好、术语表、风格示例，就越不用每次重复贴。对每天做重复性工作的人来说，这是实打实的提速，比跑分好看多了。",
        "顺带澄清一个常见误解：上下文窗口是「单场对话」的记忆，不是永久记忆。对话一关，这些内容不会自动变成模型的常识。想让模型长期记住你的偏好，得靠外部笔记，或者每次重新喂。搞清楚这一点，能省掉很多不切实际的期待。",
        "再往深处想一层：上下文变长，改变的不只是「能读多少」，还有提问的方式。以前提问，要先把问题拆碎，迁就窗口的大小；现在提问，可以把整份材料当背景，直接问结论。工具的边界往后退，人的思考就可以往前站。这才是这类参数升级里，对普通人最有价值的部分。",
        "多说一句「一本书」的直觉：人读一本书是线性地读，读完形成整体理解；模型读一本书，更像是把整本书摊开在桌面上，随时抽查任何一页。这两种「读过」不一样——模型的优势是随机访问，劣势是未必有整体感。所以长上下文要配好问题，你得知道自己要抽哪一页。",
        "当然，也别把「塞得进」当成「读得懂」。文本进窗口只是第一步，理解、关联、推理是另一回事。就像图书馆进了新书，书架够大是好事，但能不能找到、能不能读懂，还得看检索的人。这个比喻糙了点，方向没错。",
        "但这里要泼一盆冷水。上下文长，不等于长文中间的内容都能被准确利用。业内一直有「中间遗忘」的说法：模型对开头和结尾记得牢，中段容易糊。V4 Pro 有没有这个问题，长输入的响应速度怎么样，参数表上看不出来，只能等实测。",
        "所以我的判断是：长文档场景可以立刻受益，值得马上试；其他场景先别激动，等第一批深度评测出来再说。工具是用来解决问题的，不是用来追新的。",
    ]),
    ("三、500 页 PDF 的真实痛感", [
        "说个我自己的场景。之前处理一份五百页的行业 PDF，模型每轮只能吃进去几十页，我只好手动切成十几段，一段一段喂。更麻烦的是，还得自己维护一份「前面聊过什么」的摘要，每次都附在提问后面，流程又慢又容易出错。",
        "当时的流程大致是这样：先把 PDF 按章节切块、编号；每次提问，附上问题相关的两三块，再贴一段滚动摘要；模型答完，手动把新结论补回摘要。一次完整的追问，来回要折腾半小时，精力全花在「喂」上，而不是「想」上。",
        "最气人的是，很多结论偏偏藏在对照里。第 12 页的一个数字，要对上第 300 页的一句表述，切块喂的时候，这两段根本不在同一个对话里，模型想帮也对不上。",
        "有人会说，用检索也能解决长文档问题，何必非要长上下文。我的体感是：检索适合「答案就在某几段」的点到点问题；长上下文适合「答案散落全文」的汇总型问题。两个能力是互补的，不是替代关系。这次更新，补的是后一块的短板。",
        "如果 V4 Pro 的 1M 上下文真的稳定，这类活儿的做法就变成了：整份文件直接扔进去，让它自己从头读到尾，再回答问题。省掉的不只是切割的时间，还有分段导致的信息丢失——这部分损失平时看不见，出错的时候才知道疼。",
        "照例说明：我还没有对 V4 Pro 做过实测，以上是基于参数的推断。周末跑完测试，我会回来更新结论，错了认错。也给自己留个后手：任何模型处理长文档，都建议先做一次「复读机测试」——挑材料中间的一段细节直接问它，看答不答得上来。十秒钟的测试，能拦住大部分「看起来读了其实没读」的坑。",
    ]),
    ("四、三个要冷静看待的问题", [
        "第一是稳定性。新模型刚上线，并发能力、限流策略、服务优先级都是未知数。把核心工作流押上去，一旦平台侧抖动，耽误的是自己的事。灰度期观望，不是胆小，是纪律。",
        "第二是成本。长上下文按输入量计费是行业常态，1M 全喂满，账单未必比想象中友好。尝鲜的时候，建议先看一眼定价页，再用小文件试水，别一上来就整本教材往里灌。",
        "第三是生态。围绕旧模型的客户端、工作流、提示词库，要不要跟进适配，迁移的隐性成本要算总账。参数翻十倍，不等于你的整套流程收益翻十倍，中间隔着工具链的磨合。",
        "另外给重度用户提个醒：如果你的工具链里已经有围绕旧模型调好的提示词和参数，别急着全套照搬。长上下文下，提示词的位置、示例的排布，都可能影响效果，值得重新做一轮小规模对比。",
        "还有一个信号可以参考：第三方平台给的限流参数。如果平台对长上下文请求给出很低的并发额度，说明服务方自己也清楚算力吃紧；反之则说明准备充分。这个细节，比宣传稿诚实得多。",
        "如果一定要排个优先级：个人尝鲜，随时可以；辅助性场景，等第一批评测；核心生产流程，等官方公告加价格齐了再说。越靠近饭碗，越要慢半拍。",
    ]),
    ("五、普通人的行动清单", [
        "想尝鲜的，去硅基流动把玩一下，完全没问题，这是了解新模型最便宜的方式。但核心工作流别急着迁移。新模型上线初期，稳定性、并发、价格都在变，把吃饭的家伙押上去，赌注太大。",
        "稳妥的路径是：挑一个不重要的小项目，用新模型完整跑一遍，和旧模型的输出质量、花费、耗时放在一张表里对比。跑通了，满意了，再谈迁移。这件事，永远让证据说话。",
        "接下来盯三个信号就够了：官方正式公告、第一批深度评测、定价页的最终数字。三个都落地之前，一切激动都打折。这几年的规律大同小异：平台先出实例，社区先狂欢，实测来修正，最后价格落地、归于平静。与其第一天抢热搜，不如第一周看评测。",
        "再啰嗦一句心态：模型圈这两年最不缺的是「史上最强」，最缺的是「稳定可用」。参数上的十倍，落到具体工作流里常常只有一倍半；反过来，一次平台抖动，就可能让你的一天白干。慢慢来，比较快。",
        "如果你只有两分钟，就记三句话：第一，V4 Pro 在硅基流动，可以直接试；第二，1M 上下文对长文档是真需求，值得亲自验证；第三，价格和稳定性没落地之前，核心任务别动。其余的，交给时间。",
        "最后留个问题：你会为了 1M 上下文换模型吗？你手头最想整包塞进去的，又是哪份资料？评论区聊聊，攒够了我就整理一篇「评论区实测合集」，让后来的人少踩坑。",
    ]),
]

# 无标题散文模式：同内容去掉标题，段落靠空行分节奏（演示用前两节合并）
PROSE_PARAS = [p for _, paras in SECTIONS[:2] for p in paras]


# ── em 宽度估算（保守，防溢出）──
def em_len(ch: str) -> float:
    o = ord(ch)
    if o < 128:
        if ch == " ":
            return 0.32
        if ch in ".,:;!?'\"()":
            return 0.36
        return 0.56
    return 1.0


def wrap(text: str, cap: float) -> list[str]:
    lines, cur, curw = [], "", 0.0
    for ch in text:
        w = em_len(ch)
        if cur and curw + w > cap:
            lines.append(cur)
            cur, curw = ch, w
        else:
            cur += ch
            curw += w
    if cur:
        lines.append(cur)
    return lines


# ── 排版单元 ──
def build_units(sections, use_headings=True) -> list[dict]:
    units: list[dict] = []
    for i, (head, paras) in enumerate(sections):
        if use_headings and i > 0:
            units.append({"kind": "gap", "h": PARA_GAP})
        if use_headings:
            units.append({"kind": "h", "lines": wrap(head, HEAD_CAP - 0.3)})
            units.append({"kind": "gap", "h": PARA_GAP})
        for j, p in enumerate(paras):
            if j > 0:
                units.append({"kind": "gap", "h": PARA_GAP})
            units.append({"kind": "p", "lines": wrap(p, LINE_CAP)})
    return units


def unit_height(u: dict) -> int:
    if u["kind"] == "h":
        return len(u["lines"]) * LH_HEAD
    if u["kind"] == "p":
        return len(u["lines"]) * LH_BODY
    return u["h"]


# ── 分页（孤行保护：标题后至少跟 2 行正文）──
def paginate(units: list[dict]) -> list[list[dict]]:
    pages, cur, used = [], [], 0

    def flush():
        nonlocal cur, used
        if cur:
            pages.append(cur)
        cur, used = [], 0

    i = 0
    while i < len(units):
        u = units[i]
        h = unit_height(u)
        if u["kind"] == "h":
            lookahead = h + LH_BODY + 2 * LH_BODY  # 标题 + 空行 + 两行正文
            if cur and used + lookahead > CONTENT_H:
                flush()
                continue
        if not cur:
            cur, used = [u], h
        elif used + h <= CONTENT_H:
            cur.append(u)
            used += h
        else:
            flush()
            continue  # 当前单元放不下，翻页后重试，不能丢弃
        i += 1
    flush()
    return pages


# ── HTML 渲染 ──
BASE_CSS = f"""
:root {{
  --ink: #1D1D1F; --ink-2: #6E6E73; --ink-3: #86868B; --blue: #0066CC;
  --hairline: #D2D2D7; --hl-yellow: rgba(255,204,0,.40);
  --serif: "Noto Serif SC", "Source Han Serif SC", "SimSun", serif;
}}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
html, body {{ width: 1080px; height: 1440px; overflow: hidden; }}
body {{
  font-family: var(--serif); background: #FFFFFF; color: var(--ink);
  display: flex; flex-direction: column;
  padding: {PAD_TOP}px {PAD_X}px {PAD_BOTTOM}px;
}}
main {{ flex: 1; }}
.hln {{ font-size: {F_HEAD}px; line-height: {LH_HEAD}px; font-weight: 700; }}
.pln {{ font-size: {F_BODY}px; line-height: {LH_BODY}px; font-weight: 500; text-align: justify; text-align-last: justify; }}
.pln.last {{ text-align-last: auto; }}
"""


def _page(body: str, extra_css: str = "") -> str:
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
{FONTS}
<style>{BASE_CSS}{extra_css}</style>
</head>
<body>
{body}
</body>
</html>"""


def render_flow_page(units: list[dict]) -> str:
    html_lines: list[str] = ["<main>"]
    for u in units:
        if u["kind"] == "gap":
            html_lines.append(f'<div style="height:{PARA_GAP}px"></div>')
        elif u["kind"] == "h":
            for ln in u["lines"]:
                html_lines.append(f'<div class="hln">{ln}</div>')
        else:
            n = len(u["lines"])
            for k, ln in enumerate(u["lines"]):
                cls = "pln last" if k == n - 1 else "pln"
                html_lines.append(f'<div class="{cls}">{ln}</div>')
    html_lines.append("</main>")
    return _page("\n".join(html_lines))


def cover() -> str:
    items = "".join(
        f'<div class="toc-item"><span class="no">{h.split("、")[0]}、</span><span class="what">{h.split("、", 1)[1]}</span></div>'
        for h, _ in SECTIONS
    )
    css = """
.lede { font-size: 30px; color: #6E6E73; letter-spacing: .12em; font-weight: 400; margin-bottom: 40px; }
.cover-title { font-size: 82px; line-height: 1.34; font-weight: 900; letter-spacing: .02em; }
.cover-title u { text-decoration: none; border-bottom: 14px solid var(--hl-yellow); padding-bottom: 8px; }
.toc { margin-top: 70px; }
.toc-item { display: flex; align-items: baseline; gap: 26px; padding: 24px 0; border-top: 1.5px solid var(--hairline); }
.toc-item:first-child { border-top: none; }
.toc-item .no { font-size: 40px; font-weight: 700; color: var(--ink); }
.toc-item .what { font-size: 38px; font-weight: 600; }
main { flex: 1; display: flex; flex-direction: column; justify-content: center; }
"""
    body = f"""
<main>
  <p class="lede">AI 圈疯传的 DeepSeek 更新 · {DATE}</p>
  <h1 class="cover-title">V4 Pro <u>悄悄上线</u>，<br>普通人先别急着换</h1>
  <div class="toc">{items}</div>
</main>"""
    return _page(body, css)


def render() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    pages = paginate(build_units(SECTIONS, use_headings=True))
    print(f"分页：封面 + {len(pages)} 页正文")
    shots = [("page_01", cover())]
    for i, units in enumerate(pages, start=2):
        shots.append((f"page_{i:02d}", render_flow_page(units)))
    # 无标题散文模式样本（第 1 页）
    prose_units = paginate(build_units([("", PROSE_PARAS[:4])], use_headings=False))[0]
    shots.append(("prose_mode", render_flow_page(prose_units)))

    for name, html in shots:
        html_path = OUT / f"{name}.html"
        png_path = OUT / f"{name}.png"
        html_path.write_text(html, encoding="utf-8")
        cmd = [
            str(CHROME), "--headless=new", "--disable-gpu", "--hide-scrollbars",
            "--window-size=1080,1440", "--virtual-time-budget=10000",
            f"--screenshot={png_path}", html_path.as_uri(),
        ]
        subprocess.run(cmd, check=True, capture_output=True, timeout=60)
        print(f"[c4] {name}.png  ({len(html)} bytes html)")


if __name__ == "__main__":
    body_chars = sum(len(p) for _, ps in SECTIONS for p in ps)
    print(f"正文字数：{body_chars}")
    render()
