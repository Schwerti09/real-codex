"""Swarm intelligence utilities for collision avoidance and coordination."""
from typing import Any, Dict, List

try:
    import numpy as np
    import networkx as nx
except Exception:  # pragma: no cover - optional dependencies
    np = None  # type: ignore
    nx = None  # type: ignore

try:
    from dgl import DGLGraph
except Exception:  # pragma: no cover - optional dependency
    DGLGraph = None  # type: ignore


class SwarmCommunicator:
    """Handles inter-drone communication for distributed decision making."""

    def __init__(self, sensor_manager: 'SensorManager'):
        self.sensor_manager = sensor_manager
        self.graph = nx.Graph() if nx is not None else None
        self.dgl_graph = DGLGraph() if DGLGraph is not None else None

    def broadcast(self, drone_id: str, message: Dict[str, Any]) -> None:
        self.sensor_manager.publish_state(f"drones/{drone_id}/broadcast", message)
        if self.graph is not None:
            self.graph.add_node(drone_id, pos=message.get("position", (0.0, 0.0)))
        if self.dgl_graph is not None and np is not None:
            feat = np.array([message.get("battery", 0.0), *message.get("position", (0, 0))], dtype=float)
            self.dgl_graph.add_nodes(1, feat=feat)

    def receive(self, topic: str) -> None:
        self.sensor_manager.subscribe(topic)

    def avoid_collisions(self, drone_id: str, position: tuple[float, float], neighbors: List[Dict[str, Any]]) -> List[float]:
        if np is None:
            return [0.0, 0.0]
        force = np.zeros(2)
        for neighbor in neighbors:
            if neighbor.get("id") == drone_id:
                continue
            if self.graph is not None:
                self.graph.add_edge(drone_id, neighbor.get("id"))
            dist = np.linalg.norm(np.array(position) - np.array(neighbor.get("position", (0, 0))))
            if dist < 0.5:
                force += (np.array(position) - np.array(neighbor.get("position", (0, 0)))) / (dist ** 2 + 1e-6)
        return force.tolist()

    def optimize_swarm(self, drone_states: Dict[str, Dict]) -> Dict[str, List[float]]:
        """Placeholder method for GNN-based swarm optimization."""
        if self.dgl_graph is not None and np is not None:
            for did, state in drone_states.items():
                feat = np.array([state.get("battery", 0.0), *state.get("position", (0, 0))], dtype=float)
                self.dgl_graph.add_nodes(1, feat=feat)
        return {
            did: self.avoid_collisions(did, st.get("position", (0, 0)), [])
            for did, st in drone_states.items()
        }
