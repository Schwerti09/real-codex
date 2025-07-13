from __future__ import annotations

from .chat_service import ChatService

try:
    import httpx  # type: ignore
except Exception:  # pragma: no cover - optional
    httpx = None

class ClaudeService:
    name = "claude"

    @staticmethod
    def chat(prompt: str) -> str:
        if httpx is None:
            raise RuntimeError("httpx required for ClaudeService")
        return f"[claude] {prompt}"
