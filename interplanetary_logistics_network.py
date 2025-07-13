# -*- coding: utf-8 -*-
"""Quantum-secure interplanetary logistics network example.

This script demonstrates a conceptual system for managing energy and
resource logistics across a large network of drones, habitats and
satellites. It combines a multi-agent reinforcement learning controller,
Kafka based message streaming, a post-quantum blockchain placeholder and
an interactive API. The implementation is simplified and intended for
educational purposes.
"""

from __future__ import annotations

import asyncio
import json
import random
import time
from dataclasses import dataclass
from typing import Any, Dict, List

import numpy as np
try:
    import torch
    import torch.nn as nn
    if getattr(torch, "__fake__", False):
        raise ImportError("fake torch")
except Exception:  # pragma: no cover - optional dependency
    torch = None  # type: ignore
    nn = None  # type: ignore
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer

# Optional heavy dependencies are imported lazily so the script can run
# without them during testing or simulation mode.
try:
    from kafka import KafkaConsumer, KafkaProducer
    from dash import Dash, dcc, html, Input, Output
    import pandas as pd
    import plotly.express as px
    import pqcrypto  # type: ignore - placeholder for Kyber implementation
except Exception:  # pragma: no cover - optional deps
    KafkaConsumer = KafkaProducer = None  # type: ignore
    Dash = dcc = html = Input = Output = None  # type: ignore
    pd = px = None  # type: ignore
    pqcrypto = None  # type: ignore

app = FastAPI(title="Interplanetary Logistics API")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

dashboard: Dash | None = None
if Dash is not None:
    dashboard = Dash(__name__, server=app, url_base_pathname="/dashboard/")

# Kafka producer used for streaming transactions and sensor data
kafka_producer: KafkaProducer | None = None
if KafkaProducer is not None:
    kafka_producer = KafkaProducer(bootstrap_servers="localhost:9092")


def pq_sign(data: bytes) -> bytes:
    """Sign data with a post-quantum algorithm (placeholder)."""
    if pqcrypto is None:
        return b"signature"
    return b"signature"  # In reality you would call pqcrypto APIs


def pq_verify(data: bytes, signature: bytes) -> bool:
    """Verify a post-quantum signature (placeholder)."""
    if pqcrypto is None:
        return True
    return True


@dataclass
class NodeState:
    node_id: str
    consumption: float
    production: float
    radiation: float
    temperature: float

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "NodeState":
        return cls(
            node_id=str(d.get("node_id", "n0")),
            consumption=float(d.get("consumption", 0.0)),
            production=float(d.get("production", 0.0)),
            radiation=float(d.get("radiation", 0.0)),
            temperature=float(d.get("temperature", 0.0)),
        )


class MultiAgentTransformer(nn.Module if nn is not None else object):
    """Transformer-based network for many nodes."""

    def __init__(self, state_dim: int, action_dim: int, n_agents: int, n_heads: int = 4, num_layers: int = 2):
        super().__init__()
        self.n_agents = n_agents
        if nn is not None:
            enc = nn.TransformerEncoderLayer(d_model=state_dim, nhead=n_heads)
            self.encoder = nn.TransformerEncoder(enc, num_layers=num_layers)
            self.fc = nn.Linear(state_dim, action_dim)
        else:
            self.encoder = self.fc = None

    def forward(self, x: torch.Tensor) -> torch.Tensor:  # pragma: no cover - simple
        if self.encoder is None or self.fc is None:
            return x
        x = x.unsqueeze(1)
        enc = self.encoder(x)
        out = self.fc(enc.squeeze(1))
        return out

    def act(self, states: List[np.ndarray]) -> List[np.ndarray]:
        if torch is None or self.encoder is None:
            return [np.zeros(3) for _ in states]
        with torch.no_grad():
            tensor_states = torch.from_numpy(np.array(states, dtype=np.float32))
            logits = self(tensor_states)
            actions = logits.numpy()
        return actions


class LogisticsOptimizer:
    """Coordinates resources across many nodes."""

    def __init__(self, n_nodes: int = 1_000_000):
        self.n_nodes = n_nodes
        # Use Transformer for large-scale coordination
        self.agent = MultiAgentTransformer(state_dim=4, action_dim=3, n_agents=n_nodes)
        self.history: Dict[str, List[tuple[float, float]]] = {
            f"node_{i}": [] for i in range(n_nodes)
        }

    def process_states(self, states: List[NodeState]) -> tuple:
        arrays = [
            np.array([s.consumption, s.production, s.radiation, s.temperature], dtype=np.float32)
            for s in states
        ]
        actions = self.agent.act(arrays)
        balances = [s.production - s.consumption for s in states]
        for i, (state, balance) in enumerate(zip(states, balances)):
            tx = {
                "node": state.node_id,
                "balance": balance,
                "ts": time.time(),
            }
            signature = pq_sign(json.dumps(tx).encode())
            if kafka_producer is not None:
                kafka_producer.send("resource_tx", json.dumps({"tx": tx, "sig": signature.hex()}).encode())
            self.history[state.node_id].append((tx["ts"], balance))
        return actions, balances


optimizer = LogisticsOptimizer()


@app.post("/optimize")
async def optimize_endpoint(payload: List[Dict[str, Any]], token: str = Depends(oauth2_scheme)):
    states = [NodeState.from_dict(p) for p in payload]
    actions, balances = optimizer.process_states(states)
    return JSONResponse({
        "actions": [a.tolist() for a in actions],
        "balances": balances,
    })


if dashboard is not None:
    dashboard.layout = html.Div([
        dcc.Graph(id="balance-graph"),
        dcc.Interval(id="interval", interval=1000, n_intervals=0),
    ])

    @dashboard.callback(
        Output("balance-graph", "figure"), Input("interval", "n_intervals")
    )
    def update_graph(n):  # pragma: no cover - UI
        df = pd.DataFrame({"Time": [], "Balance": [], "Node": []})
        for node_id, history in list(optimizer.history.items())[:100]:
            if not history:
                continue
            times, balances = zip(*history)
            temp = pd.DataFrame({"Time": times, "Balance": balances, "Node": node_id})
            df = pd.concat([df, temp], ignore_index=True)
        fig = px.line(df, x="Time", y="Balance", color="Node", title="Resource Balance")
        return fig


async def simulation_loop(step: float = 0.01):
    """Generate synthetic states for many nodes."""
    while True:
        states = []
        for i in range(optimizer.n_nodes):
            state = NodeState(
                node_id=f"n{i}",
                consumption=random.uniform(0, 10),
                production=random.uniform(0, 12),
                radiation=random.uniform(0, 5),
                temperature=random.uniform(-50, 40),
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
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    import sys
    main(sys.argv[1:])

