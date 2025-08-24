"""Small math helpers used by tools."""
from __future__ import annotations
from typing import Iterable, Tuple
import math


def loglog_interp(points: Iterable[Tuple[float, float]], x: float) -> float:
    """Log–log interpolate y at x given sequence of (x, y) points.
    Clamps to end-points for out-of-range x.
    """
    pts = sorted(points, key=lambda p: p[0])
    if not pts:
        raise ValueError("points must be non-empty")
    if x <= pts[0][0]:
        return pts[0][1]
    if x >= pts[-1][0]:
        return pts[-1][1]
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        if x1 <= x <= x2:
            lx1, lx2 = math.log10(x1), math.log10(x2)
            ly1, ly2 = math.log10(y1), math.log10(y2)
            t = (math.log10(x) - lx1) / (lx2 - lx1)
            return 10 ** (ly1 + t * (ly2 - ly1))
    return pts[-1][1]
