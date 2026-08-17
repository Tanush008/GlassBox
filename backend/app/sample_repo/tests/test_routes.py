"""A handful of endpoint tests for TaskFlow, run with pytest + httpx."""
import pytest
from fastapi.testclient import TestClient

from .. import database
from ..main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def _reset_db():
    database.reset()
    yield
    database.reset()


def test_signup_and_login():
    r = client.post("/users/signup", json={"username": "ada", "password": "supersecret"})
    assert r.status_code == 200
    assert r.json()["username"] == "ada"

    r = client.post("/users/login", json={"username": "ada", "password": "supersecret"})
    assert r.status_code == 200


def test_signup_rejects_short_password():
    r = client.post("/users/signup", json={"username": "ada", "password": "short"})
    assert r.status_code == 400


def test_create_and_list_tasks():
    signup = client.post("/users/signup", json={"username": "grace", "password": "supersecret"})
    owner_id = signup.json()["id"]

    r = client.post("/tasks", params={"owner_id": owner_id}, json={"title": "Write COBOL"})
    assert r.status_code == 200

    r = client.get("/tasks", params={"owner_id": owner_id})
    assert r.status_code == 200
    assert len(r.json()) == 1
