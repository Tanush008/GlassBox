"""Signup / login helpers.

Deliberately simple (sha256, no email field yet) so that a request like
"add email validation to signup" has an obvious, real place to land.
"""
import hashlib
from datetime import datetime

from fastapi import HTTPException, status

from . import database
from .models import User, UserCreate
from .utils import new_id


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def signup(payload: UserCreate) -> User:
    if payload.username in database.users_by_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken.",
        )
    if len(payload.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters.",
        )

    user = User(
        id=new_id(),
        username=payload.username,
        created_at=datetime.utcnow(),
        hashed_password=_hash_password(payload.password),
    )
    database.users_by_id[user.id] = user
    database.users_by_username[user.username] = user.id
    return user


def login(username: str, password: str) -> User:
    user_id = database.users_by_username.get(username)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials.")
    user = database.users_by_id[user_id]
    if user.hashed_password != _hash_password(password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials.")
    return user
