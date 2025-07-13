# -*- coding: utf-8 -*-
"""OAuth2 based authentication and RBAC utilities."""
from __future__ import annotations

import secrets
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Callable

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
try:
    from prometheus_client import Counter
except Exception:  # pragma: no cover - optional dependency
    class Counter:  # type: ignore
        def __init__(self, *a, **k):
            pass
        def inc(self, *_args, **_kwargs):
            pass

from .policy import engine as policy_engine

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

login_counter = Counter("login_attempts_total", "Total login attempts")
key_counter = Counter("api_key_usage_total", "API key usage")

@dataclass
class User:
    username: str
    hashed_password: str
    role: str

_users: Dict[str, User] = {}
_tokens: Dict[str, User] = {}
_audit_log = Path("logs/audit.log")


def _log(event: str) -> None:
    _audit_log.parent.mkdir(exist_ok=True)
    with _audit_log.open("a", encoding="utf-8") as f:
        f.write(f"{time.time()}:{event}\n")


def create_user(username: str, password: str, role: str = "user") -> None:
    _users[username] = User(username, pwd_context.hash(password), role)
    _log(f"create_user:{username}:{role}")


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def authenticate(username: str, password: str) -> User | None:
    user = _users.get(username)
    if user and verify_password(password, user.hashed_password):
        return user
    return None


@router.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()) -> Dict[str, str]:
    login_counter.inc()
    user = authenticate(form_data.username, form_data.password)
    if not user:
        _log("login_failed")
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not policy_engine.allowed(user.role, "login"):
        _log(f"login_denied:{user.username}")
        raise HTTPException(status_code=403, detail="Policy denied")
    token = secrets.token_urlsafe(32)
    _tokens[token] = user
    _log(f"login:{user.username}")
    return {"access_token": token, "token_type": "bearer"}


def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    user = _tokens.get(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user


def require_role(role: str) -> Callable[[User], User]:
    def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role != role:
            raise HTTPException(status_code=403, detail="Forbidden")
        return user
    return dependency

# create default admin user for convenience
if not _users:
    create_user("admin", "admin", role="admin")
