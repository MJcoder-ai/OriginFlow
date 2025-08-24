from backend.tools.schedules import generate_schedules, GenerateSchedulesInput

SESSION = "test"


def edge(id, kind, src="a", tgt="b", attrs=None):
    return {
        "id": id,
        "kind": kind,
        "source_id": src,
        "target_id": tgt,
        "attrs": attrs or {},
    }


def test_generate_schedules_from_bundles():
    edges = [
        edge(
            "bundle:a:b:ac_3ph_4w",
            "bundle",
            "INV1",
            "ACB1",
            {
                "connection": "ac_3ph_4w",
                "conductors": [
                    {"function": "L1", "size": "4AWG"},
                    {"function": "L2", "size": "4AWG"},
                    {"function": "L3", "size": "4AWG"},
                    {"function": "N", "size": "4AWG"},
                    {"function": "PE", "size": "6AWG"},
                ],
                "accessories": [{"type": "glands", "qty": 2}],
            },
        )
    ]
    routes = [
        {
            "bundle_id": "bundle:a:b:ac_3ph_4w",
            "segments": [
                {"from": "INV1", "to": "ACB1", "env": "indoor", "len_m": 12.3}
            ],
        }
    ]
    patch = generate_schedules(
        GenerateSchedulesInput(
            session_id=SESSION,
            request_id="sch1",
            view_edges=edges,
            routes=routes,
        )
    )
    setmeta = [op for op in patch.operations if op.op == "set_meta"][0]
    assert setmeta.value["path"] == "physical.schedules"
    ann = [op for op in patch.operations if op.op == "add_edge"][0]
    assert "cable(s)" in ann.value["attrs"]["summary"]
    sch = setmeta.value["data"]
    assert abs(sch["cables"][0]["length_m"] - 12.3) < 1e-6

