from backend.tools.nl.parse_plan_spec import parse_plan_spec, NLToPlanSpecInput
from backend.orchestrator.auto_designer import auto_design_from_nl


def test_parse_plan_spec_3kw_defaults():
    res = parse_plan_spec(
        NLToPlanSpecInput(session_id="s", request_id="r", utterance="design a 3kW solar PV system")
    )
    spec = res["spec"]
    assert abs(spec["targets"]["dc_kw_stc"] - 3.0) < 1e-6
    # Ensure the spec is persisted to meta
    assert any(op.value.get("path") == "design_state.plan_spec" for op in res["patch"].operations)


def test_auto_design_from_nl_simulate_flow():
    patch = auto_design_from_nl("design a 3 kW pv system", session_id="s", request_id="ad:nl", simulate=True)
    ops = patch.operations
    # Should include annotations from plan + design; and schedules meta
    assert any(op.op == "set_meta" and op.value.get("path") == "design_state.plan_spec" for op in ops)
    assert any(op.op == "set_meta" and op.value.get("path") == "physical.schedules" for op in ops)
    # No physical nodes when simulate=True
    assert not any(op.op == "add_node" for op in ops)
