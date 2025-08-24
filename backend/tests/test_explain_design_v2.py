from backend.tools.explain_design_v2 import explain_design_v2, ExplainDesignV2Input


def test_explain_design_v2_outputs_bullets():
    ds = {
        "env": {"site_tmin_C": -15, "site_tmax_C": 45},
        "counts": {"modules": 24, "inverters": 1},
        "strings": [{"voc_worst_module": 58.0, "max_series_by_system": 12}],
        "derate_defaults": {"temp_factor_90C": 0.87, "grouping_factor_3ccc": 1.0},
    }
    patch = explain_design_v2(
        ExplainDesignV2Input(
            session_id="t",
            request_id="e1",
            design_state=ds,
            audience="non-technical",
        )
    )
    ann = [op for op in patch.operations if op.op == "add_edge"][0]
    bullets = ann.value["attrs"]["bullets"]
    assert any("connects 24 solar modules" in b for b in bullets)
    assert any("checked against electrical code" in b.lower() for b in bullets)

