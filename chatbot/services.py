"""Built-in chat services with optional httpx dependency."""
from __future__ import annotations

from typing import Protocol

try:  # optional import
    import httpx  # type: ignore
except Exception:  # pragma: no cover - optional dependency may be missing
    httpx = None  # type: ignore


class ChatService(Protocol):
    """Simple protocol for chat services."""

    name: str

    def send_message(self, prompt: str) -> str:
        ...


class BaseChatService:
    name: str = "base"

    def send_message(self, prompt: str) -> str:  # pragma: no cover - base impl
        if httpx is None:
            return f"{self.name}:{prompt}"
        # In real code we'd call out using httpx
        return f"{self.name}:{prompt}"


class OpenAIService(BaseChatService):
    name = "openai"


class GrokService(BaseChatService):
    name = "grok"


class ClaudeService(BaseChatService):
    name = "claude"


class PerplexityService(BaseChatService):
    name = "perplexity"


class DeepSeekService(BaseChatService):
    name = "deepseek"
