# -*- coding: utf-8 -*-
"""User and rights management using OAuth2 and roles.

This example provides a minimal multi-tenant user management system with
role-based access control. It exposes endpoints to obtain OAuth2 tokens and
an admin panel listing all registered users. Passwords are hashed and stored
in-memory for simplicity. In production you would use a persistent database
and proper JWTs.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from typing import Dict

from cryptography.fernet import Fernet

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext


@dataclass
class User:
    """Represents a user account."""

    username: str
    hashed_password: str
    role: str
    tenant_id: str


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
users: Dict[str, User] = {}
router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
active_tokens: Dict[str, str] = {}
fernet = Fernet(Fernet.generate_key())


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


@router.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = users.get(form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = secrets.token_urlsafe(32)
    secure_token = fernet.encrypt(token.encode()).decode()
    active_tokens[secure_token] = user.username
    return {"access_token": secure_token, "token_type": "bearer"}


def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    try:
        fernet.decrypt(token.encode())
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    username = active_tokens.get(token)
    if not username:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = users.get(username)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user


@router.get("/admin")
def admin_panel(user: User = Depends(get_current_user)):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Forbidden")
    return {"users": list(users.keys())}


def create_demo_user(username: str, password: str, role: str, tenant_id: str):
    users[username] = User(
        username=username,
        hashed_password=get_password_hash(password),
        role=role,
        tenant_id=tenant_id,
    )


# Create a default admin user for testing
create_demo_user("admin", "admin", "admin", tenant_id="default")
