"""
Eval harness (Phase 9).

Runs a set of scenarios and returns a JSON-able report. This is not a test
framework replacement; it's a lightweight, reproducible QA tool to run in CI
or locally before releases.
"""
from __future__ import annotations

from typing import List, Dict

from backend.evals.scenarios import pv_wiring, placeholder_replace_review


def run_all() -> Dict:
    scenarios = [
        pv_wiring,
        placeholder_replace_review,
    ]
    results: List[Dict] = []
    for sc in scenarios:
        try:
            results.append(sc.run())
        except Exception as exc:
            results.append({"name": sc.__name__, "passed": False, "error": str(exc)})
    summary = {
        "total": len(results),
        "passed": sum(1 for r in results if r.get("passed")),
        "failed": [r for r in results if not r.get("passed")],
        "results": results,
    }
    return summary
