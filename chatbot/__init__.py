"""Chatbot service package with plugin support."""
from __future__ import annotations

from .composite import CompositeChatService
from .plugin_loader import load_plugins

__all__ = ["CompositeChatService", "load_plugins"]
