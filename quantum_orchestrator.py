# -*- coding: utf-8 -*-
"""Coordinator combining LLM management and meta learning."""

from __future__ import annotations

from typing import Any, Dict

from llm_manager import LLMManager
from meta_learner import MetaLearner


class QuantumOrchestrator:
    """Route tasks between specialized agents using RL and health checks."""

    def __init__(self) -> None:
        self.llm = LLMManager()
        self.meta = MetaLearner(actions=["prompt_a", "prompt_b", "prompt_c"])
        self.agents: Dict[str, Any] = {}

    def register_agent(self, name: str, agent: Any) -> None:
        self.agents[name] = agent

    def handle_request(self, intent: str, context: Dict) -> Any:
        prompt = self.meta.choose_action(intent)
        model = self.llm.get_model()
        if model is None:
            return None
        if hasattr(model, "respond"):
            response = model.respond(prompt, context)
        else:
            response = "ok"
        # simple reward: length of response
        self.meta.update(intent, prompt, float(len(str(response))), intent)
        return response
