from starlette.testclient import TestClient
import math

from backend.main import create_app


def test_get_plan_for_session_happy_path():
    app = create_app()
    c = TestClient(app)

    sid = "sess-plan-1"
    # Create a fresh session; expect version=1
    r = c.post(f"/api/v1/odl/sessions?session_id={sid}")
    assert r.status_code == 200
    assert r.json().get("version") == 1

    # Ask for a plan
    cmd = "design a 5kW solar PV system with 425 W panels"
    r = c.get(f"/api/v1/odl/sessions/{sid}/plan", params={"command": cmd})
    assert r.status_code == 200
    data = r.json()
    assert "tasks" in data and isinstance(data["tasks"], list)

    # Verify the panel task exists and count matches parsed sizing
    panel_task = next(
        t
        for t in data["tasks"]
        if t["id"] == "make_placeholders"
        and t["args"]["component_type"] == "panel"
    )
    assert panel_task["args"]["count"] == math.ceil(5000 / 425)
    assert any(t["id"] == "generate_wiring" for t in data["tasks"])
