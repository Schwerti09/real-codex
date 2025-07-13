from __future__ import annotations

from .chat_service import ChatService

try:  # optional dependency
    import httpx  # type: ignore
except Exception:  # pragma: no cover - optional
    httpx = None

class OpenAIService:
    name = "openai"

    @staticmethod
    def chat(prompt: str) -> str:
        if httpx is None:
            raise RuntimeError("httpx required for OpenAIService")
        # simplified placeholder implementation
        return f"[openai] {prompt}"
