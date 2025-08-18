from __future__ import annotations
"""Compile design snapshots into ODL text representation."""

from typing import List

from backend.schemas.analysis import DesignSnapshot


LAYERS = [
    "single_line",
    "high_level",
    "civil",
    "networking",
    "physical",
]


def snapshot_to_odl(snapshot: DesignSnapshot, layers: List[str] | None = None) -> str:
    """Return an ODL text document describing ``snapshot``.

    When link waypoints are available they are emitted using ``route[(x,y) -> ...]``.
    """

    layers = layers or LAYERS
    lines: List[str] = ["# OriginFlow ODL Design"]
    for layer in layers:
        lines.append(f"# Layer: {layer}")
        for c in snapshot.components:
            pos = (c.layout or {}).get(layer)
            if pos:
                x = pos.get("x")
                y = pos.get("y")
                lines.append(
                    f"{c.type} {c.name or c.id} at(layer=\"{layer}\", x={int(x)}, y={int(y)})"
                )
            else:
                lines.append(f"{c.type} {c.name or c.id}")
        for l in snapshot.links:
            pts = (l.path_by_layer or {}).get(layer, [])
            if pts:
                coords = " -> ".join(f"({int(p['x'])},{int(p['y'])})" for p in pts)
                lines.append(
                    f"link {l.source_id} -> {l.target_id} route[{coords}]"
                )
            else:
                lines.append(f"link {l.source_id} -> {l.target_id}")
        lines.append("")
    return "\n".join(lines)


__all__ = ["snapshot_to_odl"]

