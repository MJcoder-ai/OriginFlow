"""
Round-trip tests for Phase-3 tools.

Tools operate on in-memory ODL graphs and produce deterministic patches that
can be applied via the Phase-2 patch logic.
"""
from __future__ import annotations

from backend.odl.schemas import ODLGraph, ODLNode
from backend.odl.patches import apply_patch
from backend.tools.schemas import (
    GenerateWiringInput,
    GenerateMountsInput,
    AddMonitoringInput,
    MakePlaceholdersInput,
)
from backend.tools import wiring, structural, monitoring, placeholders


def test_tools_generate_and_apply_patches():
    g = ODLGraph(
        session_id="sess-tools-1",
        version=1,
        nodes={
            "inv1": ODLNode(id="inv1", type="inverter", attrs={"layer": "electrical"}),
            "p1": ODLNode(id="p1", type="panel", attrs={"layer": "electrical"}),
            "p2": ODLNode(id="p2", type="panel", attrs={"layer": "electrical"}),
        },
        edges=[],
        meta={},
    )
    applied = {}

    # Wiring
    w_patch = wiring.generate_wiring(
        GenerateWiringInput(
            session_id=g.session_id,
            request_id="r1",
            view_nodes=list(g.nodes.values()),
            edge_kind="electrical",
        )
    )
    g, applied = apply_patch(g, w_patch, applied)
    assert len(g.edges) == 2

    # Structural mounts
    s_patch = structural.generate_mounts(
        GenerateMountsInput(
            session_id=g.session_id,
            request_id="r2",
            view_nodes=list(g.nodes.values()),
            layer="structural",
        )
    )
    g, applied = apply_patch(g, s_patch, applied)
    assert any(n.type == "mount" for n in g.nodes.values())

    # Monitoring device
    m_patch = monitoring.add_monitoring_device(
        AddMonitoringInput(
            session_id=g.session_id,
            request_id="r3",
            view_nodes=list(g.nodes.values()),
            layer="electrical",
        )
    )
    g, applied = apply_patch(g, m_patch, applied)
    assert any(n.type == "monitoring" for n in g.nodes.values())

    # Placeholders
    ph_patch = placeholders.make_placeholders(
        MakePlaceholdersInput(
            session_id=g.session_id,
            request_id="r4",
            count=2,
            placeholder_type="generic_panel",
            attrs={"layer": "electrical"},
        )
    )
    g, applied = apply_patch(g, ph_patch, applied)
    assert sum(1 for n in g.nodes.values() if n.type == "generic_panel") == 2
