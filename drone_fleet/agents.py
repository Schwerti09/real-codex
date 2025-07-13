"""Reinforcement learning agents for autonomous drones."""

from typing import Any, Dict, List

# RL and numerical libraries are optional because they are heavy
try:
    from stable_baselines3 import PPO
    import numpy as np
    from pettingzoo.utils import BaseParallelWrapper
    from pettingzoo import AECEnv
except Exception:  # pragma: no cover - optional dependency
    PPO = None  # type: ignore
    np = None  # type: ignore
    BaseParallelWrapper = object  # type: ignore
    AECEnv = object  # type: ignore

try:
    import openai  # for Grok 3 / xAI integration
except Exception:  # pragma: no cover - optional dependency
    openai = None  # type: ignore


class DroneEnvWrapper(BaseParallelWrapper):  # type: ignore[misc]
    """Wrap AECEnv to use with SB3 for parallel MARL training."""

    def __init__(self, env: AECEnv):
        super().__init__(env)



class DroneAgent:
    """Represents a single drone agent using RL for path planning."""

    def __init__(self, drone_id: str, model: Any | None = None) -> None:
        self.drone_id = drone_id
        # When stable-baselines3 is available, model can be a PPO instance
        self.policy = model if model is not None else []
        self.context_model = None

    def train(self, env: Any, steps: int = 1000) -> None:
        """Train the agent using PPO on the provided environment."""
        if PPO is None:
            raise ImportError("stable-baselines3 is required for training")
        # Wrap PettingZoo environments when available
        if isinstance(env, AECEnv):
            env = DroneEnvWrapper(env)
        self.policy = PPO("MlpPolicy", env, verbose=0)
        self.policy.learn(total_timesteps=steps)

    def plan_route(self, state: Any, context: Dict | None = None) -> List[Any]:
        """Return a planned route given state and optional contextual data."""
        if PPO is not None and hasattr(self.policy, "predict") and np is not None:
            obs = np.array(state.position, dtype=np.float32)
            action, _ = self.policy.predict(obs, deterministic=True)
            action = action.tolist()
        else:
            action = [state]

        if context and openai is not None and self.context_model is not None:
            try:
                response = openai.ChatCompletion.create(
                    model="grok-3",
                    messages=[
                        {
                            "role": "user",
                            "content": f"Optimize route for {self.drone_id} given {context}",
                        }
                    ],
                )
                action_mod = response["choices"][0]["message"]["content"]
                action.append(action_mod)
            except Exception:  # pragma: no cover - optional
                pass
        return action

    def update_policy(self, experience: Any) -> None:
        """Update the agent's policy based on new experience."""
        if isinstance(self.policy, list):
            self.policy.append(experience)
        elif PPO is not None and hasattr(self.policy, "learn"):
            self.policy.learn(total_timesteps=100, reset_num_timesteps=False)


class FleetController:
    """Manages multiple DroneAgent instances."""

    def __init__(self, drone_ids: List[str]):
        self.agents = {did: DroneAgent(did) for did in drone_ids}

    def compute_actions(self, state: Any, context: Dict | None = None) -> Dict:
        """Compute actions for all drones given the state."""
        return {
            did: agent.plan_route(state[did], context)
            for did, agent in self.agents.items()
        }
