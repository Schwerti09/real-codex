"""Composite chat service that routes to multiple providers."""
from __future__ import annotations

from typing import List

from .services import ChatService, GrokService, OpenAIService, ClaudeService, PerplexityService, DeepSeekService
from .plugin_loader import load_plugins


class CompositeChatService:
    """Try multiple providers in sequence with fallback."""

    def __init__(self, services: List[ChatService] | None = None) -> None:
        if services is None:
            services = [
                GrokService(),
                OpenAIService(),
                ClaudeService(),
                PerplexityService(),
                DeepSeekService(),
            ]
            services.extend(load_plugins())
        self.services = services

    def send_message(self, prompt: str) -> str:
        last_exc: Exception | None = None
        for service in self.services:
            try:
                return service.send_message(prompt)
            except Exception as exc:  # pragma: no cover - runtime path
                last_exc = exc
                continue
        raise RuntimeError("All providers failed") from last_exc
