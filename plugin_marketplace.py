# -*- coding: utf-8 -*-
"""Simple registry of third party plugins."""

from __future__ import annotations

from typing import Dict


class PluginMarketplace:
    """Stores available plugin descriptions."""

    def __init__(self) -> None:
        self.available: Dict[str, str] = {
            "mqtt": "MQTT sensor integration",
            "weather": "Weather data feed",
            "market": "Energy market price feed",
        }

    def list_plugins(self) -> Dict[str, str]:
        return self.available.copy()
