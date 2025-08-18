from backend.schemas.analysis import DesignSnapshot, Link, CanvasComponent
from backend.services.wiring import plan_missing_wiring


def test_plan_missing_wiring_idempotent():
    p = CanvasComponent(id="P1", name="P1", type="panel", x=0, y=0, layout={"single_line": {"x": 100, "y": 100}}, locked_in_layers={"single_line": True})
    i = CanvasComponent(id="I1", name="I1", type="inverter", x=0, y=0, layout={"single_line": {"x": 400, "y": 100}}, locked_in_layers={"single_line": True})
    snap = DesignSnapshot(components=[p, i], links=[])
    plan1 = plan_missing_wiring(snap)
    assert ("P1", "I1") in plan1
    snap.links = [Link(id="L1", source_id="P1", target_id="I1", path_by_layer={}, locked_in_layers={})]
    plan2 = plan_missing_wiring(snap)
    assert ("P1", "I1") not in plan2

