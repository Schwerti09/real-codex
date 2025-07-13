import argparse
from drone_fleet import (
    ResourceNetworkSimulation,
    QuantumBlockchain,
    DroneAgent,
    DroneRouteEnv,
    create_dashboard,
    FleetAPI,
    SensorManager,
    SwarmCommunicator,
)


def run_simulation(num_drones: int, nodes: int, steps: int) -> None:
    sim = ResourceNetworkSimulation(num_drones=num_drones, nodes=nodes)
    sim.run(steps=steps)
    print("Total CO2 emissions:", sim.total_co2)


def run_api() -> None:
    api = FleetAPI()
    import uvicorn
    uvicorn.run(api.app, host="0.0.0.0", port=8000)


def run_dashboard() -> None:
    sensors = SensorManager(broker_url="local")
    app = create_dashboard(sensors)
    app.run_server(host="0.0.0.0", port=8050)


def train_agent(steps: int) -> None:
    try:
        env = DroneRouteEnv(goal=(5.0, 5.0), n_drones=1)
        agent = DroneAgent("trainer")
        agent.train(env, steps=steps)
        obs, _ = env.reset()
        print("Sample action:", agent.plan_route(type("obj", (), {"position": obs[0]})()))
    except Exception as exc:  # pragma: no cover - optional deps
        print("RL training skipped:", exc)


def main() -> None:
    parser = argparse.ArgumentParser(description="Drone Fleet SuperTool")
    parser.add_argument("--simulate", action="store_true", help="run resource network simulation")
    parser.add_argument("--api", action="store_true", help="start REST API")
    parser.add_argument("--dashboard", action="store_true", help="launch dashboard")
    parser.add_argument("--train", action="store_true", help="train demo RL agent")
    parser.add_argument("--drones", type=int, default=100, help="number of drones for simulation")
    parser.add_argument("--nodes", type=int, default=10, help="number of nodes for simulation")
    parser.add_argument("--steps", type=int, default=3, help="simulation steps or training timesteps")
    args = parser.parse_args()

    if args.train:
        train_agent(args.steps)
    if args.simulate:
        run_simulation(args.drones, args.nodes, args.steps)
    if args.api:
        run_api()
    if args.dashboard:
        run_dashboard()


if __name__ == "__main__":
    main()
