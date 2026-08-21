"""初始化数据库与领域注册。"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.config import load_domains  # noqa: E402
from pipeline.db import init_db, upsert_domain  # noqa: E402


def main() -> None:
    init_db()
    for d in load_domains():
        upsert_domain(d.id, d.name, str(d.dir / "config.yaml"))
        print(f"[init] 领域 {d.id}（{d.name}）已注册")
    print("[init] 完成")


if __name__ == "__main__":
    main()
