from __future__ import annotations

import importlib.util
import os
from typing import List

from .infrastructure.chat_service import ChatService


def load_plugins() -> List[ChatService]:
    paths = os.environ.get("CHATBOT_PLUGIN_PATHS")
    services: List[ChatService] = []
    if not paths:
        return services
    for path in paths.split(os.pathsep):
        if not path:
            continue
        if os.path.isfile(path):
            spec = importlib.util.spec_from_file_location("chat_plugin", path)
        else:
            spec = importlib.util.find_spec(path)
        if spec is None:
            continue
        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)  # type: ignore
        except Exception:
            continue
        if hasattr(module, "get_chat_service"):
            try:
                service = module.get_chat_service()
                services.append(service)
            except Exception:
                continue
    return services
