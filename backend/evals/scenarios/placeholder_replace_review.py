"""
Eval scenario: placeholder → real replacement (review-required).
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.routes.odl import router as odl_router
from backend.api.routes.ai import router as ai_router
from backend.api.routes.approvals import router as approvals_router
from backend.db.session import get_db, SessionLocal


def _get_db():
    with SessionLocal() as db:
        yield db


def build_app() -> FastAPI:
    app = FastAPI()
    app.include_router(odl_router)
    app.include_router(ai_router)
    app.include_router(approvals_router)
    app.dependency_overrides[get_db] = _get_db
    return app


def run() -> dict:
    app = build_app()
    c = TestClient(app)
    sid = "eval-replace-1"
    steps = []

    # Create + seed
    steps.append(("create_session", c.post(f"/odl/sessions?session_id={sid}").status_code == 200))
    seed = {
        "patch_id": "seed",
        "operations": [
            {"op_id": "seed:meta", "op": "set_meta", "value": {"domain": "PV"}},
            {"op_id": "seed:n:gp",  "op": "add_node", "value": {"id": "gp", "type": "generic_panel", "attrs": {"layer": "electrical", "placeholder": True}}},
        ],
    }
    steps.append(("seed", c.post(f"/odl/{sid}/patch", headers={"If-Match": "1"}, json=seed).status_code == 200))

    # Ask orchestrator to replace (review required)
    req = {
        "session_id": sid,
        "task": "replace_placeholders",
        "request_id": "r-eval2",
        "args": {
            "layer": "electrical",
            "placeholder_type": "generic_panel",
            "pool": [{"part_number": "P-425", "name": "ACME 425W", "manufacturer": "ACME", "category": "panel", "power": 425, "price": 210}],
            "requirements": {"target_power": 400}
        }
    }
    r = c.post("/ai/act", json=req)
    env = r.json()
    steps.append(("orchestrator_pending", env["status"] == "pending"))

    # Propose the patch
    proposed = env["output"]["card"]["actions"][0]["payload"]
    p = {
        "approval_id": "apr-eval2",
        "session_id": sid,
        "task": "replace_placeholders",
        "request_id": "r-eval2",
        "patch_json": proposed,
    }
    steps.append(("propose", c.post("/approvals/propose", json=p).status_code == 200))

    # Approve and check version advanced
    r2 = c.post("/approvals/apr-eval2/decision", json={"decision": "approve"})
    ok = r2.status_code == 200 and r2.json()["record"]["status"] == "approved"
    steps.append(("approve", ok))
    head = c.get(f"/odl/{sid}/head").json()
    steps.append(("head_advanced", head["version"] >= 3))

    passed = all(flag for _, flag in steps)
    return {"name": "placeholder_replace_review", "steps": steps, "passed": passed, "final_version": head["version"]}
