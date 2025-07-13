# Drone Fleet Control

This repository contains a modular Python framework for an AI-driven logistics
network controlling autonomous drones in urban and interplanetary settings. It
demonstrates multi-agent reinforcement learning, real-time sensor integration
over Apache Kafka, swarm-based collision avoidance, a quantum-secure blockchain
for resource trading, and a REST API compatible with major logistics and space
infrastructure.

## Features

- **Multi-agent reinforcement learning** with PettingZoo and PPO for optimized routing across Earth and Mars.
- **Training environment** using Gym for PPO-based route planning and support for hierarchical RL.
- **IoT sensor integration** over Apache Kafka or MQTT, with optional Flink and gRPC streaming.
- **Swarm communication** leveraging NetworkX and DGL for distributed collision avoidance.
- **Scalable sensor pipeline** handling billions of events per day via Kafka.
- **Resource flow optimization** across energy, water and oxygen networks.
- **REST API** compatible with logistics and space infrastructure.
- **Dashboard** visualizing routes, resources and blockchain transactions.
- **Security** with Kyber-based post-quantum encryption, TLS and optional xAI context integration.
- **Blockchain** layer using lattice-based cryptography and Web3 smart contracts for resource trading.
- **Digital signatures** for authenticated blockchain entries and drone messages.
- **Quantum-secure blockchain** enabling peer-to-peer energy trades with smart contracts and Ethereum compatibility.
- **Simulation** supporting millions of drones in a hybrid Earth/Mars environment.
- **Emergency protocols** trigger return-to-base on low battery or other faults and logs events to `logs/emergency_log.jsonl` for analysis.
- **Self-healing LLM management** with Prometheus health monitoring.
- **MetaLearner RL orchestrator** optimizing prompts across agents.
- **GraphQL API** and extended Quantum Orchestrator for decentralized agent swarms.
- **Prometheus metrics** for LLMs and API endpoints exposed at `/metrics`.
- **Audit logging and key rotation** for API security with data export and deletion endpoints.
- **Role-based access control** with OAuth2 tokens for admin and operator roles.
- **Policy engine** enforcing custom rules on sensitive actions.
- **Self-service portal** for managing API keys.
- **Login and API key metrics** collected via Prometheus.

## Installation

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# Optional extras for advanced features
pip install pettingzoo "dgl" flower web3 openai prometheus_client graphene grpcio
```
For Kafka and MQTT support, start local brokers (see their docs).

Copy `.env.example` to `.env` and adjust the values if you want to override the
default API key or rate limit:

```bash
cp .env.example .env
```

## Quickstart

Start the REST API:

```bash
python start_api.py
```
This convenience script runs `uvicorn drone_fleet.api:FleetAPI.app` with
default settings.

Query an endpoint:

```bash
curl -H "X-API-Key: secret" -H "X-User: demo" http://localhost:8000/status
```
Obtain an admin token:

```bash
curl -X POST -F 'username=admin' -F 'password=admin' http://localhost:8000/token
```
Use the token with endpoints that require admin role:

```bash
curl -H "Authorization: Bearer <token>" -H "X-API-Key: secret" -X POST \
  'http://localhost:8000/admin/rotate_key?old_key=secret'
```
Rotate a key and export usage logs:

```bash
python - <<'PY'
from drone_fleet.api import FleetAPI
api = FleetAPI()
new_key = api.rotate_key("secret")
print("new key", new_key)
print(api.request_logs)
PY
```

Prometheus metrics are available at `http://localhost:8000/metrics`.
Run the demo simulation including blockchain trades:

```bash
python run_simulation.py --drones 1000 --steps 5 --battery-threshold 15
```
The script also trains a small PPO agent using the new Gym environment if the
required packages are installed.

### SuperTool CLI

`supertool.py` provides a single entry point bundling training, simulation,
API and dashboard features. Example usage:

