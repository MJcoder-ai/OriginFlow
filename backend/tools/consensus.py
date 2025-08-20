"""
Consensus/ranking tool.

Provides a basic ranking policy over candidates. This is intentionally simple
so a more sophisticated policy can be plugged in later without changing
interfaces.
"""
from __future__ import annotations

from backend.tools.schemas import RankInput, RankResult, ComponentCandidate


def rank_candidates(inp: RankInput) -> RankResult:
    cands = list(inp.candidates)
    if inp.objective == "min_price":
        cands.sort(key=lambda c: (c.price if c.price is not None else float("inf")))
    elif inp.objective == "best_value":
        def value(c: ComponentCandidate):
            s = c.score or 0.0
            p = c.price if c.price and c.price > 0 else 1e9
            return -(s / p)
        cands.sort(key=value)
    else:
        cands.sort(key=lambda c: (c.score or 0.0), reverse=True)
    return RankResult(candidates=cands)
