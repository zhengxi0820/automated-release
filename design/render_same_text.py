"""同文对照页：用参考笔记（strawman/steelman）的原文，按当前排版参数渲染一页。

用法：python design/render_same_text.py
输出：design/preview/对照_同文.png（1080x1800）

文字与参考图逐字一致（含原文的"遇到到"；原文末句被截图截断，此处补全为"判断"）。
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import render_preview_c5 as m  # noqa: E402

OUT = Path(__file__).resolve().parent / "preview" / "对照_同文.png"
CHROME = m.CHROME

PARAGRAPHS = [
    "straw man是一个逻辑学里非常经典的观点，也是一个很有意思的辩论技巧，叫稻草人谬误。",
    "大概意思就是，两个人争论时，其中一个人故意把对方的观点说得特别蠢、特别极端、特别容易攻击，然后对着这个被篡改过的弱版本一顿输出。",
    "比如你说：“我觉得这台XX手机有点贵。”",
    "对方说：“哦，懂了，你看不起国产手机。”",
    "我相信大家日常生活里经常遇到到这样的人，这就是strawman，稻草人谬误，你真正的观点被削弱、扭曲了。",
    "后来英语里就出现了一个特别形象的反向说法：",
    "steelman。",
    "straw是稻草，软弱、一碰就倒。",
    "steel是钢铁，坚固、强壮、难以击败。",
    "于是，钢人论证法出现了，也就是steelman，它完全是稻草人谬误的反面，它要求你先替对方把论点补完整，把其中最合理、最难反驳的部分全部找出来，甚至说得比对方本人还好，然后再开始判断。",
]


def main() -> None:
    L = m.Layout(1080, 1800)  # 行距/段距/留白/字重走 Layout 定稿值
    L.track = 0.0         # 参考图实测字距为 0（其空气感来自字形本身）
    L.f_body = 40         # 参考图实测字号 ≈ 41.5，40px 每行可容 23 字
    L.line_cap = 23.0
    L.pad_top, L.pad_bottom = 78, 82  # 对照页微调 2-3px 使单页恰好容纳（生产用 80/85）

    units = []
    for j, p in enumerate(PARAGRAPHS):
        if j > 0:
            units.append({"kind": "gap", "h": L.para_gap})
        units.append({"kind": "p", "lines": m.wrap(p, L.line_cap)})

    total_h = sum(
        len(u["lines"]) * L.lh_body if u["kind"] == "p" else u["h"] for u in units
    )
    print(f"排版高度 {total_h}px / 版心 {L.content_h}px（{'单页可容' if total_h <= L.content_h else '超出一页'}），"
          f"共 {sum(len(u['lines']) for u in units if u['kind'] == 'p')} 行")

    html = m.page_html(L, m.flow_page_html(L, units).split("<body>")[1].split("</body>")[0])
    html_path = OUT.with_suffix(".html")
    html_path.write_text(html, encoding="utf-8")
    cmd = [
        str(CHROME), "--headless=new", "--disable-gpu", "--hide-scrollbars",
        f"--window-size={L.w},{L.h}", "--virtual-time-budget=10000",
        f"--screenshot={OUT}", html_path.as_uri(),
    ]
    subprocess.run(cmd, check=True, capture_output=True, timeout=60)
    from PIL import Image, ImageCms
    im = Image.open(OUT)
    im.save(OUT, icc_profile=ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes())
    print(f"输出：{OUT}")


if __name__ == "__main__":
    main()
