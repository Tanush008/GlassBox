"""Signup / login endpoints."""
from fastapi import APIRouter

from .. import auth
from ..models import UserCreate, UserOut

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/signup", response_model=UserOut)
def signup(payload: UserCreate):
    user = auth.signup(payload)
    return user


@router.post("/login", response_model=UserOut)
def login(payload: UserCreate):
    user = auth.login(payload.username, payload.password)
    return user
