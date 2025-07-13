"""Simulation utilities for global drone fleets."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Tuple
import random
import math

from .agents import FleetController
from .sensors import SensorManager
from .swarm import SwarmCommunicator
from .security import EmergencyProtocol


@dataclass
class DroneState:
    position: Tuple[float, float]
    battery: float = 100.0
    co2: float = 0.0
    resources: Dict[str, float] = field(
        default_factory=lambda: {
            "water": 0.0,
            "fuel": 0.0,
            "energy": 0.0,
            "oxygen": 0.0,
        }
    )
    planet: str = "earth"


@dataclass
class Simulation:
    num_drones: int
    gravity: float = 9.81
    battery_threshold: float = 20.0
    controller: FleetController = field(init=False)
    state: Dict[str, DroneState] = field(init=False)
    total_co2: float = 0.0
    sensors: SensorManager = field(init=False)
    swarm: SwarmCommunicator = field(init=False)
    emergency: EmergencyProtocol = field(init=False)

    def __post_init__(self) -> None:
        drone_ids = [f"drone_{i}" for i in range(self.num_drones)]
        self.controller = FleetController(drone_ids)
        self.state = {
            did: DroneState(position=(random.random() * 10, random.random() * 10))
            for did in drone_ids
        }
        for state in self.state.values():
            state.planet = "earth"
        self.sensors = SensorManager(broker_url="local")
        self.swarm = SwarmCommunicator(self.sensors)
        self.emergency = EmergencyProtocol()

    def step(self) -> None:
        actions = self.controller.compute_actions(self.state)
        # Apply actions to update drone states (placeholder)
        for did, route in actions.items():
            x, y = self.state[did].position
            dx = random.random() - 0.5
            dy = random.random() - 0.5
            # simple swarm collision avoidance
            neighbors = [
                {"id": oid, "position": self.state[oid].position}
                for oid in self.state
                if oid != did
            ]
            avoid = self.swarm.avoid_collisions(did, (x, y), neighbors)
            dx += avoid[0]
            dy += avoid[1]
            self.state[did].position = (x + dx, y + dy)
            g = 3.71 if self.state[did].planet == "mars" else self.gravity
            usage = math.hypot(dx, dy) * g * 0.01
            self.state[did].battery -= usage
            self.state[did].co2 += usage * 0.01
            self.total_co2 += usage * 0.01
            if self.state[did].battery < self.battery_threshold:
                self.emergency.execute(did, "low_battery")

    def run(self, steps: int = 10) -> None:
        for _ in range(steps):
            self.step()


class GlobalSimulation(Simulation):
    """Simulation for large fleets including satellites."""

    world_size: Tuple[float, float] = (360.0, 180.0)  # degrees for lat/long
    planet: str = "earth"

    def __post_init__(self) -> None:
        if self.planet.lower() == "mars":
            self.gravity = 3.71
        super().__post_init__()
        # Overwrite positions for global scale
        for state in self.state.values():
            state.position = (
                random.random() * self.world_size[0] - 180.0,
                random.random() * self.world_size[1] - 90.0,
            )


class HybridSimulation(Simulation):
    """Simulates a fleet split between Earth and Mars."""

    earth_ratio: float = 0.5

    def __post_init__(self) -> None:
        earth_drones = int(self.num_drones * self.earth_ratio)
        super().__post_init__()
        # First half Earth, rest Mars
        for i, state in enumerate(self.state.values()):
            if i < earth_drones:
                state.position = (
                    random.random() * 360 - 180,
                    random.random() * 180 - 90,
                )
                state.planet = "earth"
            else:
                state.position = (
                    random.random() * 360 - 180,
                    random.random() * 180 - 90,
                )
                state.planet = "mars"
                state.battery *= 3.71 / 9.81

@dataclass
class NodeState:
    """Represents a household, colony or satellite node."""
    demand: Dict[str, float]
    supply: Dict[str, float]
    position: Tuple[float, float]
    planet: str = "earth"


@dataclass
class ResourceNetworkSimulation(HybridSimulation):
    """Simulates resource flows across a large interplanetary network."""

    nodes: int = 0
    latency_min: float = 4.0  # minutes between Earth and Mars
    latency_max: float = 24.0
    node_state: Dict[str, NodeState] = field(init=False)

    def __post_init__(self) -> None:
        super().__post_init__()
        self.node_state = {}
        for i in range(self.nodes):
            nid = f"node_{i}"
            self.node_state[nid] = NodeState(
                demand={"water": random.random() * 5, "oxygen": random.random() * 5, "energy": random.random() * 20},
                supply={"water": random.random() * 5, "oxygen": random.random() * 5, "energy": random.random() * 20},
                position=(random.random() * 360 - 180, random.random() * 180 - 90),
                planet="mars" if i % 2 else "earth",
            )

    def step(self) -> None:
        # Simulate communication latency between Earth and Mars
        latency = random.uniform(self.latency_min, self.latency_max) * 60
        try:
            import time
            time.sleep(0 if latency < 0.1 else 0)  # skip actual wait in demo
        except Exception:  # pragma: no cover - unlikely
            pass
        super().step()
        for did, state in self.state.items():
            node_key = f"node_{random.randrange(self.nodes)}"
            node = self.node_state[node_key]
            # Simple placeholder: transfer one unit of water if available
            if node.supply.get("water", 0) > 1:
                state.resources.setdefault("water", 0)
                state.resources["water"] += 1
                node.supply["water"] -= 1
                self.total_co2 -= 0.001  # pretend savings from efficient routing
