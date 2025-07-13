# -*- coding: utf-8 -*-
"""Tiny policy engine simulating OPA behavior for auth workflows."""
from __future__ import annotations

try:
    import yaml
except Exception:  # pragma: no cover - optional dependency
    yaml = None  # type: ignore
from pathlib import Path
from typing import Dict


class PolicyEngine:
    """Loads simple allow/deny policies from a YAML file."""

    def __init__(self, path: str = "policies.yaml") -> None:
        self.path = Path(path)
        self.rules: Dict[str, Dict[str, str]] = {}
        if self.path.exists():
            self.load()

    def load(self) -> None:
        if yaml is not None:
            data = yaml.safe_load(self.path.read_text())
            self.rules = data or {}
        else:
            rules: Dict[str, Dict[str, str]] = {}
            current_role = None
            for line in self.path.read_text().splitlines():
                line = line.strip()
                if not line:
                    continue
                if not line.startswith('-') and line.endswith(':'):
                    current_role = line[:-1]
                    rules.setdefault(current_role, {})
                    continue
                if ':' in line and current_role:
                    action, verdict = line.split(':', 1)
                    rules[current_role][action.strip()] = verdict.strip()
            self.rules = rules

    def allowed(self, user_role: str, action: str) -> bool:
        if not self.rules:
            return True
        actions = self.rules.get(user_role, {})
        result = actions.get(action, "allow")
        return result == "allow"


engine = PolicyEngine()
