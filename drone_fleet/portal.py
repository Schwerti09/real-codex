# -*- coding: utf-8 -*-
"""Self-service portal for managing API keys."""
from __future__ import annotations

from typing import Dict
from fastapi import APIRouter, Depends
from .auth import require_role
from .api import FleetAPI

router = APIRouter()
portal_api: FleetAPI | None = None


def init(api: FleetAPI) -> None:
    global portal_api
    portal_api = api


@router.get("/portal/keys")
def list_keys(user=Depends(require_role("admin"))):
    if portal_api is None:
        return {"keys": []}
    return {"keys": list(portal_api.api_keys.keys())}


@router.post("/portal/keys")
def create_key(user=Depends(require_role("admin"))):
    if portal_api is None:
        return {"error": "api not set"}
    base = next(iter(portal_api.api_keys))
    new_key = portal_api.rotate_key(base)
    return {"new_key": new_key}


@router.delete("/portal/keys/{key}")
def revoke_key(key: str, user=Depends(require_role("admin"))):
    if portal_api is None:
        return {"error": "api not set"}
    portal_api.revoke_key(key)
    return {"revoked": key}
