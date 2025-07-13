from __future__ import annotations

from .chat_service import ChatService

try:
    import httpx  # type: ignore
except Exception:  # pragma: no cover - optional
    httpx = None

class DeepSeekService:
    name = "deepseek"

    @staticmethod
    def chat(prompt: str) -> str:
        if httpx is None:
            raise RuntimeError("httpx required for DeepSeekService")
        return f"[deepseek] {prompt}"
