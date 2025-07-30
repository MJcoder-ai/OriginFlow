"""Unit tests for the deterministic rule engine.

These tests verify that the wire sizing calculation behaves as
expected for a variety of inputs.  They use the simple table
implemented in Phase 2 and should be adjusted if that table is
updated.  To run these tests, install ``pytest`` and run

```
pytest -q backend/tests/test_rule_engine.py
```
"""

from backend.services.rule_engine import RuleEngine


def test_size_wire_nominal_case() -> None:
    engine = RuleEngine()
    # 5 kW at 230 V -> current ≈ 21.74 A; with 20 m run the engine
    # should select a 6 mm² conductor based on the default table.
    result = engine.size_wire(load_kw=5.0, distance_m=20.0)
    assert result.gauge == "6 mm²"
    # Current should be approximately 21.74 A
    assert abs(result.current_a - (5.0 * 1000.0 / 230.0)) < 0.1
    # Fuse rating should be 25% above current
    assert abs(result.fuse_rating_a - result.current_a * 1.25) < 0.1
    # Voltage drop should be reasonable (non-negative)
    assert result.voltage_drop_pct >= 0


def test_size_wire_minimum_case() -> None:
    engine = RuleEngine()
    # Very small load and distance should select the smallest conductor.
    result = engine.size_wire(load_kw=0.5, distance_m=5.0)
    assert result.gauge == "2.5\u00a0mm\u00b2"


def test_size_wire_zero_voltage() -> None:
    engine = RuleEngine()
    # Zero voltage should not cause division errors; current and
    # voltage drop should be zero and the largest conductor returned.
    result = engine.size_wire(load_kw=1.0, distance_m=10.0, voltage=0.0)
    # With zero voltage the current is undefined; we expect current_a = 0
    assert result.current_a == 0
    # With zero load the smallest conductor should be selected
    assert result.gauge == "2.5\u00a0mm\u00b2"
