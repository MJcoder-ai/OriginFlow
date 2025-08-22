"""Utility functions for evaluating domain rules and constraints."""
from __future__ import annotations

import ast
import operator
from typing import Any, Dict, List


# Safe operators for expression evaluation
SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
    ast.And: lambda x, y: x and y,
    ast.Or: lambda x, y: x or y,
    ast.Not: operator.not_,
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def _safe_eval(expr: str, variables: Dict[str, Any]) -> Any:
    """Safely evaluate mathematical and comparison expressions.
    
    This function uses AST parsing to safely evaluate expressions containing
    only mathematical operations, comparisons, and variable references.
    It prevents code injection by restricting the allowed operations.
    """
    try:
        tree = ast.parse(expr, mode='eval')
        return _eval_node(tree.body, variables)
    except (SyntaxError, ValueError, TypeError) as e:
        raise ValueError(f"Invalid expression: {e}")


def _eval_node(node: ast.AST, variables: Dict[str, Any]) -> Any:
    """Recursively evaluate AST nodes safely."""
    if isinstance(node, ast.Name):
        if node.id in variables:
            return variables[node.id]
        raise NameError(f"Variable '{node.id}' not found")
    
    elif isinstance(node, ast.Constant):
        return node.value
    
    elif isinstance(node, ast.Num):  # For Python < 3.8 compatibility
        return node.n
    
    elif isinstance(node, ast.Str):  # For Python < 3.8 compatibility
        return node.s
    
    elif isinstance(node, ast.BinOp):
        left = _eval_node(node.left, variables)
        right = _eval_node(node.right, variables)
        op_func = SAFE_OPERATORS.get(type(node.op))
        if op_func is None:
            raise ValueError(f"Unsupported binary operator: {type(node.op).__name__}")
        return op_func(left, right)
    
    elif isinstance(node, ast.UnaryOp):
        operand = _eval_node(node.operand, variables)
        op_func = SAFE_OPERATORS.get(type(node.op))
        if op_func is None:
            raise ValueError(f"Unsupported unary operator: {type(node.op).__name__}")
        return op_func(operand)
    
    elif isinstance(node, ast.Compare):
        left = _eval_node(node.left, variables)
        for op, comparator in zip(node.ops, node.comparators):
            right = _eval_node(comparator, variables)
            op_func = SAFE_OPERATORS.get(type(op))
            if op_func is None:
                raise ValueError(f"Unsupported comparison operator: {type(op).__name__}")
            if not op_func(left, right):
                return False
            left = right  # For chained comparisons
        return True
    
    elif isinstance(node, ast.BoolOp):
        values = [_eval_node(value, variables) for value in node.values]
        op_func = SAFE_OPERATORS.get(type(node.op))
        if op_func is None:
            raise ValueError(f"Unsupported boolean operator: {type(node.op).__name__}")
        
        if isinstance(node.op, ast.And):
            return all(values)
        elif isinstance(node.op, ast.Or):
            return any(values)
    
    else:
        raise ValueError(f"Unsupported expression type: {type(node).__name__}")


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
            # Use safe expression evaluation instead of eval()
            passed = bool(_safe_eval(expr, local_vars))
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
