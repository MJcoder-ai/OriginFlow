"""Utility functions for evaluating domain rules and constraints."""
from __future__ import annotations

from typing import Any, Dict, List


def evaluate_constraints(
    constraints: Dict[str, Any],
    inputs: Dict[str, Any],
    result: Dict[str, Any],
) -> List[str]:
    """Evaluate constraint expressions against inputs and results.

    ``constraints`` is expected to be a mapping from rule identifiers to
    dictionaries containing at least an ``expression`` key.  Expressions
    are evaluated in a restricted namespace using only the provided
    ``inputs`` and ``result`` dictionaries.  Returns a list of human
    readable validation messages for any violated constraints or
    evaluation errors.
    """
    validations: List[str] = []
    if not constraints:
        return validations
    local_vars = {**inputs, **result}
    for rule_id, rule in constraints.items():
        expr = rule.get("expression")
        if not expr:
            continue
        try:
            # Evaluate expression in a restricted namespace.  No builtins
            # or globals are exposed; only local_vars are available.
            passed = bool(eval(expr, {}, local_vars))
        except NameError as exc:
            # Skip constraints with undefined variables and note that
            # evaluation could not proceed, rather than flagging a violation.
            validations.append(
                f"Constraint {rule_id} cannot be evaluated: undefined variable {exc}"
            )
            continue
        except Exception as exc:
            validations.append(f"Constraint {rule_id} evaluation error: {exc}")
            continue
        if not passed:
            description = rule.get("description", expr)
            validations.append(f"Constraint {rule_id} violated: {description}")
    return validations
