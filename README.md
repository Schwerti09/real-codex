# Real Codex

[![CI](https://github.com/example/real-codex/actions/workflows/ci.yml/badge.svg)](https://github.com/example/real-codex/actions/workflows/ci.yml)

Ein Prototyp-Kontrollsystem fuer Algenbioreaktor-Netzwerke zur CO₂-Sequestrierung und weitere Demoanwendungen wie quantensichere Drohnen- und interplanetare Logistik. Zentrale Module sind:

- `bioreactor_optimization.py` – Einzelreaktor-Optimierung mit MQTT und FastAPI.
- `bioreactor_network_optimization.py` – Multi-Agent-RL auf Basis eines Transformer-Modells, Kafka-Streaming, Blockchain-Logging und Dash-Dashboard.
- `quantum_logistics_network.py` – Drohnen-Logistik mit quantensicherer Blockchain und Transformer-RL.
- `interplanetary_logistics_network.py` – Ressourcenmanagement zwischen Erde und Mars mit Transformer-RL.

Die Systeme verwenden optional Post-Quantum-Kryptografie (z.B. Kyber via `pqcrypto`) um Transaktionen abzusichern.

| Feature                | Modul                            | Paket             |
|------------------------|----------------------------------|-------------------|
| Einzelreaktor-API      | `bioreactor_optimization.py`     | `fastapi`         |
| Netzwerkoptimierung    | `bioreactor_network_optimization.py` | `stable-baselines3` |
| Drohnenlogistik        | `quantum_logistics_network.py`   | `transformers`    |
| Interplanetare Logistik| `interplanetary_logistics_network.py` | `pqcrypto`        |

## Systemvoraussetzungen
- **Python**: 3.11
- Abhaengigkeiten laut `requirements.txt`
- Kafka- und MQTT-Broker fuer Echtzeit-Betrieb

## Installation
1. Python-Abhaengigkeiten installieren:
   ```bash
   ./setup.sh
   ```
   *(Optional)* `pqcrypto` und `stable-baselines3` werden nur fuer die Post-Quantum- bzw. RL-Funktionen benoetigt und koennen auf Plattformen ohne Binaerpakete ausgelassen werden.
2. Kafka-Broker starten:
   ```bash
   zookeeper-server-start.sh config/zookeeper.properties
   kafka-server-start.sh config/server.properties
   ```
3. MQTT-Broker starten:
   ```bash
   mosquitto -c /etc/mosquitto/mosquitto.conf
   ```

## Quickstart
```bash
./setup.sh
pytest -q
```
Kopiere `examples/plugins/dummy_plugin.py` als Vorlage fuer eigene Plug-ins und
lade sie mit `CHATBOT_PLUGIN_PATHS`.

## Nutzung
Start des Netzwerkoptimierers im Simulationsmodus:
```bash
python bioreactor_network_optimization.py --simulate
```
API Beispielaufruf:
```bash
curl -X POST http://localhost:8000/optimize \
     -H 'Content-Type: application/json' \
     -H 'Authorization: Bearer secret-token' \
     -d '[{"reactor_id": "r1", "light": 120.0, "temperature": 26.0, "co2": 0.03, "nutrients": 1.2, "ph": 7.5}]'
```
Dashboard unter `http://localhost:8000/dashboard/`.

### Training
Optionales RL-Training kann mit [Stable-Baselines3](https://github.com/DLR-RM/stable-baselines3) ausgefuehrt werden:
```bash
python -c "from bioreactor_network_optimization import optimizer; optimizer.train(1000)"
```

## API Documentation
Swagger-UI steht unter `/docs` bereit. Wichtige Endpunkte:
- **POST `/optimize`** – Optimiert Reaktorparameter.
- **GET `/health`** – Statuspruefung.
- **GET `/anomalies`** – Liefert Anomalien und Prognose.

## Tests
```bash
source .venv/bin/activate
pytest -q
```

## Skalierung & Deployment
Containerisierung via `Dockerfile`, Kubernetes-Konfiguration in `k8s/` inklusive HorizontalPodAutoscaler.

## Monetarisierung
Moegliche Modelle sind SaaS-Abos, Handel von CO₂-Zertifikaten und Beratungsdienstleistungen.

## Chatbot Provider
Das Projekt enthaelt eine modulare Chat-Orchestrierung.  
Ueber die Umgebungsvariable `CHATBOT_PROVIDERS` kann die Reihenfolge der
LLM-Anbieter (Grok, OpenAI, Claude, Perplexity, DeepSeek) festgelegt werden.
Eigene Chat-Dienste koennen per `CHATBOT_PLUGIN_PATHS` eingebunden werden und
werden automatisch als Fallback genutzt.

### Plug-in Entwicklung
Plug-ins muessen eine Funktion `get_chat_service()` bereitstellen und duerfen
keine unbehandelten Exceptions werfen. Fehler werden separat geloggt. Eine
Beispielimplementierung befindet sich in `examples/plugins/dummy_plugin.py`.

## License
MIT License.

## Disclaimer
Proof of Concept zu Demonstrationszwecken.

Weitere Details siehe [docs/BLUEPRINT.md](docs/BLUEPRINT.md).
