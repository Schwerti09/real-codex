# -*- coding: utf-8 -*-
"""Real-time optimization of CO2 absorption in algae bioreactors.

This script demonstrates how one could combine a neural network based
controller, real time sensor data via MQTT, reinforcement learning and a
simple API to integrate with external systems. The implementation uses
widely available Python libraries such as `numpy`, `paho-mqtt`,
`matplotlib` and `fastapi` together with `torch` for the neural network
model. Each component is simplified but intended to show how such a
system can be composed.

The optimization step is executed in a loop that targets a maximum step
run time of 10ms. In practice the performance heavily depends on the
hardware and load of the event loop. The example assumes pre-trained
weights and omits the training logic for brevity.
"""

import asyncio
import json
import time
from dataclasses import dataclass
from typing import Dict, Any

import numpy as np
import torch
import torch.nn as nn
import paho.mqtt.client as mqtt
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import matplotlib.pyplot as plt


data_history = []
app = FastAPI(title="Bioreactor Optimization API")


@dataclass
class SensorState:
    light: float
    temperature: float
    co2: float
    nutrients: float
    ph: float

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "SensorState":
        return cls(
            light=float(d.get("light", 0.0)),
            temperature=float(d.get("temperature", 0.0)),
            co2=float(d.get("co2", 0.0)),
            nutrients=float(d.get("nutrients", 0.0)),
            ph=float(d.get("ph", 7.0)),
        )


def algae_growth_rate(light: float, temperature: float, co2: float, nutrients: float) -> float:
    """Simple growth model based on typical kinetics.

    The formula is for demonstration only and has no empirical basis.
    """
    temp_factor = np.exp(-((temperature - 25.0) ** 2) / 50.0)
    growth = 0.1 * light * temp_factor * co2 * nutrients
    return growth


class DQNAgent(nn.Module):
    """Minimal deep Q-network for parameter selection."""

    def __init__(self, state_dim: int, action_dim: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(state_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, action_dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)

    def act(self, state: np.ndarray) -> np.ndarray:
        with torch.no_grad():
            tensor_state = torch.from_numpy(state.astype(np.float32))
            q_values = self(tensor_state)
            action = q_values.numpy()
        return action


class BioreactorOptimizer:
    def __init__(self):
        self.agent = DQNAgent(state_dim=5, action_dim=3)
        self.last_state = np.zeros(5, dtype=np.float32)
        self.figure, self.ax = plt.subplots()
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("CO2 Absorption (g/L)")
        plt.ion()

    def update_plot(self, t: float, absorption: float):
        data_history.append((t, absorption))
        x, y = zip(*data_history)
        self.ax.clear()
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("CO2 Absorption (g/L)")
        self.ax.plot(x, y)
        plt.draw()
        plt.pause(0.001)

    def process_state(self, state: SensorState):
        array = np.array([state.light, state.temperature, state.co2, state.nutrients, state.ph], dtype=np.float32)
        action = self.agent.act(array)
        absorption = algae_growth_rate(state.light, state.temperature, state.co2, state.nutrients)
        self.update_plot(time.time(), absorption)
        # In a real system the action would be sent back to the controller here
        self.last_state = array
        return action, absorption


optimizer = BioreactorOptimizer()


@app.post("/optimize")
async def optimize_endpoint(payload: Dict[str, Any]):
    state = SensorState.from_dict(payload)
    action, absorption = optimizer.process_state(state)
    return JSONResponse({"action": action.tolist(), "co2_absorption": absorption})


def on_mqtt_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        state = SensorState.from_dict(payload)
        optimizer.process_state(state)
    except Exception as exc:  # pragma: no cover - runtime log output
        print(f"Failed to process MQTT message: {exc}")


def start_mqtt(broker: str, topic: str):
    client = mqtt.Client()
    client.on_message = on_mqtt_message
    client.connect(broker)
    client.subscribe(topic)
    client.loop_start()
    return client


async def main_loop(step_time: float = 0.01):
    """Runs the optimization loop."""
    while True:
        await asyncio.sleep(step_time)
        # This example only updates visualization on MQTT or API calls


if __name__ == "__main__":
    broker = "localhost"
    topic = "bioreactor/sensors"
    start_mqtt(broker, topic)
    loop = asyncio.get_event_loop()
    loop.create_task(main_loop())
    import uvicorn  # noqa

    uvicorn.run(app, host="0.0.0.0", port=8000)
