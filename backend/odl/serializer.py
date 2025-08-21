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
from typing import Dict, Any, Iterable


def _fmt_attrs(attrs: Dict[str, Any] | None) -> str:
    if not attrs:
        return ""
    # Render a subset of attrs (we keep small, portable keys).
    # Ignore noisy fields (e.g., large blobs) if any are added in future.
    allowed = {
        k: attrs[k]
        for k in sorted(attrs.keys())
        if k in {"layer", "placeholder", "x", "y"}
    }
    if not allowed:
        return ""
    parts = [f"{k}={allowed[k]}" for k in allowed]
    return " [" + " ".join(parts) + "]"


def view_to_odl(view: Dict[str, Any]) -> str:
    nodes: Iterable[Dict[str, Any]] = sorted(
        view.get("nodes") or [],
        key=lambda n: (n.get("type", ""), n.get("id", "")),
    )
    edges: Iterable[Dict[str, Any]] = sorted(
        view.get("edges") or [],
        key=lambda e: (e.get("source", ""), e.get("target", "")),
    )
    lines = ["# ODL (canonical text)"]
    for n in nodes:
        nid = n.get("id", "")
        ntype = n.get("type") or "generic"
        attrs = n.get("attrs") or {}
        lines.append(f"node {nid} : {ntype}{_fmt_attrs(attrs)}")
    for e in edges:
        src = e.get("source", "")
        tgt = e.get("target", "")
        attrs = e.get("attrs") or {}
        lines.append(f"link {src} -> {tgt}{_fmt_attrs(attrs)}")
    return "\n".join(lines) + "\n"
