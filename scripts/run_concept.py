"""概念科普入口：python scripts/run_concept.py --domain ai-basics [--concept "复利"] [--until draft|package]

不带 --concept 时从 concepts/<domain>.txt 池顶取一个并归档。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.orchestrator import run_concept  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description="概念科普：讲透一个概念")
    ap.add_argument("--domain", required=True, help="领域 id（content_type=concept）")
    ap.add_argument("--concept", default=None, help="概念名；缺省从概念池取下一个")
    ap.add_argument("--date", default=None, help="日期 YYYY-MM-DD（默认今天）")
    ap.add_argument("--until", default="draft", choices=["draft", "package"])
    args = ap.parse_args()

    result = run_concept(args.domain, concept=args.concept, date=args.date, until=args.until)
    print(result)


if __name__ == "__main__":
    main()
