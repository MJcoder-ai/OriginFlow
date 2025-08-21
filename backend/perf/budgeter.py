"""
Token/cost budgeter (Phase 9).

This is a lightweight, model-agnostic estimator that projects the "size" of an
incoming /ai/act request based on the ODL view slice and tool args, and enforces
guardrails before we call any LLMs or long-running tools.

In production you can replace the estimator with actual tokenizer calls and a
live cost table. Here we keep it simple and deterministic.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, Literal
import json

BudgetDecision = Literal["allow", "warn", "block"]


@dataclass
class BudgetPolicy:
    # Soft/hard limits per act request
    max_chars_soft: int = 30_000     # warn if exceeded
    max_chars_hard: int = 120_000    # block if exceeded
    max_nodes_soft: int = 400        # warn if exceeded
    max_nodes_hard: int = 2_000      # block if exceeded


def _sizeof(obj: Any) -> int:
    """Rough size via JSON serialization (bytes == chars for ASCII)."""
    try:
        return len(json.dumps(obj, ensure_ascii=True, separators=(",", ":")))
    except Exception:
        return 0


def estimate_chars(view_nodes: list[Dict[str, Any]] | None, args: Dict[str, Any] | None) -> int:
    nbytes = 0
    nbytes += _sizeof(view_nodes or [])
    nbytes += _sizeof(args or {})
    return nbytes


def budget_check(
    *,
    policy: BudgetPolicy,
    view_nodes_count: int,
    estimated_chars: int,
) -> tuple[BudgetDecision, list[str]]:
    """
    Decide whether to allow, warn or block the act based on cheap signals.
    Returns (decision, warnings).
    """
    warns: list[str] = []
    if view_nodes_count > policy.max_nodes_hard or estimated_chars > policy.max_chars_hard:
        return "block", [f"Request too large: nodes={view_nodes_count}, size={estimated_chars} chars"]
    if view_nodes_count > policy.max_nodes_soft:
        warns.append(f"Large view: {view_nodes_count} nodes")
    if estimated_chars > policy.max_chars_soft:
        warns.append(f"Large payload: ~{estimated_chars} chars")
    if warns:
        return "warn", warns
    return "allow", []
