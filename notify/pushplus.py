"""PushPlus 微信推送。"""

from __future__ import annotations

import requests

from pipeline.config import env


def send_pushplus(title: str, content: str) -> dict:
    token = env("PUSHPLUS_TOKEN")
    if not token:
        return {"status": "skipped", "reason": "未配置 PUSHPLUS_TOKEN"}
    resp = requests.post(
        "https://www.pushplus.plus/send",
        json={"token": token, "title": title, "content": content, "template": "html"},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()
