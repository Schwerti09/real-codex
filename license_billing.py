# -*- coding: utf-8 -*-
"""License and billing module using Stripe."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

try:
    import stripe
except Exception:  # pragma: no cover - optional dependency
    stripe = None


@dataclass
class License:
    key: str
    tenant_id: str
    active: bool


licenses: Dict[str, License] = {}


def create_license(key: str, tenant_id: str) -> None:
    licenses[key] = License(key=key, tenant_id=tenant_id, active=True)


def verify_license(key: str) -> bool:
    lic = licenses.get(key)
    return bool(lic and lic.active)


def create_subscription(customer_id: str, price_id: str) -> str:
    """Create a subscription via Stripe (mock)."""
    if stripe is None:
        return "test-subscription"
    sub = stripe.Subscription.create(customer=customer_id, items=[{"price": price_id}])
    return sub.id


def tokenize_absorption(amount: float) -> str:
    """Return a token representing CO2 absorption."""
    return f"CO2-{amount:.2f}"
