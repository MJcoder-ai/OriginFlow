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
