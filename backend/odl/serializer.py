"""
ODL text serializer
-------------------
Converts a view (nodes/edges on a layer) into a stable, line-oriented ODL text.
Format (canonical, minimal):
  node <id> : <type> [k1=v1 k2=v2 ...]        # attrs optional
  link <source> -> <target> [k1=v1 k2=v2 ...]  # attrs optional

Notes:
- IDs and types are emitted as-is; attributes are rendered in a stable key
  order.
- This is intentionally simple so it's easy to diff and copy/paste.
"""
from __future__ import annotations
from typing import Dict, Any, Iterable, Iterator


def _fmt_attrs(attrs: Dict[str, Any] | None) -> str:
    if not attrs:
        return ""
    # Render important component attributes that provide engineering value.
    # Include component specifications, ratings, and identification.
    component_attrs = {
        # Component identification
        "part_number", "name", "manufacturer", "model", "type",
        # Electrical specifications
        "power", "rating_A", "voltage_rating_V", "voc", "vmp", "imp", "isc", 
        "ac_kw", "vdc_max", "mppt_vmin", "mppt_vmax", "mppts",
        # Mechanical/physical
        "layer", "application", "location",
        # Layout (minimal for position tracking)
        "x", "y", "placeholder"
    }
    
    # Filter to important attributes only
    allowed = {
        k: attrs[k]
        for k in sorted(attrs.keys())
        if k in component_attrs and attrs[k] is not None
    }
    
    if not allowed:
        return ""
    
    # Format key-value pairs with proper handling of different types
    parts = []
    for k in allowed:
        v = allowed[k]
        if isinstance(v, str) and (" " in v or "-" in v):
            # Quote strings with spaces or hyphens for readability
            parts.append(f'{k}="{v}"')
        else:
            parts.append(f"{k}={v}")
    
    return " [" + " ".join(parts) + "]"


def _iter_nodes(nodes: Iterable[Any] | None) -> Iterator[Dict[str, Any]]:
    """Yield dict-like nodes, skipping anything malformed."""
    for n in nodes or []:
        if isinstance(n, dict):
            yield n


def _iter_edges(edges: Iterable[Any] | None) -> Iterator[Dict[str, Any]]:
    """Yield dict-like edges, skipping anything malformed."""
    for e in edges or []:
        if isinstance(e, dict):
            yield e


def view_to_odl(view: Dict[str, Any]) -> str:
    nodes: Iterable[Dict[str, Any]] = sorted(
        _iter_nodes(view.get("nodes")),
        key=lambda n: (str(n.get("type") or ""), str(n.get("id") or "")),
    )
    edges: Iterable[Dict[str, Any]] = sorted(
        _iter_edges(view.get("edges")),
        key=lambda e: (str(e.get("source_id") or ""), str(e.get("target_id") or "")),
    )
    lines = ["# ODL (canonical text)"]
    for n in nodes:
        nid = n.get("id", "")
        ntype = n.get("type") or "generic"
        attrs = n.get("attrs") if isinstance(n.get("attrs"), dict) else {}
        lines.append(f"node {nid} : {ntype}{_fmt_attrs(attrs)}")
    for e in edges:
        src = e.get("source_id", "")
        tgt = e.get("target_id", "")
        attrs = e.get("attrs") if isinstance(e.get("attrs"), dict) else {}
        lines.append(f"link {src} -> {tgt}{_fmt_attrs(attrs)}")
    return "\n".join(lines) + "\n"
