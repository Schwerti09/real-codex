import os
from pathlib import Path

import pytest

from chatbot.composite import CompositeChatService
from chatbot.infrastructure.openai_service import OpenAIService


def test_fallback(monkeypatch):
    service = CompositeChatService(providers=["openai", "claude"])

    def fail(prompt: str) -> str:
        raise RuntimeError("boom")

    monkeypatch.setattr(OpenAIService, "chat", fail)
    reply = service.chat("hi")
    assert reply.startswith("[claude]")


def test_plugin_loading(tmp_path, monkeypatch):
    plugin_path = tmp_path / "dummy_plugin.py"
    plugin_path.write_text(
        """
from chatbot.infrastructure.chat_service import ChatService
class Dummy:
    name = 'dummy'
    def chat(self, prompt:str)->str:
        return 'dummy:' + prompt

def get_chat_service():
    return Dummy()
"""
    )
    monkeypatch.setenv("CHATBOT_PLUGIN_PATHS", str(plugin_path))
    service = CompositeChatService(providers=["openai"])
    names = [svc.name for svc in service.services]
    assert "dummy" in names
    reply = service.chat("hi")
    assert reply.startswith("dummy:")
