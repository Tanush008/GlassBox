"""TaskFlow API entrypoint - this is the demo app the context engine and
agents operate on. It is intentionally separate from Glassbox's own
FastAPI app in backend/app/main.py."""
from fastapi import FastAPI

from .routers import tasks, users

app = FastAPI(title="TaskFlow API")
app.include_router(users.router)
app.include_router(tasks.router)


@app.get("/health")
def health():
    return {"status": "ok"}
