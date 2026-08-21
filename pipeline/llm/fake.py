"""测试用假模型：返回固定 JSON，避免依赖 API。"""

from __future__ import annotations

import json


class FakeProvider:
    def __init__(self, response: dict | None = None, text: str = ""):
        self.response = response
        self.text = text
        self.calls: list[str] = []

    def chat(self, prompt, system="", json_mode=True, temperature=0.6, max_tokens=4096):
        self.calls.append(prompt)
        if json_mode:
            return self.response if self.response is not None else {}
        return self.text or json.dumps(self.response, ensure_ascii=False)