```bash
python supertool.py --train --steps 200
python supertool.py --simulate --drones 500 --nodes 50 --steps 10
python supertool.py --api --dashboard
```

### Self-Service Portal

Admins can manage API keys at runtime:

```bash
curl -H "Authorization: Bearer <token>" -H "X-API-Key: secret" \
     http://localhost:8000/portal/keys
```
Use `POST /portal/keys` to create a key and `DELETE /portal/keys/{key}` to revoke it.

## API Documentation

Run `uvicorn drone_fleet.api:FleetAPI.app` and open `http://localhost:8000/docs`
for Swagger UI. Example endpoints:

* **GET `/status`** – check system status
* **POST `/blockchain/trade`** – record a resource trade
* **POST `/delivery`** – submit a delivery order
* **GET `/metrics`** – Prometheus endpoint exposing runtime metrics
* **GET `/data_export/{tenant}/{user}`** – download usage logs
* **DELETE `/user/{tenant}/{user}`** – erase stored logs for the user

## Monitoring & Alerts

Sample Prometheus alert rule (YAML):

```yaml
- alert: HighErrorRate
  expr: llm_errors_total{tenant="tenant_default"} > 10
  for: 5m
  labels:
    severity: critical
  annotations:
    description: More than 10 LLM errors in 5 minutes
```

Grafana dashboards can visualize request rates and latencies using the metrics
`api_requests_total` and `llm_latency_seconds`. Example dashboards are provided
in `grafana/`. Alerting examples are available in `grafana/alerts.yml`.

## Tests

Install test requirements and run:

```bash
pip install pytest pytest-cov
pytest tests/ --cov=drone_fleet
```

Replay logged emergency events:

```bash
python replay_protocol.py --file logs/emergency_log.jsonl
```

## Troubleshooting

- **API returns 403**: check that `X-API-Key` matches a valid key in `.env`.
- **429 Too Many Requests**: wait for the time in the `Retry-After` header before retrying.
- **Kafka connection errors**: ensure the broker is running on `localhost:9092`.


To start the REST API or dashboard, create appropriate entry points using the
`FleetAPI` and `create_dashboard` functions in the `drone_fleet` package. The
`ResourceNetworkSimulation` class demonstrates how to manage up to millions of drones spanning Earth and Mars with resource trading.

## Chat Service Providers

`CompositeChatService` automatically routes prompts across providers like Grok,
OpenAI, Claude, Perplexity and DeepSeek. Additional providers can be registered
via the `CHATBOT_PLUGIN_PATHS` environment variable. Each path should point to a
Python file exposing a `get_service()` function that returns a chat service
instance.

This Bring‑Your‑Own‑Model mechanism lets you integrate custom or private LLMs
without modifying the core code base. Providers are tried in order with
automatic fallback if one fails.

## Privacy & Data Handling

No personally identifiable information is stored in metrics or logs. All
recorded events use anonymized drone IDs. To remove historical data simply
delete the corresponding JSONL files under `logs/`. API keys can be revoked or
rotated using the `FleetAPI` methods `rotate_key`, `revoke_key` and `add_key`. Request logs per user can be downloaded via `/data_export/{tenant}/{user}` and removed using `/user/{tenant}/{user}`.

## Monetization & Scaling

Possible revenue models include:

1. **Software-as-a-Service (SaaS)** – Host the platform and charge customers per
   active drone or delivery.
2. **Perpetual License** – Sell licenses to logistics companies for on-premise
   deployments.
3. **Consulting and Customization** – Provide tailored features and integration
   services.
4. **Blockchain Tokens** – Issue tokens for automated billing and usage credits.
5. **Usage quotas** – Limit API calls per tenant with billing for overages.

For large fleets, deploy the services in a Kubernetes cluster (e.g. AWS EKS) and
scale Kafka and database layers horizontally. Blockchain nodes can also be
containerized for resilience.

## Disclaimer

This project is intended as a starting point for research and development. It is
not ready for production use without further testing, security auditing, and
performance optimizations.
