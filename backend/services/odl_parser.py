from __future__ import annotations
"""Parser converting ODL text into a :class:`DesignSnapshot`.

This utility reads the simplified ODL format produced by the existing
``odl_compiler``.  Only a subset of the language is supported but it covers
the structures currently emitted: layer declarations, component positions and
link routes.  The parser is deliberately forgiving – unknown lines are
ignored to allow forward compatibility.
"""

import re
from typing import List, Dict, Optional

from backend.schemas.analysis import DesignSnapshot, Link, CanvasComponent

RE_LAYER = re.compile(r"^\s*#\s*Layer:\s*(\w+)\s*$")
RE_NODE = re.compile(r'^\s*(\w+)\s+([A-Za-z0-9_\-]+)(?:\s+at\(layer="([^"]+)",\s*x=(\-?\d+),\s*y=(\-?\d+)\))?\s*$')
RE_LINK = re.compile(r'^\s*link\s+([A-Za-z0-9_\-]+)\s*->\s*([A-Za-z0-9_\-]+)(?:\s+route\[\s*(.+?)\s*\])?\s*$')
RE_PT = re.compile(r'\(\s*(\-?\d+)\s*,\s*(\-?\d+)\s*\)')


def parse_odl_text(text: str) -> DesignSnapshot:
    layer = "single_line"
    comps: Dict[str, CanvasComponent] = {}
    links: List[Link] = []

    for raw in text.splitlines():
        m = RE_LAYER.match(raw)
        if m:
            layer = m.group(1)
            continue
        n = RE_NODE.match(raw)
        if n:
            typ, name_or_id, lay, xs, ys = n.groups()
            cid = name_or_id
            comp = comps.get(cid) or CanvasComponent(id=cid, name=cid, type=typ, x=0, y=0)
            if lay and xs and ys:
                comp.layout = {**(comp.layout or {}), lay: {"x": float(xs), "y": float(ys)}}
            comps[cid] = comp
            continue
        e = RE_LINK.match(raw)
        if e:
            s, t, rest = e.groups()
            link = Link(id=f"{s}_{t}", source_id=s, target_id=t, path_by_layer={}, locked_in_layers={})
            if rest:
                pts = [{"x": float(x), "y": float(y)} for (x, y) in RE_PT.findall(rest)]
                if pts:
                    link.path_by_layer[layer] = pts
            links.append(link)
            continue

    return DesignSnapshot(components=list(comps.values()), links=links)


__all__ = ["parse_odl_text"]

