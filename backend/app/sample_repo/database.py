"""A tiny in-memory "database" so the demo repo has no external
dependencies. Two dicts, keyed by id."""
from typing import Dict

from .models import Task, User

users_by_id: Dict[str, User] = {}
users_by_username: Dict[str, str] = {}  # username -> id
tasks_by_id: Dict[str, Task] = {}


def reset():
    """Used by tests to get a clean slate between runs."""
    users_by_id.clear()
    users_by_username.clear()
    tasks_by_id.clear()
