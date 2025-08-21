"""
Phase-6 E2E test: review-required flow → propose → approve → ODL updated.
"""
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.routes.odl import router as odl_router
from backend.api.routes.ai import router as ai_router
from backend.api.routes.approvals import router as approvals_router
from backend.db.session import get_db, SessionLocal


def _get_db():
    with SessionLocal() as db:
        yield db


def _make_app():
    app = FastAPI()
    app.include_router(odl_router)
    app.include_router(ai_router)
    app.include_router(approvals_router)
    app.dependency_overrides[get_db] = _get_db
    return app


def test_review_required_replace_placeholders_approval_flow():
    app = _make_app()
    c = TestClient(app)
    sid = "sess-approve-1"

    # Create session + seed with one generic panel
    assert c.post(f"/odl/sessions?session_id={sid}").status_code == 200
    seed = {
        "patch_id": "seed",
        "operations": [
            {"op_id": "seed:n:inv", "op": "add_node", "value": {"id": "inv1", "type": "inverter", "attrs": {"layer": "electrical"}}},
            {"op_id": "seed:n:gp1", "op": "add_node", "value": {"id": "gp1", "type": "generic_panel", "attrs": {"layer": "electrical", "placeholder": True}}},
        ],
    }
    assert c.post(f"/odl/{sid}/patch", headers={"If-Match": "1"}, json=seed).status_code == 200

    # Ask orchestrator to replace placeholders (review_required)
    req = {
        "session_id": sid,
        "task": "replace_placeholders",
        "request_id": "r-rpl-1",
        "args": {"layer": "electrical", "placeholder_type": "generic_panel", "pool": [
            {"part_number": "P-400", "name": "Panel 400", "manufacturer": "ACME", "category": "panel", "power": 400, "price": 200}
        ], "requirements": {"target_power": 350}}
    }
    r = c.post("/ai/act", json=req)
    env = r.json()
    assert env["status"] == "pending"
    proposed = env["output"]["card"]["actions"][0]["payload"]

    # Submit approval proposal
    apr = {
        "approval_id": "apr-1",
        "session_id": sid,
        "task": "replace_placeholders",
        "request_id": "r-rpl-1",
        "patch_json": proposed
    }
    assert c.post("/approvals/propose", json=apr).status_code == 200

    # Approve → should apply patch and increment version
    d = {"decision": "approve"}
    r = c.post("/approvals/apr-1/decision", json=d)
    assert r.status_code == 200
    body = r.json()
    assert body["record"]["status"] == "approved"
    assert body["applied_version"] == 3
