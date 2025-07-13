"""Simple quantum-secure blockchain using Dilithium signatures."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List
import hashlib
import time

try:
    from web3 import Web3
except Exception:  # pragma: no cover - optional dependency
    Web3 = None  # type: ignore

try:
    from pqcrypto.sign import dilithium2
except Exception:  # pragma: no cover - optional dependency
    dilithium2 = None  # type: ignore


@dataclass
class Block:
    index: int
    timestamp: float
    data: Any
    prev_hash: str
    signature: str | None = None
    hash: str = field(init=False)

    def __post_init__(self) -> None:
        self.hash = hashlib.sha256(
            f"{self.index}{self.timestamp}{self.data}{self.prev_hash}".encode()
        ).hexdigest()


class QuantumBlockchain:
    """Minimal blockchain skeleton with PQ signatures and optional smart contracts."""

    def __init__(self, provider_url: str | None = None) -> None:
        self.chain: List[Block] = [self._create_genesis_block()]
        if dilithium2 is not None:
            self._pk, self._sk = dilithium2.generate_keypair()
        else:
            self._pk = self._sk = b""
        self.w3 = Web3(Web3.HTTPProvider(provider_url)) if provider_url and Web3 else None
        self.contract = None

    def _create_genesis_block(self) -> Block:
        return Block(index=0, timestamp=time.time(), data="genesis", prev_hash="0")

    def add_block(self, data: Any) -> Block:
        prev = self.chain[-1]
        block = Block(index=prev.index + 1, timestamp=time.time(), data=data, prev_hash=prev.hash)
        if dilithium2 is not None:
            block.signature = dilithium2.sign(self._sk, block.hash.encode()).hex()
        self.chain.append(block)
        return block

    def create_trade(self, sender: str, receiver: str, resource: str, amount: float) -> Block:
        contract = {
            "sender": sender,
            "receiver": receiver,
            "resource": resource,
            "amount": amount,
        }
        if self.contract is not None:
            try:
                self.contract.functions.trade(sender, receiver, resource, amount).transact()
            except Exception:  # pragma: no cover - optional
                pass
        return self.add_block({"trade": contract})

    def execute_contract(self, contract: dict) -> Block:
        if self.contract is not None:
            try:
                self.contract.functions.execute(contract).transact()
            except Exception:  # pragma: no cover - optional
                pass
        return self.add_block({"contract": contract})

    def verify_chain(self) -> bool:
        for i in range(1, len(self.chain)):
            prev = self.chain[i - 1]
            curr = self.chain[i]
            if curr.prev_hash != prev.hash:
                return False
            calc_hash = hashlib.sha256(
                f"{curr.index}{curr.timestamp}{curr.data}{curr.prev_hash}".encode()
            ).hexdigest()
            if curr.hash != calc_hash:
                return False
            if dilithium2 is not None and curr.signature is not None:
                try:
                    dilithium2.verify(self._pk, bytes.fromhex(curr.signature), curr.hash.encode())
                except Exception:
                    return False
        return True
