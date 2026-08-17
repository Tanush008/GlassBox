"""Pydantic models shared across the TaskFlow API."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: str
    username: str
    created_at: datetime


class User(UserOut):
    hashed_password: str


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    priority: int = Field(default=1, ge=1, le=5)


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[int] = Field(default=None, ge=1, le=5)
    completed: Optional[bool] = None


class Task(BaseModel):
    id: str
    owner_id: str
    title: str
    description: Optional[str] = None
    priority: int
    completed: bool = False
    created_at: datetime
