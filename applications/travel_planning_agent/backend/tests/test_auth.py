import os

import pytest
from fastapi.testclient import TestClient


if not os.getenv("TRAVEL_PLANNING_DB_PATH"):
    pytest.skip("TRAVEL_PLANNING_DB_PATH not set", allow_module_level=True)

from app.main import create_app


def test_register_and_login() -> None:
    app = create_app()
    client = TestClient(app)

    response = client.post("/api/v1/auth/register", json={"username": "demo", "password": "secret123"})
    assert response.status_code == 200
    token = response.json()["access_token"]
    assert token

    login = client.post("/api/v1/auth/login", json={"username": "demo", "password": "secret123"})
    assert login.status_code == 200
