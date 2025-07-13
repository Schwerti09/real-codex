# -*- coding: utf-8 -*-
"""Interactive onboarding tutorial module."""

from fastapi import APIRouter

router = APIRouter()

steps = [
    "Welcome to the Codex bioreactor system!",
    "1. Obtain an access token via /token",
    "2. POST sensor data to /optimize",
    "3. View results on the dashboard",
]


@router.get("/tutorial")
def tutorial() -> dict:
    return {"steps": steps}
