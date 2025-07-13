"""IoT sensor integration for the drone fleet."""
from typing import Any


class SensorManager:
    """Collects and distributes sensor data via Apache Kafka or MQTT."""

    def __init__(self, broker_url: str):
        self.broker_url = broker_url
        # Placeholder for MQTT/Kafka/Flink client initialization
        self.client = None
        self.topics: dict[str, list[Any]] = {}
        self.grpc_channel = None

    def publish_state(self, topic: str, payload: Any) -> None:
        """Publish sensor data to a topic."""
        self.topics.setdefault(topic, []).append(payload)

    def subscribe(self, topic: str) -> None:
        """Subscribe to a sensor topic."""
        self.topics.setdefault(topic, [])

    def stream_to_flink(self, topic: str, payload: Any) -> None:
        """Placeholder for streaming data to Apache Flink."""
        _ = (topic, payload)

    def send_grpc(self, message: bytes) -> None:
        """Placeholder for sending a gRPC message."""
        _ = message

    def get_latest(self, topic: str) -> Any:
        data = self.topics.get(topic, [])
        return data[-1] if data else None
