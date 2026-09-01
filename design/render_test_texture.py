"""字体质感对照实验：找出与参考图观感一致的字重/墨色/字距组合。

输出：design/preview/texture_test/ 4 张单页 + texture_4up.png 对照图
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from render_preview_c4 import SECTIONS  # noqa: E402
from render_preview_c5 import Layout, em_len, wrap, flow_page_html  # noqa: E402
from render_preview_c5 import build_units, paginate  # noqa: E402

OUT = Path(__file__).resolve().parent / "preview" / "texture_test"
CHROME = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")

CONFIGS = {
    #           weight  ink        tracking
    "A_600_gray": (600, "#1D1D1F", 0.0),
    "B_500_black": (500, "#000000", 0.0),
    "C_500_black_tr": (500, "#000000", 0.04),
    "D_600_black_tr": (600, "#000000", 0.04),
}


def render_one(tag: str, weight: int, ink: str, tracking: float) -> Path:
    L = Layout(1080, 1800)
    # 覆盖墨色与字重
    css = L.CSS.format(w=L.w, h=L.h, px=L.pad_x, pt=L.pad_top, pb=L.pad_bottom,
                       fb=L.f_body, fh=L.f_head, lhb=L.lh_body, lhh=L.lh_head)
    css = css.replace("color: var(--ink)", f"color: {ink}")
    css = css.replace("font-weight: 600", f"font-weight: {weight}")
    if tracking:
        css = css.replace(".pln {", f".pln {{ letter-spacing: {tracking}em;")
        css = css.replace(".pln.last {", f".pln.last {{ letter-spacing: {tracking}em;")

    # 有字距时行容量要收紧，防止浏览器二次折行
    cap = L.line_cap - (tracking * L.line_cap + 0.5 if tracking else 0)
    units = build_units(L, [("", SECTIONS[0][1] + SECTIONS[1][1][:2])], use_headings=False)
    # 手动重建（用调整后的 cap）
    units = []
    for j, p in enumerate(SECTIONS[0][1] + SECTIONS[1][1][:2]):
        if j > 0:
            units.append({"kind": "gap", "h": L.para_gap})
        units.append({"kind": "p", "lines": wrap(p, cap)})

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
<style>{css}</style>
</head>
<body>
{flow_page_html.__doc__ or ""}
<main>"""
    # 直接复用 flow_page_html 的行渲染逻辑
    from render_preview_c5 import page_html
    lines = ["<main>"]
    for u in units:
        if u["kind"] == "gap":
            lines.append(f'<div style="height:{u["h"]}px"></div>')
        else:
            n = len(u["lines"])
            for k, ln in enumerate(u["lines"]):
                lines.append(f'<div class="{"pln last" if k == n - 1 else "pln"}">{ln}</div>')
    lines.append("</main>")
    html = page_html(L, "\n".join(lines)).replace("color: var(--ink)", f"color: {ink}")
    # 字重与字距再注入一次（page_html 用的是未改 CSS）
    html = html.replace("font-weight: 600;", f"font-weight: {weight};")
    if tracking:
        html = html.replace(".pln {", f".pln {{ letter-spacing: {tracking}em;")
        html = html.replace(".pln.last {", f".pln.last {{ letter-spacing: {tracking}em;")

    OUT.mkdir(parents=True, exist_ok=True)
    html_path = OUT / f"{tag}.html"
    html_path.write_text(html, encoding="utf-8")
    png_path = OUT / f"{tag}.png"
    cmd = [str(CHROME), "--headless=new", "--disable-gpu", "--hide-scrollbars",
           "--window-size=1080,1800", "--virtual-time-budget=10000",
           f"--screenshot={png_path}", html_path.as_uri()]
    subprocess.run(cmd, check=True, capture_output=True, timeout=60)
    return png_path


def main() -> None:
    pngs = {tag: render_one(tag, *cfg) for tag, cfg in CONFIGS.items()}
    from PIL import Image, ImageDraw
    cw, ch = 900, 1000
    sheet = Image.new("RGB", (cw * 2 + 60, ch * 2 + 120), "#CCCCCC")
    dr = ImageDraw.Draw(sheet)
    for i, (tag, p) in enumerate(pngs.items()):
        r, c = divmod(i, 2)
        im = Image.open(p).crop((78, 180, 78 + cw, 180 + ch))
        sheet.paste(im, (20 + c * (cw + 20), 70 + r * (ch + 40)))
        dr.text((20 + c * (cw + 20), 40 + r * (ch + 40)), tag, fill="#900")
    sheet.save(OUT.parent / "texture_4up.png")
    print("done:", list(pngs))


if __name__ == "__main__":
    main()
