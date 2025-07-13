"""Utility to load chat service plugins from file paths."""
from __future__ import annotations

import importlib.util
import os
from typing import List

from .services import ChatService


def load_plugins() -> List[ChatService]:
    paths = os.environ.get("CHATBOT_PLUGIN_PATHS")
    services: List[ChatService] = []
    if not paths:
        return services
    for path in paths.split(os.pathsep):
        if not path:
            continue
        spec = importlib.util.spec_from_file_location("chat_plugin", path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            service = getattr(module, "get_service", None)
            if callable(service):
                inst = service()
                services.append(inst)
    return services
