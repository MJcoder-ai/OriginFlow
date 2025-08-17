"""Tests for the naming policy API endpoints."""

import os
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

# ensure settings load with dummy environment variables
os.environ.setdefault("OPENAI_API_KEY", "test")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test.db")

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))

from backend.config import settings  # noqa: E402

import importlib.util
import types

# Stub out the migration module to avoid importing the entire services package
services_pkg = types.ModuleType("backend.services")
services_pkg.__path__ = []  # type: ignore[attr-defined]
sys.modules["backend.services"] = services_pkg

migration_stub = types.ModuleType("backend.services.component_name_migration")
async def update_existing_component_names(session):
    return None
migration_stub.update_existing_component_names = update_existing_component_names
sys.modules["backend.services.component_name_migration"] = migration_stub

# Provide a minimal deps module with a ``get_session`` dependency
deps_stub = types.ModuleType("backend.api.deps")
async def get_session():
    class DummySession:
        pass
    yield DummySession()
deps_stub.get_session = get_session
sys.modules["backend.api.deps"] = deps_stub

SPEC_PATH = ROOT / "backend" / "api" / "routes" / "naming_policy.py"
spec = importlib.util.spec_from_file_location("naming_policy_routes", SPEC_PATH)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)  # type: ignore[attr-defined]

app = FastAPI()
app.include_router(module.router, prefix="/api/v1")
client = TestClient(app)


def test_get_naming_policy_endpoint() -> None:
    """Fetching the policy returns current settings."""
    resp = client.get("/api/v1/naming-policy/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["template"] == settings.component_name_template
    assert data["version"] == settings.component_naming_version


def test_update_naming_policy_endpoint() -> None:
    """Policy updates modify settings in-memory."""
    original_template = settings.component_name_template
    original_version = settings.component_naming_version
    try:
        payload = {
            "template": "{manufacturer} {part_number}",
            "version": original_version + 1,
            "apply_to_existing": False,
        }
        resp = client.put("/api/v1/naming-policy/", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["template"] == payload["template"]
        assert data["version"] == payload["version"]
        assert settings.component_name_template == payload["template"]
        assert settings.component_naming_version == payload["version"]
    finally:
        settings.component_name_template = original_template
        settings.component_naming_version = original_version
