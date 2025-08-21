"""
Phase-7 test: domain registry influences placeholder→category mapping and risk override.
"""
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

# Ensure project root is on sys.path
sys.path.append(str(Path(__file__).resolve().parents[2]))

from backend.api.routes.odl import router as odl_router
from backend.api.routes.ai import router as ai_router
from backend.db.session import get_db, SessionLocal


def _get_db():
    with SessionLocal() as db:
        yield db


def _make_app():
    app = FastAPI()
    app.include_router(odl_router)
    app.include_router(ai_router)
    app.dependency_overrides[get_db] = _get_db
    return app


def test_replace_placeholders_uses_domain_mapping_and_review():
    app = _make_app()
    c = TestClient(app)
    sid = "sess-domain-1"
    # Create session with domain meta = PV
    assert c.post(f"/odl/sessions?session_id={sid}").status_code == 200
    seed = {
        "patch_id": "seed",
        "operations": [
            {"op_id": "seed:meta", "op": "set_meta", "value": {"domain": "PV"}},
            {"op_id": "seed:n:gp1", "op": "add_node", "value": {"id": "gp1", "type": "generic_panel", "attrs": {"layer": "electrical", "placeholder": True}}},
        ],
    }
    assert c.post(f"/odl/{sid}/patch", headers={"If-Match": "1"}, json=seed).status_code == 200

    # Trigger replacement with no explicit categories → domain should map generic_panel → panel categories
    req = {
        "session_id": sid,
        "task": "replace_placeholders",
        "request_id": "r-rpl-domain",
        "args": {
            "layer": "electrical",
            "placeholder_type": "generic_panel",
            "pool": [{"part_number": "P-400", "name": "Panel 400", "manufacturer": "ACME", "category": "panel", "power": 400, "price": 200}]
        }
    }
    r = c.post("/ai/act", json=req)
    assert r.status_code == 200
    env = r.json()
    # Domain risk override for replace_placeholders is 'medium' → review_required → pending
    assert env["status"] == "pending"
