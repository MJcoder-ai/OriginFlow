"""
Unit tests for budgeter decisions.
"""
from backend.perf.budgeter import BudgetPolicy, budget_check


def test_budget_allow():
    pol = BudgetPolicy(max_chars_soft=1000, max_chars_hard=5000, max_nodes_soft=10, max_nodes_hard=100)
    d, warns = budget_check(policy=pol, view_nodes_count=5, estimated_chars=800)
    assert d == "allow"
    assert not warns


def test_budget_warn_and_block():
    pol = BudgetPolicy(max_chars_soft=1000, max_chars_hard=5000, max_nodes_soft=10, max_nodes_hard=100)
    d, warns = budget_check(policy=pol, view_nodes_count=15, estimated_chars=1200)
    assert d == "warn" and len(warns) >= 1

    d2, warns2 = budget_check(policy=pol, view_nodes_count=150, estimated_chars=6000)
    assert d2 == "block"
