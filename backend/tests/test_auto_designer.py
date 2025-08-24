from backend.orchestrator.plan_spec import PlanSpec, Env, Targets
from backend.orchestrator.auto_designer import run_auto_design


def test_auto_design_simulates_end_to_end():
    spec = PlanSpec(env=Env(site_tmin_C=-10, site_tmax_C=45), targets=Targets(dc_kw_stc=3.0))
    patch = run_auto_design(spec, session_id="s", request_id="ad1", simulate=True)
    ops = patch.operations
    # must include annotations and set_meta for schedules/bom
    assert any(op.op == "set_meta" and op.value.get("path") == "physical.schedules" for op in ops)
    assert any(op.op == "set_meta" and op.value.get("path") == "physical.bom" for op in ops)
    assert any(op.op == "add_edge" and op.value["id"].startswith("ann:") for op in ops)


def test_auto_design_materializes_nodes():
    spec = PlanSpec(env=Env(site_tmin_C=-10, site_tmax_C=45), targets=Targets(dc_kw_stc=3.0))
    patch = run_auto_design(spec, session_id="s", request_id="ad2", simulate=False)
    ops = patch.operations
    assert any(op.op == "add_node" and op.value["type"] == "string_inverter" for op in ops)
    assert sum(1 for op in ops if op.op == "add_node" and op.value["type"] == "pv_module") >= 8

