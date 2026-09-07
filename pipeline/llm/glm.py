"""智谱 GLM（BigModel 开放平台）实现。OpenAI 兼容协议，Bearer 鉴权。"""

from __future__ import annotations

import json

import requests

from ..config import env
from .base import LLMProvider

BASE = "https://open.bigmodel.cn/api/paas/v4/chat/completions"


def _parse_json_text(text: str) -> dict:
    """容错解析：剥掉 markdown 代码围栏，截取首尾大括号。"""
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"GLM 返回内容不是 JSON: {text[:200]}")
    return json.loads(text[start:end + 1])


class GLMProvider(LLMProvider):
    def __init__(self, model: str = "glm-4-flash"):
        self.model = model
        self.api_key = env("GLM_API_KEY")
        if not self.api_key:
            raise RuntimeError("缺少 GLM_API_KEY（请在 .env 中配置）")

    def chat(
        self,
        prompt: str,
        system: str = "",
        json_mode: bool = True,
        temperature: float = 0.6,
        max_tokens: int = 4096,
    ) -> str | dict:
        messages = []
        if system:
            if json_mode:
                system = system + " 输出必须是合法 JSON 对象，不要包 markdown 代码块。"
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
            # glm-4.5+/5.x 始终思考（不可关闭），只能调档：effort low|high|max。
            # low 档推理开销最小；流水线的深度"思考"由 steelman 等阶段承担。
            "thinking": {"type": "enabled", "effort": "low"},
        }
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

        # 依次降级：response_format+thinking → 无 response_format → 无 thinking
        payloads = [{**payload, "response_format": {"type": "json_object"}}, payload,
                    {k: v for k, v in payload.items() if k != "thinking"}] if json_mode else [payload]

        last_resp = None
        content = ""
        for attempt_payload in payloads:
            resp = requests.post(BASE, headers=headers, json=attempt_payload, timeout=900)
            last_resp = resp
            if resp.status_code == 400:
                continue  # 参数不支持，降级重试
            resp.raise_for_status()
            msg = resp.json()["choices"][0]["message"]
            content = msg.get("content") or ""
            if content.strip():
                break  # 拿到正文
            # 200 但空内容（思考耗尽 token 等）：换下一组参数重试
        if not content.strip():
            debug = last_resp.json()
            ch = debug["choices"][0]
            msg = ch.get("message", {})
            raise ValueError(
                "GLM 返回空内容 | finish={} | usage={} | message_keys={}".format(
                    ch.get("finish_reason"), debug.get("usage"), list(msg.keys())
                )
            )
        if json_mode:
            return _parse_json_text(content)
        return content
