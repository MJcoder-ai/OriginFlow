from backend.tools.labels import generate_labels, GenerateLabelsInput


def node(id, t):
    return {"id": id, "type": t}


def edge(id, kind, attrs):
    return {"id": id, "kind": kind, "attrs": attrs}


def test_generate_labels_basic():
    nodes = [
        node("MAIN", "service_panel_200A"),
        node("INV", "string_inverter"),
        node("ACDISC", "ac_disconnect"),
        node("RSD", "mlpe_rsd"),
    ]
    edges = [
        edge(
            "e1",
            "bundle",
            {"connection": "dc_pv", "conductors": [{"function": "PV+", "size": "10AWG"}]},
        ),
        edge(
            "e2",
            "bundle",
            {"connection": "ac_1ph_3w", "conductors": [{"function": "L1", "size": "10AWG"}]},
        ),
    ]
    patch = generate_labels(
        GenerateLabelsInput(
            session_id="s", request_id="r", view_nodes=nodes, view_edges=edges
        )
    )
    setmeta = [op for op in patch.operations if op.op == "set_meta"][0]
    assert setmeta.value["path"] == "physical.labels"
    ann = [op for op in patch.operations if op.op == "add_edge"][0]
    assert "labels/placards" in ann.value["attrs"]["summary"]

