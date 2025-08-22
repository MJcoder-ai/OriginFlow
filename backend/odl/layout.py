from typing import Dict, Any, List

def ensure_positions(view: Dict[str, Any]) -> Dict[str, Any]:
    """
    Return a copy of the view where nodes without positions get simple grid positions.
    This does NOT mutate the input dict and does NOT persist to the store.
    """
    nodes: List[Dict[str, Any]] = list(view.get("nodes") or [])
    if not nodes:
        return view

    # Detect if at least one node already has a usable position
    if any(("x" in n or "y" in n or ("pos" in n and isinstance(n["pos"], dict))) for n in nodes):
        return view  # nothing to do

    # Create a shallow copy of the view and nodes to avoid mutating store output
    out = dict(view)
    out_nodes: List[Dict[str, Any]] = []
    out["nodes"] = out_nodes

    # Simple left-to-right grid; spacing large enough for default glyphs
    col_w, row_h, per_row = 220, 160, 8
    for idx, n in enumerate(nodes):
        r, c = divmod(idx, per_row)
        x, y = 80 + c * col_w, 80 + r * row_h
        m = dict(n)
        # Respect existing pos blocks if present but empty-ish
        m.setdefault("pos", {})
        if isinstance(m["pos"], dict):
            m["pos"].setdefault("x", x)
            m["pos"].setdefault("y", y)
        else:
            m["pos"] = {"x": x, "y": y}
        out_nodes.append(m)
    return out
