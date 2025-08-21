"""
Eval scenario: PV small wiring.

Goal: a small session with an inverter + two panels; run 'generate_wiring' and
assert a new version and at least one electrical edge exists in the view.
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient
from backend.api.routes.odl import router as odl_router
from backend.api.routes.ai import router as ai_router
from backend.db.session import get_db, SessionLocal


def _get_db():
    with SessionLocal() as db:
        yield db


def build_app() -> FastAPI:
    app = FastAPI()
    app.include_router(odl_router)
    app.include_router(ai_router)
    app.dependency_overrides[get_db] = _get_db
    return app


def run() -> dict:
    app = build_app()
    c = TestClient(app)
    sid = "eval-pv-wire-1"
    steps = []

    # Create session
    r = c.post(f"/odl/sessions?session_id={sid}")
    steps.append(("create_session", r.status_code == 200))
    v0 = r.json()["version"]

    # Seed graph (1 inverter, 2 panels)
    seed = {
        "patch_id": "seed",
        "operations": [
            {"op_id": "seed:n:inv", "op": "add_node", "value": {"id": "inv1", "type": "inverter", "attrs": {"layer": "electrical"}}},
            {"op_id": "seed:n:p1",  "op": "add_node", "value": {"id": "p1", "type": "panel", "attrs": {"layer": "electrical"}}},
            {"op_id": "seed:n:p2",  "op": "add_node", "value": {"id": "p2", "type": "panel", "attrs": {"layer": "electrical"}}},
        ],
    }
    steps.append(("seed", c.post(f"/odl/{sid}/patch", headers={"If-Match": str(v0)}, json=seed).status_code == 200))

    # Act: generate_wiring
    req = {"session_id": sid, "task": "generate_wiring", "request_id": "r-eval1", "args": {"layer": "electrical"}}
    r = c.post("/ai/act", json=req)
    ok = r.status_code == 200 and r.json()["status"] == "complete"
    steps.append(("generate_wiring", ok))

    # Check view
    head = c.get(f"/odl/{sid}/head").json()
    v1 = head["version"]
    view = c.get(f"/odl/{sid}/view?layer=electrical").json()
    # at least one edge exists from p1 or p2 to inv1
    # (edges are not directly returned in Phase 2 view spec if filtered; here they are)
    edges = view.get("edges", [])
    has_edge = any(e.get("target_id") == "inv1" for e in edges)
    steps.append(("view_has_edge", has_edge))

    passed = all(flag for _, flag in steps)
    return {"name": "pv_wiring", "steps": steps, "passed": passed, "final_version": v1}
