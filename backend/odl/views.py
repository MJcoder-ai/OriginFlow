from __future__ import annotations

from typing import List
from backend.odl.schemas import ODLGraph, LayerView, ODLNode, ODLEdge


def layer_view(graph: ODLGraph, layer: str) -> LayerView:
    """
    Simple layer projection based on node.attr["layer"] equality.
    If nodes do not have a "layer" attr, the view returns all nodes.
    """
    def _in_layer(n: ODLNode) -> bool:
        lyr = (n.attrs or {}).get("layer")
        return (lyr == layer) if lyr is not None else True  # default include

    nodes = [n for n in graph.nodes.values() if _in_layer(n)]
    node_ids = {n.id for n in nodes}
    edges = [e for e in graph.edges if e.source_id in node_ids and e.target_id in node_ids]
    return LayerView(
        session_id=graph.session_id,
        base_version=graph.version,
        layer=layer,
        nodes=nodes,
        edges=edges,
    )


def electrical_view(graph: ODLGraph) -> LayerView:
    """Example specialized view (can be expanded later)."""
    return layer_view(graph, "electrical")


def structural_view(graph: ODLGraph) -> LayerView:
    """Example specialized view (can be expanded later)."""
    return layer_view(graph, "structural")
