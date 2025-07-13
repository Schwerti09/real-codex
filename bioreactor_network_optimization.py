# -*- coding: utf-8 -*-
"""Scalable control system for a network of algae bioreactors.

This example demonstrates how multi-agent reinforcement learning, Kafka based
stream processing, blockchain logging and a FastAPI interface can be combined
into one application. The code is simplified for demonstration purposes and
focuses on structure rather than production-ready performance.
"""

from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass
from typing import Any, Dict, List
import logging

import numpy as np
try:
    import torch
    import torch.nn as nn
    if getattr(torch, "__fake__", False):
        raise ImportError("fake torch")
except Exception:  # pragma: no cover - optional dependency
    torch = None  # type: ignore
    nn = None  # type: ignore

try:
    from stable_baselines3 import PPO  # type: ignore
    from gym import Env
    from gym.spaces import Box, MultiDiscrete
except Exception:  # pragma: no cover - optional dependency
    PPO = Env = Box = MultiDiscrete = None  # type: ignore
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer

from user_management import router as user_router, get_current_user
from plugin_system import (
    PluginManager,
    MQTTPlugin,
    WeatherPlugin,
    MarketDataPlugin,
)
from onboarding import router as onboarding_router
from analysis_module import EarlyWarningSystem, detect_anomalies

# Optional libraries used for I/O and visualization. They are imported lazily
# because they are heavy and not required for running unit tests.
try:
    import paho.mqtt.client as mqtt
    from kafka import KafkaConsumer, KafkaProducer
    from dash import Dash, dcc, html, Input, Output
    import pandas as pd
    import plotly.express as px
    from web3 import Web3
except Exception:  # pragma: no cover - optional deps may not be installed
    mqtt = None  # type: ignore
    KafkaConsumer = KafkaProducer = None  # type: ignore
    Dash = dcc = html = Input = Output = None  # type: ignore
    pd = px = None  # type: ignore
    Web3 = None  # type: ignore

# Basic logging configuration
logging.basicConfig(level=logging.INFO)
# ---------------------------------------------------------------------------
# Data classes and utility functions
# ---------------------------------------------------------------------------

@dataclass
class SensorState:
    """Single bioreactor sensor reading."""

    reactor_id: str
    light: float
    temperature: float
    co2: float
    nutrients: float
    ph: float

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "SensorState":
        return cls(
            reactor_id=str(d.get("reactor_id", "r0")),
            light=float(d.get("light", 0.0)),
            temperature=float(d.get("temperature", 0.0)),
            co2=float(d.get("co2", 0.0)),
            nutrients=float(d.get("nutrients", 0.0)),
            ph=float(d.get("ph", 7.0)),
        )


def algae_growth_rate(light: float, temperature: float, co2: float, nutrients: float) -> float:
    """Very small growth model used for demonstration only."""
    temp_factor = np.exp(-((temperature - 25.0) ** 2) / 50.0)
    return 0.1 * light * temp_factor * co2 * nutrients


# ---------------------------------------------------------------------------
# RL agent
# ---------------------------------------------------------------------------

class MultiAgentDQN(nn.Module if nn is not None else object):
    """Minimal multi-agent DQN used for demonstration."""

    def __init__(self, state_dim: int, action_dim: int, n_agents: int):
        super().__init__()
        self.n_agents = n_agents
        if nn is not None:
            self.net = nn.Sequential(
                nn.Linear(state_dim, 128),
                nn.ReLU(),
                nn.Linear(128, 64),
                nn.ReLU(),
                nn.Linear(64, action_dim * n_agents),
            )
        else:  # pragma: no cover - CPU fallback
            self.net = None

    def forward(self, x: torch.Tensor) -> torch.Tensor:  # pragma: no cover - trivial
        return self.net(x)

    def act(self, states: np.ndarray) -> np.ndarray:
        if torch is None or self.net is None:
            return np.zeros((self.n_agents, 3), dtype=float)
        with torch.no_grad():
            t = torch.from_numpy(states.astype(np.float32))
            q_values = self(t)
            return q_values.numpy().reshape(self.n_agents, -1)


