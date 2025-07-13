# -*- coding: utf-8 -*-
"""Reinforcement learning orchestrator for prompt optimization."""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, Tuple
import random


class MetaLearner:
    """Simple Q-learning orchestrator for prompt variations."""

    def __init__(self, actions: list[str] | None = None) -> None:
        self.q_table: Dict[Tuple[str, str], float] = defaultdict(float)
        self.actions = actions or ["default"]
        self.epsilon = 0.1
        self.alpha = 0.1
        self.gamma = 0.9

    def choose_action(self, intent: str) -> str:
        if random.random() < self.epsilon:
            return random.choice(self.actions)
        qs = {a: self.q_table[(intent, a)] for a in self.actions}
        return max(qs, key=qs.get)

    def update(self, intent: str, action: str, reward: float, next_intent: str) -> None:
        best_next = max(self.q_table[(next_intent, a)] for a in self.actions)
        old = self.q_table[(intent, action)]
        self.q_table[(intent, action)] = old + self.alpha * (reward + self.gamma * best_next - old)
