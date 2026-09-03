"""成品发布包：图片 + 标题 + 正文 + 标签 + 发布检查。"""

from __future__ import annotations

import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "data" / "output"


def build_package(domain_id: str, article_id: int, title: str, body_text: str, tags: list[str],
                  todo_verify: list[str], image_paths: list[Path]) -> Path:
    """打包为 zip，返回路径。body_text 为全文纯文本（含节标题）。"""
    article_dir = OUTPUT_DIR / domain_id / str(article_id)
    package_dir = article_dir / "package"
    package_dir.mkdir(parents=True, exist_ok=True)

    images_dir = package_dir / "images"
    images_dir.mkdir(exist_ok=True)
    for p in image_paths:
        (images_dir / p.name).write_bytes(p.read_bytes())

    (package_dir / "publish.txt").write_text(f"{title}\n\n{body_text}", encoding="utf-8")
    (package_dir / "tags.txt").write_text(" ".join(tags), encoding="utf-8")

    check_lines = ["# 发布检查", "", "- [ ] 发布时勾选「AI 参与创作/辅助生成」",
                   "", "## 待查证清单", ""]
    check_lines += [f"- [ ] {v}" for v in todo_verify] if todo_verify else ["（无）"]
    (package_dir / "发布检查.md").write_text("\n".join(check_lines), encoding="utf-8")

    zip_path = article_dir / f"{domain_id}-{article_id}-publish.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in package_dir.rglob("*"):
            if f.is_file():
                zf.write(f, f.relative_to(package_dir))
    return zip_path
