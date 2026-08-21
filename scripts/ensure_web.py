"""确保审核界面在 8000 端口运行（幂等）：已监听则跳过，否则拉起 uvicorn。"""

from __future__ import annotations

import socket
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PORT = 8000


def port_open(port: int) -> bool:
    with socket.socket() as s:
        s.settimeout(1)
        return s.connect_ex(("127.0.0.1", port)) == 0


def main() -> None:
    if port_open(PORT):
        print(f"web already running on {PORT}")
        return
    log_dir = ROOT / "data"
    log_dir.mkdir(parents=True, exist_ok=True)
    log = log_dir / "web.log"
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    with open(log, "a", encoding="utf-8") as f:
        subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "web.app:app", "--host", "0.0.0.0", "--port", str(PORT)],
            cwd=str(ROOT),
            stdout=f,
            stderr=subprocess.STDOUT,
            creationflags=flags,
        )
    print(f"web started on {PORT}")


if __name__ == "__main__":
    main()
