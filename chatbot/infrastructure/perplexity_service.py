from __future__ import annotations

from .chat_service import ChatService

try:
    import httpx  # type: ignore
except Exception:  # pragma: no cover - optional
    httpx = None

class PerplexityService:
    name = "perplexity"

    @staticmethod
    def chat(prompt: str) -> str:
        if httpx is None:
            raise RuntimeError("httpx required for PerplexityService")
        return f"[perplexity] {prompt}"
