# TaskFlow API

A tiny task-management REST API used as the demo repository inside Glassbox.
It exists purely so the context engine and agents have something real to
reason about - swap this folder for any Python repo you want to point
Glassbox at.

## Layout

- `main.py` - FastAPI app entrypoint, mounts the routers.
- `database.py` - in-memory "database" (a couple of dicts) and a fake session.
- `models.py` - Pydantic models for User and Task.
- `auth.py` - signup / login / password hashing helpers.
- `utils.py` - small shared helpers (id generation, pagination).
- `routers/tasks.py` - CRUD endpoints for tasks.
- `routers/users.py` - signup/login endpoints.
- `tests/test_routes.py` - a handful of endpoint tests.
