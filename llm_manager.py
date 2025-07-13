# -*- coding: utf-8 -*-
"""Self-healing large language model manager."""

from __future__ import annotations

import importlib
from typing import Dict, Optional
import time

try:
    from prometheus_client import (
        Counter,
        Histogram,
        Gauge,
        CollectorRegistry,
        REGISTRY,
    )
except Exception:  # pragma: no cover - optional dependency
    Counter = Histogram = Gauge = CollectorRegistry = REGISTRY = None  # type: ignore

try:
    from prometheus_client import Gauge
except Exception:  # pragma: no cover - optional dependency
    Gauge = None  # type: ignore


class LLMManager:
    """Manage multiple language models with health monitoring."""

    def __init__(self) -> None:
        self.models: Dict[str, object] = {}
        self.accuracy: Dict[str, float] = {}
        if Gauge is not None:
            labels = ["model", "user_id", "tenant"]
            self.accuracy_gauge = Gauge(
                "llm_accuracy", "Model accuracy", ["model"], registry=REGISTRY
            )
            self.request_counter = Counter(
                "llm_requests_total",
                "LLM requests",
                labels,
                registry=REGISTRY,
            )
            self.error_counter = Counter(
                "llm_errors_total", "LLM errors", labels, registry=REGISTRY
            )
            self.latency_histogram = Histogram(
                "llm_latency_seconds", "LLM latency", labels, registry=REGISTRY
            )
            self.token_counter = Counter(
                "llm_tokens_total", "LLM tokens", labels, registry=REGISTRY
            )
        else:
            self.accuracy_gauge = None
            self.request_counter = None
            self.error_counter = None
            self.latency_histogram = None
            self.token_counter = None

    def register(self, name: str, module_path: str) -> None:
        """Dynamically load a model class from a module."""
        module = importlib.import_module(module_path)
        self.models[name] = getattr(module, "Model")()
        self.accuracy[name] = 1.0
        if self.accuracy_gauge is not None:
            self.accuracy_gauge.labels(model=name).set(1.0)

    def update_accuracy(self, name: str, value: float) -> None:
        self.accuracy[name] = value
        if self.accuracy_gauge is not None:
            self.accuracy_gauge.labels(model=name).set(value)

    def get_model(self) -> Optional[object]:
        """Return the best available model."""
        for name, acc in sorted(self.accuracy.items(), key=lambda x: x[1], reverse=True):
            if acc >= 0.85:
                return self.models[name]
        # fallback: highest accuracy even if below threshold
        if self.accuracy:
            best = max(self.accuracy, key=self.accuracy.get)
            return self.models[best]
        return None

    def reload_weights(self, name: str) -> None:  # pragma: no cover - placeholder
        """Reload model weights without downtime (placeholder)."""
        model = self.models.get(name)
        if model and hasattr(model, "load_weights"):
            model.load_weights()
        self.update_accuracy(name, 1.0)

    def send_prompt(
        self,
        name: str,
        prompt: str,
        context: Optional[dict] = None,
        user_id: str = "anon",
        tenant: str = "default",
    ) -> str:
        """Send a prompt to the specified model and collect metrics."""
        model = self.models.get(name)
        if model is None:
            raise ValueError(f"Model {name} not registered")
        if self.request_counter is not None:
            self.request_counter.labels(model=name, user_id=user_id, tenant=tenant).inc()
        start = time.monotonic()
        try:
            if hasattr(model, "respond"):
                result = model.respond(prompt, context or {})
            else:
                result = str(model(prompt))  # type: ignore
            return result
        except Exception:
            if self.error_counter is not None:
                self.error_counter.labels(model=name, user_id=user_id, tenant=tenant).inc()
            raise
        finally:
            duration = time.monotonic() - start
            if self.latency_histogram is not None:
                self.latency_histogram.labels(model=name, user_id=user_id, tenant=tenant).observe(duration)
            if self.token_counter is not None:
                tokens = len(prompt.split())
                self.token_counter.labels(model=name, user_id=user_id, tenant=tenant).inc(tokens)
