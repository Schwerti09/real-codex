"""Security features for encrypted communication and emergency protocols."""
from typing import Any

try:
    from pqcrypto.kem import kyber512
except Exception:  # pragma: no cover - optional dependency
    kyber512 = None  # type: ignore

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives.asymmetric import ed25519
except ImportError:  # pragma: no cover
    Fernet = None  # type: ignore
    ed25519 = None  # type: ignore


class CommSecurity:
    """Handles encryption of messages between drones."""

    def __init__(self, key: bytes | None = None):
        if Fernet is None:
            raise ImportError("cryptography is required for encryption")
        self.key = key or Fernet.generate_key()
        self.fernet = Fernet(self.key)
        if kyber512:
            self._pqc_pk, self._pqc_sk = kyber512.generate_keypair()
        else:
            self._pqc_pk = self._pqc_sk = b""
        if ed25519 is not None:
            self._signing_key = ed25519.Ed25519PrivateKey.generate()
            self._verify_key = self._signing_key.public_key()
        else:
            self._signing_key = self._verify_key = None

    def encrypt(self, data: bytes) -> bytes:
        return self.fernet.encrypt(data)

    def decrypt(self, token: bytes) -> bytes:
        return self.fernet.decrypt(token)

    def pqc_encrypt(self, data: bytes) -> tuple[bytes, bytes]:
        """Encrypt using Kyber if available (returns ciphertext, shared key)."""
        if kyber512 is None:
            raise RuntimeError("Kyber library not available")
        ct, ss = kyber512.encrypt(self._pqc_pk)
        # XOR shared secret with data for demo purposes
        return bytes(a ^ b for a, b in zip(data, ss)), ct

    def pqc_decrypt(self, encrypted: bytes, ct: bytes) -> bytes:
        if kyber512 is None:
            raise RuntimeError("Kyber library not available")
        ss = kyber512.decrypt(ct, self._pqc_sk)
        return bytes(a ^ b for a, b in zip(encrypted, ss))

    def sign(self, data: bytes) -> bytes:
        """Sign data using Ed25519 if available."""
        if self._signing_key is None:
            raise RuntimeError("ed25519 not available")
        return self._signing_key.sign(data)

    def verify(self, data: bytes, signature: bytes) -> bool:
        if self._verify_key is None:
            raise RuntimeError("ed25519 not available")
        try:
            self._verify_key.verify(signature, data)
            return True
        except Exception:
            return False


class EmergencyProtocol:
    """Defines emergency behaviors such as return-to-base."""

    def __init__(self, storage_path: str = "logs/emergency_log.jsonl") -> None:
        self.events: list[dict[str, Any]] = []
        self.storage_path = storage_path
        import os
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)

    def execute(self, drone_id: str, reason: str) -> None:
        import json, time

        event = {"drone_id": drone_id, "type": reason, "timestamp": time.time()}
        self.events.append(event)
        with open(self.storage_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")
        print(f"Emergency protocol for {drone_id}: {reason}")
