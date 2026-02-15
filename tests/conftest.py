"""Global test configuration."""

import os
import warnings

import pytest


warnings.filterwarnings(
    "ignore",
    category=ResourceWarning,
    message=r"unclosed database in <sqlite3\.Connection",
)


#@pytest.fixture(autouse=True)
#def reset_audit_services(tmp_path, monkeypatch):
#    """Reset audit services before each test to ensure isolation."""
#    from enterprise.genxai.security.audit import reset_audit_services

#    db_path = tmp_path / "audit.db"
#    monkeypatch.setenv("GENXAI_AUDIT_DB", str(db_path))
#    reset_audit_services()
#    yield
#    reset_audit_services()


#@pytest.fixture(autouse=True)
#def reset_policy_engine():
#    """Reset policy engine state before each test to avoid rule leakage."""
#    from enterprise.genxai.security import policy_engine

#    policy_engine._policy_engine = None
#    yield
#    policy_engine._policy_engine = None
