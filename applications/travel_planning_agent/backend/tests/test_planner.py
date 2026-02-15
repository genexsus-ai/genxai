import os

import pytest
from fastapi.testclient import TestClient


if not os.getenv("TRAVEL_PLANNING_DB_PATH"):
    pytest.skip("TRAVEL_PLANNING_DB_PATH not set", allow_module_level=True)

from app.main import create_app


def test_plan_trip_requires_auth() -> None:
    app = create_app()
    client = TestClient(app)

    response = client.post(
        "/api/v1/planner/plan",
        json={
            "session_title": "Weekend Escape",
            "preferences": {
                "origin": "NYC",
                "destination": "Miami",
                "start_date": "2025-05-01",
                "end_date": "2025-05-04",
                "travelers": 2,
                "budget": 1500,
                "interests": ["beach", "food"],
            },
        },
    )
    assert response.status_code == 401