class MultiAgentTransformer(nn.Module if nn is not None else object):
    """Transformer-based multi-agent policy."""

    def __init__(self, state_dim: int, action_dim: int, n_agents: int, n_heads: int = 4, num_layers: int = 2) -> None:
        super().__init__()
        self.n_agents = n_agents
        if nn is not None:
            encoder_layer = nn.TransformerEncoderLayer(d_model=state_dim, nhead=n_heads)
            self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
            self.fc = nn.Linear(state_dim, action_dim)
        else:  # pragma: no cover - CPU fallback
            self.encoder = self.fc = None

    def forward(self, x: torch.Tensor) -> torch.Tensor:  # pragma: no cover - trivial
        # Transformer expects shape (seq_len, batch, feature). We treat agents as sequence.
        if self.encoder is None or self.fc is None:
            return x
        x = x.unsqueeze(1)
        enc = self.encoder(x)
        out = self.fc(enc.squeeze(1))
        return out

    def act(self, states: np.ndarray) -> np.ndarray:
        if torch is None or self.encoder is None:
            return np.zeros((self.n_agents, 3), dtype=float)
        with torch.no_grad():
            t = torch.from_numpy(states.astype(np.float32))
            logits = self(t)
            return logits.numpy()


class BioreactorEnv(Env if Env is not None else object):
    """Simple environment for RL training using Stable-Baselines3."""

    def __init__(self, n_reactors: int = 100):
        super().__init__()
        self.n_reactors = n_reactors
        if Box is None:
            raise RuntimeError("gym is required for RL training")
        self.observation_space = Box(low=0.0, high=100.0, shape=(n_reactors, 5), dtype=np.float32)
        self.action_space = MultiDiscrete([3] * n_reactors)
        self.state = np.random.uniform(0, 100, (n_reactors, 5)).astype(np.float32)

    def step(self, action):  # type: ignore[override]
        states = [
            SensorState(
                reactor_id=f"r{i}",
                light=self.state[i, 0],
                temperature=self.state[i, 1],
                co2=self.state[i, 2],
                nutrients=self.state[i, 3],
                ph=self.state[i, 4],
            )
            for i in range(self.n_reactors)
        ]
        absorptions = [algae_growth_rate(s.light, s.temperature, s.co2, s.nutrients) for s in states]
        reward = float(np.sum(absorptions))
        self.state = np.random.uniform(0, 100, (self.n_reactors, 5)).astype(np.float32)
        done = False
        return self.state, reward, done, {}

    def reset(self):  # type: ignore[override]
        self.state = np.random.uniform(0, 100, (self.n_reactors, 5)).astype(np.float32)
        return self.state


# ---------------------------------------------------------------------------
# Optimizer orchestrating multiple reactors
# ---------------------------------------------------------------------------

class BioreactorNetworkOptimizer:
    def __init__(self, n_reactors: int = 100):
        self.n_reactors = n_reactors
        # Use a Transformer-based agent for improved coordination
        self.agent = MultiAgentTransformer(state_dim=5, action_dim=3, n_agents=n_reactors)
        self.data_history: Dict[str, List[tuple]] = {f"reactor_{i}": [] for i in range(n_reactors)}
        self.blockchain = self._setup_blockchain()
        self.kafka_producer = self._setup_kafka()
        if PPO is not None:
            self.env = BioreactorEnv(n_reactors)
            self.model = PPO("MlpPolicy", self.env, verbose=0)
        else:
            self.env = None
            self.model = None

    def _setup_blockchain(self):  # pragma: no cover - external I/O
        if Web3 is None:
            return None
        provider = Web3.HTTPProvider("http://localhost:8545")
        w3 = Web3(provider)
        return w3

    def _setup_kafka(self):  # pragma: no cover - external I/O
        if KafkaProducer is None:
            return None
        return KafkaProducer(bootstrap_servers="localhost:9092")

    def train(self, timesteps: int = 1000) -> None:
        """Train the PPO model if available."""
        if self.model is None:
            logging.warning("stable-baselines3 not installed; skipping training")
            return
        self.model.learn(total_timesteps=timesteps)

    def log_to_blockchain(self, reactor_id: str, absorption: float):  # pragma: no cover - external I/O
        if self.blockchain is None:
            return
        # In a real implementation this would send a transaction.
        print(f"Logging {reactor_id} absorption {absorption} to blockchain")

    # Core processing
    def process_states(self, states: List[SensorState]):
        arrays = np.array(
            [[s.light, s.temperature, s.co2, s.nutrients, s.ph] for s in states],
            dtype=np.float32,
        )
        if self.model is not None:
            actions, _ = self.model.predict(arrays, deterministic=True)
        else:
            actions = self.agent.act(arrays)
        absorptions = [
            algae_growth_rate(s.light, s.temperature, s.co2, s.nutrients)
            for s in states
        ]
        for idx, (state, absorption) in enumerate(zip(states, absorptions)):
            rid = state.reactor_id
            self.data_history.setdefault(rid, []).append((time.time(), absorption))
            self.log_to_blockchain(rid, absorption)
            if self.kafka_producer is not None:
                self.kafka_producer.send("co2_absorption", json.dumps({
                    "reactor": rid,
                    "absorption": absorption,
                }).encode())
            if warning_system.update(absorption):
                logging.warning("Anomaly detected for %s", rid)
        return actions, absorptions


