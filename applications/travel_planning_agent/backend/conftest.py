import os

import pytest


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    db_path = os.getenv("TRAVEL_PLANNING_DB_PATH")
    if db_path:
        return

    skip_marker = pytest.mark.skip(reason="TRAVEL_PLANNING_DB_PATH not set")
    for item in items:
        if item.nodeid.startswith("tests/test_auth.py") or item.nodeid.startswith(
            "tests/test_planner.py"
        ):
            item.add_marker(skip_marker)