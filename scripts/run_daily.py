"""每日流水线入口：python scripts/run_daily.py --domain ai-tools [--until assess|draft|package] [--auto-select N]"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.orchestrator import run_daily  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description="XHS 热点流水线每日运行")
    ap.add_argument("--domain", required=True, help="领域 id")
    ap.add_argument("--date", default=None, help="日期 YYYY-MM-DD（默认今天）")
    ap.add_argument("--until", default="assess", choices=["collect", "assess", "draft", "package"])
    ap.add_argument("--auto-select", type=int, default=0, help="自动选中前 N 条候选（测试/演示用）")
    args = ap.parse_args()

    result = run_daily(args.domain, date=args.date, until=args.until, auto_select=args.auto_select)
    print(result)


if __name__ == "__main__":
    main()
