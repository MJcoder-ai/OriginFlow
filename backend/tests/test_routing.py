from backend.tools.routing import (
    plan_routes,
    PlanRoutesInput,
    BundleRef,
    Pose,
    Waypoint,
)


def test_plan_routes_with_poses_and_waypoint():
    inp = PlanRoutesInput(
        session_id="s",
        request_id="r",
        bundles=[
            BundleRef(
                id="B-1", source_id="A", target_id="C", system="ac_1ph_3w", attrs={}
            )
        ],
        node_poses={"A": Pose(x=0, y=0), "C": Pose(x=3, y=4)},
        waypoints={"B-1": [Waypoint(id="B", pose=Pose(x=0, y=4))]},
    )
    patch = plan_routes(inp)
    segs = [
        op
        for op in patch.operations
        if op.op == "set_meta" and op.value["path"] == "physical.routes"
    ][0].value["data"][0]["segments"]
    # A->B length 4, B->C length 3 → total 7
    assert abs(sum(s["len_m"] for s in segs) - 7.0) < 1e-6


def test_plan_routes_fallback_length():
    inp = PlanRoutesInput(
        session_id="s",
        request_id="r2",
        bundles=[
            BundleRef(
                id="B-2", source_id="X", target_id="Y", system="dc_pv", attrs={}
            )
        ],
        default_length_m=5.0,
    )
    patch = plan_routes(inp)
    segs = [
        op
        for op in patch.operations
        if op.op == "set_meta" and op.value["path"] == "physical.routes"
    ][0].value["data"][0]["segments"]
    assert segs[0]["len_m"] == 5.0

