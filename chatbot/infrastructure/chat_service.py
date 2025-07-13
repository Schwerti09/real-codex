from __future__ import annotations

from typing import Protocol

class ChatService(Protocol):
    """Simple chat service interface."""

    name: str

    def chat(self, prompt: str) -> str:
        """Return a reply for the given prompt."""
        ...