# ---------------------------------------------------------------------------
# API and dashboard setup
# ---------------------------------------------------------------------------

app = FastAPI(title="Bioreactor Network Optimization API")
app.include_router(user_router)
app.include_router(onboarding_router)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

optimizer = BioreactorNetworkOptimizer()
plugins = PluginManager()
plugins.register(MQTTPlugin(broker="localhost", topic="bioreactor/sensors"))
plugins.register(WeatherPlugin(api_url="https://example.com/weather"))
plugins.register(MarketDataPlugin(api_url="https://example.com/market"))
warning_system = EarlyWarningSystem()


@app.post("/optimize")
async def optimize_endpoint(payload: List[Dict[str, Any]], token: str = Depends(oauth2_scheme)):
    if token != "secret-token":  # extremely small example authentication
        raise HTTPException(status_code=401, detail="Invalid token")
    states = [SensorState.from_dict(p) for p in payload]
    actions, absorptions = optimizer.process_states(states)
    return JSONResponse({
        "actions": [a.tolist() for a in actions],
        "co2_absorptions": absorptions,
    })


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/anomalies")
def anomalies() -> Dict[str, Any]:
    history = warning_system.history
    return {
        "history": history,
        "anomalies": detect_anomalies(history),
        "forecast": warning_system.latest_forecast(),
    }


# Dash dashboard (mounted on top of FastAPI)
if Dash is not None:
    dash_app = Dash(__name__, server=app, url_base_pathname="/dashboard/")
    dash_app.layout = html.Div([
        dcc.Graph(id="co2-graph"),
        dcc.Interval(id="interval", interval=1000, n_intervals=0),
    ])

    @dash_app.callback(Output("co2-graph", "figure"), [Input("interval", "n_intervals")])
    def update_graph(n):  # pragma: no cover - visualization
        if pd is None:
            return {}
        df = pd.DataFrame(columns=["Time", "CO2", "Reactor"])
        for rid, data in optimizer.data_history.items():
            if not data:
                continue
            t, val = zip(*data)
            temp_df = pd.DataFrame({"Time": t, "CO2": val, "Reactor": rid})
            df = pd.concat([df, temp_df], ignore_index=True)
        fig = px.line(df, x="Time", y="CO2", color="Reactor", title="CO2 Absorption")
        return fig


def start_mqtt(broker: str, topic: str):  # pragma: no cover - external I/O
    if mqtt is None:
        return None
    client = mqtt.Client()
    client.on_message = lambda c, u, m: optimizer.process_states([SensorState.from_dict(json.loads(m.payload.decode()))])
    client.connect(broker)
    client.subscribe(topic)
    client.loop_start()
    return client


def start_kafka_consumer(topic: str):  # pragma: no cover - external I/O
    if KafkaConsumer is None:
        return None
    consumer = KafkaConsumer(topic, bootstrap_servers="localhost:9092")
    for msg in consumer:
        payload = json.loads(msg.value.decode())
        states = [SensorState.from_dict(p) for p in payload]
        optimizer.process_states(states)


async def simulation_loop(step: float = 0.01):
    """Simulate environment for multiple reactors."""
    while True:
        states = []
        for i in range(optimizer.n_reactors):
            state = SensorState(
                reactor_id=f"r{i}",
                light=np.random.uniform(50, 150),
                temperature=np.random.uniform(20, 30),
                co2=np.random.uniform(0.02, 0.05),
                nutrients=np.random.uniform(0.8, 1.5),
                ph=np.random.uniform(6.5, 8.0),
            )
            states.append(state)
        optimizer.process_states(states)
        await asyncio.sleep(step)


def main(args: List[str]):
    import uvicorn  # pragma: no cover - entry point
    simulate = "--simulate" in args
    if simulate:
        loop = asyncio.get_event_loop()
        loop.create_task(simulation_loop())
    plugins.start_all()
    uvicorn.run(app, host="0.0.0.0", port=8000)
    plugins.stop_all()


if __name__ == "__main__":
    import sys
    main(sys.argv[1:])
