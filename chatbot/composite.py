from __future__ import annotations

import os
import logging
from typing import List

from prometheus_client import Counter

from .infrastructure.chat_service import ChatService
from .infrastructure.grok_service import GrokService
from .infrastructure.openai_service import OpenAIService
from .infrastructure.claude_service import ClaudeService
from .infrastructure.perplexity_service import PerplexityService
from .infrastructure.deepseek_service import DeepSeekService
from .plugins import load_plugins


class CompositeChatService:
    """Routes messages to available providers with fallback."""

    def __init__(self, providers: List[str] | None = None) -> None:
        builtins = {
            "grok": GrokService(),
            "openai": OpenAIService(),
            "claude": ClaudeService(),
            "perplexity": PerplexityService(),
            "deepseek": DeepSeekService(),
        }
        self.services: List[ChatService] = []
        order = providers or os.environ.get("CHATBOT_PROVIDERS", "grok,openai,claude,perplexity,deepseek").split(",")
        for name in order:
            svc = builtins.get(name.strip())
            if svc:
                self.services.append(svc)
        self.services = load_plugins() + self.services

        self._fallback_counter = Counter(
            "chat_fallback_total", "Number of provider fallbacks"
        )
        self._provider_counter = Counter(
            "chat_provider_total", "Chat provider responses", ["provider"]
        )

    def chat(self, prompt: str) -> str:
        last_err: Exception | None = None
        for service in self.services:
            try:
                reply = service.chat(prompt)
                self._provider_counter.labels(service.name).inc()
                return reply
            except Exception as exc:  # pragma: no cover - fallback
                logging.warning("%s failed: %s", service.name, exc)
                self._fallback_counter.inc()
                last_err = exc
                continue
        raise RuntimeError(f"All providers failed: {last_err}")
