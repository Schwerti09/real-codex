# -*- coding: utf-8 -*-
"""Plug-in architecture for external data sources and IoT integrations."""

from __future__ import annotations

import logging
from typing import Dict, List, Protocol


class DataPlugin(Protocol):
    """Protocol for data plugins."""

    name: str

    def start(self) -> None:
        ...

    def stop(self) -> None:
        ...


class PluginManager:
    """Manages data plugins."""

    def __init__(self) -> None:
        self._plugins: Dict[str, DataPlugin] = {}

    def register(self, plugin: DataPlugin) -> None:
        self._plugins[plugin.name] = plugin

    def start_all(self) -> None:
        for plugin in self._plugins.values():
            try:
                plugin.start()
            except Exception as exc:
                logging.error("Plugin %s failed to start: %s", plugin.name, exc)

    def stop_all(self) -> None:
        for plugin in self._plugins.values():
            try:
                plugin.stop()
            except Exception as exc:
                logging.error("Plugin %s failed to stop: %s", plugin.name, exc)

    @property
    def plugins(self) -> List[str]:
        return list(self._plugins.keys())

    def info(self) -> Dict[str, str]:
        return {name: plugin.__class__.__name__ for name, plugin in self._plugins.items()}


# Example plugin for MQTT
try:
    import paho.mqtt.client as mqtt
except Exception:  # pragma: no cover - optional dependency
    mqtt = None


class MQTTPlugin:
    """Example MQTT data plugin."""

    def __init__(self, broker: str, topic: str) -> None:
        self.name = "mqtt"
        self.broker = broker
        self.topic = topic
        self.client: mqtt.Client | None = None

    def start(self) -> None:
        if mqtt is None:
            return
        self.client = mqtt.Client()
        self.client.on_message = self.on_message
        self.client.connect(self.broker)
        self.client.subscribe(self.topic)
        self.client.loop_start()

    def stop(self) -> None:
        if self.client is not None:
            self.client.loop_stop()
            self.client.disconnect()

    def on_message(self, client: mqtt.Client, userdata, msg) -> None:
        print(f"MQTTPlugin received: {msg.payload.decode()}")


# Optional plugin fetching weather data
try:
    import requests
except Exception:  # pragma: no cover - optional dependency
    requests = None


class WeatherPlugin:
    """Fetches weather data from a REST API."""

    def __init__(self, api_url: str) -> None:
        self.name = "weather"
        self.api_url = api_url
        self.data: Dict[str, float] | None = None

    def start(self) -> None:
        if requests is None:
            return
        try:
            resp = requests.get(self.api_url, timeout=5)
            self.data = resp.json()
        except Exception as exc:  # pragma: no cover - network
            print(f"WeatherPlugin failed: {exc}")

    def stop(self) -> None:
        self.data = None


class MarketDataPlugin:
    """Mock plugin for energy market prices."""

    def __init__(self, api_url: str) -> None:
        self.name = "market"
        self.api_url = api_url
        self.price: float | None = None

    def start(self) -> None:
        if requests is None:
            return
        try:
            resp = requests.get(self.api_url, timeout=5)
            data = resp.json()
            self.price = float(data.get("price", 0.0))
        except Exception as exc:  # pragma: no cover - network
            print(f"MarketDataPlugin failed: {exc}")

    def stop(self) -> None:
        self.price = None
