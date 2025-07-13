"""Entry point for running a global drone fleet simulation with RL demo."""
from argparse import ArgumentParser
from drone_fleet import (
    ResourceNetworkSimulation,
    QuantumBlockchain,
    DroneAgent,
    DroneRouteEnv,
)


def main() -> None:
    parser = ArgumentParser(description="Run drone fleet simulation")
    parser.add_argument("--drones", type=int, default=1000)
    parser.add_argument("--steps", type=int, default=3)
    parser.add_argument("--battery-threshold", type=float, default=20.0)
    args = parser.parse_args()

    # Demonstration with fewer drones; class supports 1e6 and millions of nodes
    # Train a single agent in the simple environment
    try:
        env = DroneRouteEnv(goal=(5.0, 5.0), n_drones=3)
        agent = DroneAgent("trainer")
        agent.train(env, steps=100)
        obs, _ = env.reset()
        print("Sample action:", agent.plan_route(type("obj", (), {"position": obs[0]})()))
    except Exception as exc:  # pragma: no cover - optional dependencies
        print("RL demo skipped:", exc)
    from llm_manager import LLMManager
    m = LLMManager()
    import types, sys
    mod = types.ModuleType("demo")
    mod.Model = type("M", (), {"respond": lambda self, p, c: "resp"})
    sys.modules["demo"] = mod
    m.register("demo", "demo")
    print("LLM selected:", m.get_model().__class__.__name__)

    simulation = ResourceNetworkSimulation(
        num_drones=args.drones, nodes=100, battery_threshold=args.battery_threshold
    )
    simulation.run(steps=args.steps)
    print("Total CO2 emissions:", simulation.total_co2)
    print("Emergencies triggered:", len(simulation.emergency.events))

    chain = QuantumBlockchain()
    chain.create_trade("earth_base", "mars_base", "water", 100.0)
    chain.execute_contract({"service": "delivery", "fee": 42})
    print("Blockchain length:", len(chain.chain))
    print("Chain valid:", chain.verify_chain())


if __name__ == "__main__":
    main()
