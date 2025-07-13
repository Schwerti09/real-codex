import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from drone_fleet.simulation import ResourceNetworkSimulation
from drone_fleet.blockchain import QuantumBlockchain
from drone_fleet.agents import FleetController


def test_simulation_runs():
    sim = ResourceNetworkSimulation(num_drones=10, nodes=5)
    sim.run(steps=2)
    assert isinstance(sim.total_co2, float)
    assert len(sim.state) == 10
    assert len(sim.node_state) == 5
    # ensure emergency protocol list exists
    assert isinstance(sim.emergency.events, list)


def test_blockchain_trade():
    chain = QuantumBlockchain()
    block = chain.create_trade("earth_base", "mars_base", "water", 100.0)
    assert chain.verify_chain()
    assert block.data["trade"]["amount"] == 100.0


def test_fleet_controller_actions():
    controller = FleetController(["d1", "d2"])
    state = {
        "d1": type("obj", (), {"position": [0.0, 0.0, 0.0]})(),
        "d2": type("obj", (), {"position": [1.0, 1.0, 0.0]})(),
    }
    actions = controller.compute_actions(state, {"weather": "sunny"})
    assert isinstance(actions, dict)


def test_emergency_triggered():
    sim = ResourceNetworkSimulation(num_drones=1, nodes=1)
    # force battery low
    for s in sim.state.values():
        s.battery = 0.1
    sim.step()
    assert sim.emergency.events
    # check log file was written
    assert os.path.exists(sim.emergency.storage_path)
    with open(sim.emergency.storage_path, "r", encoding="utf-8") as f:
        assert any("low_battery" in line for line in f)
    os.remove(sim.emergency.storage_path)
