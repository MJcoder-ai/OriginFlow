"""
Minimal E2E tests for ODL create/get/patch/view using TestClient.
Adjust imports to your app structure if you have a central FastAPI app instance.
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]))

from fastapi import FastAPI
from fastapi.testclient import TestClient

import importlib.util
spec = importlib.util.spec_from_file_location(
    "odl_routes", Path(__file__).resolve().parents[1] / "api" / "routes" / "odl.py",
)
odl_routes = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(odl_routes)  # type: ignore


def create_app() -> FastAPI:
    app = FastAPI()
    app.include_router(odl_routes.router)
    return app


def test_create_get_patch_view_roundtrip():
    app = create_app()
    c = TestClient(app)
    session_id = "sess-odl-1"

    r = c.post(f"/odl/sessions?session_id={session_id}")
    assert r.status_code == 200
    g = r.json()
    assert g["version"] == 1

    patch = {
        "patch_id": "p-1",
        "operations": [
            {
                "op_id": "op-1",
                "op": "add_node",
                "value": {"id": "n1", "type": "panel", "attrs": {"layer": "single-line"}},
            }
        ],
    }
    r = c.post(f"/odl/{session_id}/patch", headers={"If-Match": "1"}, json=patch)
    assert r.status_code == 200
    env = r.json()
    assert env["status"] == "complete"
    assert env["output"]["card"]["title"] == "Patch Applied"

    r = c.get(f"/odl/{session_id}/view?layer=single-line")
    assert r.status_code == 200
    v = r.json()
    assert v["layer"] == "single-line"
    assert any(n["id"] == "n1" for n in v["nodes"])
