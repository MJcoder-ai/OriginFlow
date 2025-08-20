import sys
from pathlib import Path
import importlib.util

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parents[2]))

spec_odl = importlib.util.spec_from_file_location(
    "backend.api.routes.odl", Path(__file__).resolve().parents[1] / "api" / "routes" / "odl.py",
)
odl_routes = importlib.util.module_from_spec(spec_odl)
assert spec_odl.loader is not None
sys.modules["backend.api.routes.odl"] = odl_routes
spec_odl.loader.exec_module(odl_routes)  # type: ignore

spec_ai = importlib.util.spec_from_file_location(
    "backend.api.routes.ai", Path(__file__).resolve().parents[1] / "api" / "routes" / "ai.py",
)
ai_routes = importlib.util.module_from_spec(spec_ai)
assert spec_ai.loader is not None
sys.modules["backend.api.routes.ai"] = ai_routes
spec_ai.loader.exec_module(ai_routes)  # type: ignore


def _make_app() -> FastAPI:
    app = FastAPI()
    app.include_router(odl_routes.router)
    app.include_router(ai_routes.router)
    return app


def test_ai_act_body():
    app = _make_app()
    client = TestClient(app)
    sid = "act-test"
    assert client.post(f"/odl/sessions?session_id={sid}").status_code == 200
    resp = client.post(
        "/ai/act",
        json={
            "session_id": sid,
            "task": "generate_wiring",
            "request_id": "r1",
            "args": {"layer": "electrical", "edge_kind": "electrical"},
        },
    )
    assert resp.status_code == 200
