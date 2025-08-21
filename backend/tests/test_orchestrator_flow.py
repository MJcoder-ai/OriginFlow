"""
Phase-4 E2E test: Orchestrator routes a task to a tool and updates ODL.
"""
import sys
from pathlib import Path
import importlib.util

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


def test_orchestrator_generate_wiring_happy_path():
    app = _make_app()
    c = TestClient(app)
    sid = "sess-orch-1"

    # Create session
    assert c.post(f"/odl/sessions?session_id={sid}").status_code == 200
    # Seed graph with inverter + panel on electrical layer
    seed = {
        "patch_id": "seed",
        "operations": [
            {
                "op_id": "seed:n:inv",
                "op": "add_node",
                "value": {
                    "id": "inv1",
                    "type": "inverter",
                    "attrs": {"layer": "electrical"},
                },
            },
            {
                "op_id": "seed:n:p1",
                "op": "add_node",
                "value": {
                    "id": "p1",
                    "type": "panel",
                    "attrs": {"layer": "electrical"},
                },
            },
        ],
    }
    assert c.post(f"/odl/{sid}/patch", headers={"If-Match": "1"}, json=seed).status_code == 200

    # Orchestrate: generate wiring (low risk → auto)
    req = {
        "session_id": sid,
        "task": "generate_wiring",
        "request_id": "r-genwire-1",
        "args": {"layer": "electrical", "edge_kind": "electrical"},
    }
    r = c.post("/ai/act", json=req)
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "complete"
    assert body["output"]["card"]["title"] == "Patch Applied"


def test_make_placeholders_component_type():
    app = _make_app()
    c = TestClient(app)
    sid = "sess-orch-placeholder"

    assert c.post(f"/odl/sessions?session_id={sid}").status_code == 200

    req = {
        "session_id": sid,
        "task": "make_placeholders",
        "request_id": "r-ph-1",
        "args": {"component_type": "panel", "count": 2, "layer": "electrical"},
    }
    r = c.post("/ai/act", json=req)
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "complete"

    view = c.get(f"/odl/{sid}/view?layer=electrical").json()
    assert sum(1 for n in view["nodes"] if n["type"] == "panel") == 2
