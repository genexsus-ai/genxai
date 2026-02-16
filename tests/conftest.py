"""Global test configuration."""

import importlib.util
import os
import sys
import types
import warnings
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
ENTERPRISE_SRC = ROOT_DIR / "genxai_enterprise"
ENTERPRISE_CLI_SRC = ROOT_DIR / "cli"

HAS_ENTERPRISE = bool(importlib.util.find_spec("genxai_enterprise")) or ENTERPRISE_SRC.exists()

if HAS_ENTERPRISE:
    if ENTERPRISE_SRC.exists() and str(ENTERPRISE_SRC) not in sys.path:
        sys.path.insert(0, str(ENTERPRISE_SRC))
    if ENTERPRISE_CLI_SRC.exists() and str(ENTERPRISE_CLI_SRC) not in sys.path:
        sys.path.insert(0, str(ENTERPRISE_CLI_SRC))

    enterprise_module = types.ModuleType("enterprise")
    genxai_module = types.ModuleType("enterprise.genxai")
    cli_module = types.ModuleType("enterprise.cli")
    genxai_module.__path__ = [str(ENTERPRISE_SRC)]
    cli_module.__path__ = [str(ENTERPRISE_CLI_SRC)]
    enterprise_module.genxai = genxai_module
    enterprise_module.cli = cli_module
    sys.modules.setdefault("enterprise", enterprise_module)
    sys.modules.setdefault("enterprise.genxai", genxai_module)
    sys.modules.setdefault("enterprise.cli", cli_module)

    from enterprise.genxai.security import policy_engine as enterprise_policy_engine
    from enterprise.genxai.security import rbac as enterprise_rbac

    sys.modules["genxai.security.policy_engine"] = enterprise_policy_engine
    sys.modules["genxai.security.rbac"] = enterprise_rbac


warnings.filterwarnings(
    "ignore",
    category=ResourceWarning,
    message=r"unclosed database in <sqlite3\.Connection",
)


@pytest.fixture(autouse=True)
def reset_audit_services(tmp_path, monkeypatch):
    """Reset audit services before each test to ensure isolation."""
    if not HAS_ENTERPRISE:
        yield
        return

    from enterprise.genxai.security.audit import reset_audit_services

    db_path = tmp_path / "audit.db"
    monkeypatch.setenv("GENXAI_AUDIT_DB", str(db_path))
    reset_audit_services()
    yield
    reset_audit_services()


@pytest.fixture(autouse=True)
def reset_policy_engine():
    """Reset policy engine state before each test to avoid rule leakage."""
    if not HAS_ENTERPRISE:
        yield
        return

    from enterprise.genxai.security import policy_engine

    policy_engine._policy_engine = None
    yield
    policy_engine._policy_engine = None


def pytest_ignore_collect(collection_path, config):
    """Skip enterprise-only tests when enterprise package is unavailable."""
    if HAS_ENTERPRISE:
        return False

    if collection_path.suffix != ".py":
        return False

    try:
        content = collection_path.read_text(encoding="utf-8")
    except Exception:
        return False

    return any(
        marker in content
        for marker in ("genxai_enterprise", "enterprise.genxai", "enterprise.cli")
    )
