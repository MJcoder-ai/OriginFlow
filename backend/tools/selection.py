"""
Component selection tool.

Pure, in-memory candidate ranking based on a provided pool. No DB access.
"""
from __future__ import annotations

from typing import List
from backend.tools.schemas import SelectionInput, SelectionResult, ComponentCandidate


def find_components(inp: SelectionInput) -> SelectionResult:
    """
    Rank components from the given pool against requirements. A simple heuristic:
    - Prefer components that meet or exceed target power (if present)
    - Secondary sort by lower price
    - Tertiary sort by manufacturer preference (if any future prefs exist)
    """
    pool: List[ComponentCandidate] = []
    target_power = float(inp.requirements.get("target_power", 0) or 0)

    for raw in inp.pool:
        cand = ComponentCandidate(
            part_number=str(raw.get("part_number") or raw.get("pn") or ""),
            name=str(raw.get("name") or ""),
            manufacturer=raw.get("manufacturer"),
            category=raw.get("category"),
            power=float(raw.get("power") or 0) if raw.get("power") is not None else None,
            price=float(raw.get("price") or 0) if raw.get("price") is not None else None,
        )
        score = 0.0
        if cand.power is not None:
            if target_power > 0:
                if cand.power >= target_power:
                    score += 1.0
                score += min(cand.power / max(target_power, 1e-9), 2.0) * 0.25
            else:
                score += 0.1
        if cand.price is not None:
            score += max(0.0, 1.0 - min(cand.price / 1000.0, 1.0)) * 0.3
        cand.score = round(score, 4)
        pool.append(cand)

    pool.sort(key=lambda c: (c.score or 0.0, -(c.power or 0.0)), reverse=True)
    return SelectionResult(candidates=pool)
