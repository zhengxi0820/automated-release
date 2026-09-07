"""Render cover.html -> cover.png (1080x1800) + thumb.png for feed-visibility check.

Usage: python _render.py [v1 v2 v3 v4 ...]   (default: all four)
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CHROME = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")


def render(tag: str) -> None:
    d = ROOT / tag
    html = d / "cover.html"
    png = d / "cover.png"
    if png.exists():
        png.unlink()
    cmd = [
        str(CHROME), "--headless=new", "--disable-gpu", "--hide-scrollbars",
        "--window-size=1080,1800", "--virtual-time-budget=10000",
        f"--screenshot={png}", html.as_uri(),
    ]
    subprocess.run(cmd, check=True, capture_output=True, timeout=90)
    if not png.exists():
        raise RuntimeError(f"no screenshot produced: {png}")

    from PIL import Image, ImageCms
    im = Image.open(png)
    # embed sRGB profile so viewers don't shift the white/dark backgrounds
    im.save(png, icc_profile=ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes())
    # feed-thumbnail check: xiaohongshu feed shows covers around ~300px wide
    im.resize((300, 500), Image.LANCZOS).save(d / "thumb.png")
    print(f"[{tag}] {png}  {png.stat().st_size // 1024} KB")


if __name__ == "__main__":
    tags = sys.argv[1:] or ["v1", "v2", "v3", "v4"]
    for t in tags:
        render(t)
