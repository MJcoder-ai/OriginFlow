import os
import sys
from pathlib import Path
from uuid import uuid4

import asyncio

from fastapi.testclient import TestClient

# ensure settings load with dummy env vars
os.environ.setdefault("OPENAI_API_KEY", "test")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test.db")

sys.path.append(str(Path(__file__).resolve().parents[2]))

import importlib.util

from fastapi import FastAPI

from backend.services import odl_graph_service  # noqa: E402


spec = importlib.util.spec_from_file_location(
    "requirements_routes",
    Path(__file__).resolve().parents[1] / "api" / "routes" / "requirements.py",
)
requirements_routes = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(requirements_routes)  # type: ignore[attr-defined]

app = FastAPI()
app.include_router(requirements_routes.router, prefix="/api/v1")
client = TestClient(app)


def test_update_requirements_accepts_empty_graph():
    """Empty graphs should be treated as valid sessions."""
    session_id = f"req-{uuid4()}"
    asyncio.run(odl_graph_service.create_graph(session_id))

    resp = client.post(
        f"/api/v1/requirements/{session_id}",
        json={"target_power": 5000},
    )
    assert resp.status_code == 200

    graph = asyncio.run(odl_graph_service.get_graph(session_id))
    assert graph.graph["requirements"]["target_power"] == 5000


def test_update_requirements_missing_session():
    """Unknown sessions return 404."""
    resp = client.post(
        "/api/v1/requirements/does-not-exist",
        json={"target_power": 5000},
    )
    assert resp.status_code == 404
