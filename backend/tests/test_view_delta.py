"""
Phase-8 test: view_delta reports changes only when version increases.
"""
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

# Ensure project root is on sys.path
sys.path.append(str(Path(__file__).resolve().parents[2]))

from backend.api.routes.odl import router as odl_router
from backend.db.session import get_db, SessionLocal


def _get_db():
    with SessionLocal() as db:
        yield db


def _make_app():
    app = FastAPI()
    app.include_router(odl_router)
    app.dependency_overrides[get_db] = _get_db
    return app


def test_view_delta_roundtrip():
    app = _make_app()
    c = TestClient(app)
    sid = "sess-delta-1"
    assert c.post(f"/odl/sessions?session_id={sid}").status_code == 200
    head = c.get(f"/odl/{sid}/head").json()
    v0 = head["version"]

    # First delta: no changes yet
    d = c.get(f"/odl/{sid}/view_delta?since={v0}&layer=single-line").json()
    assert d["changed"] is False
    assert d["version"] == v0

    # Apply a simple node add
    patch = {
        "patch_id": "p1",
        "operations": [
            {"op_id": "op1", "op": "add_node", "value": {"id": "n1", "type": "panel", "attrs": {"layer": "single-line"}}}
        ]
    }
    assert c.post(f"/odl/{sid}/patch", headers={"If-Match": str(v0)}, json=patch).status_code == 200

    # Delta should now include the view
    head2 = c.get(f"/odl/{sid}/head").json()
    v1 = head2["version"]
    d2 = c.get(f"/odl/{sid}/view_delta?since={v0}&layer=single-line").json()
    assert d2["changed"] is True
    assert d2["version"] == v1
    assert any(n["id"] == "n1" for n in d2["view"]["nodes"])
