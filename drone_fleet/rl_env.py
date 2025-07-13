"""Gym environment for training drone routing agents."""
from __future__ import annotations

from typing import Tuple

try:
    import gym
    from gym import spaces
    import numpy as np
except Exception:  # pragma: no cover - optional dependency
    gym = None  # type: ignore
    spaces = None  # type: ignore
    np = None  # type: ignore

if gym is not None:

    class DroneRouteEnv(gym.Env):
        """Multi-drone navigation environment with simple collision avoidance."""

        def __init__(self, goal: Tuple[float, float] = (0.0, 0.0), n_drones: int = 1) -> None:
            self.goal = np.array(goal, dtype=np.float32)
            self.n_drones = n_drones
            self.observation_space = spaces.Box(
                low=-100.0, high=100.0, shape=(n_drones, 3), dtype=np.float32
            )
            self.action_space = spaces.Box(
                low=-1.0, high=1.0, shape=(n_drones, 2), dtype=np.float32
            )
            self.state = np.zeros((n_drones, 3), dtype=np.float32)
            self.gravity = 9.81

        def reset(self, *, seed: int | None = None, options: dict | None = None):
            super().reset(seed=seed)  # type: ignore[arg-type]
            self.state = np.random.uniform(-10, 10, (self.n_drones, 3)).astype(np.float32)
            return self.state, {}

        def _check_collisions(self) -> float:
            collisions = 0
            for i in range(self.n_drones):
                for j in range(i + 1, self.n_drones):
                    if np.linalg.norm(self.state[i, :2] - self.state[j, :2]) < 0.1:
                        collisions += 1
            return collisions / max(1, self.n_drones)

        def step(self, action):
            self.state[:, :2] += action
            distances = np.linalg.norm(self.state[:, :2] - self.goal, axis=1)
            collisions = self._check_collisions()
            rewards = -distances - 10 * collisions
            dones = distances < 0.5
            return self.state, rewards, dones, False, {}
else:

    class DroneRouteEnv:  # type: ignore
        """Placeholder requiring gym to be installed."""

        def __init__(self, *_, **__):
            raise ImportError("gym is required for DroneRouteEnv")
