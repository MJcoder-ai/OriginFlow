"""Deterministic rule engine for safety-critical sizing calculations.

The rule engine encapsulates deterministic formulas and lookup tables for
engineering design.  In Phase\u00a02 we implement a simple wire-sizing
calculator based on load (kilowatts), distance (metres) and nominal
voltage.  Future expansions will include pipe and duct sizing for
water pumping and HVAC domains.

This module deliberately avoids using AI models; all calculations are
transparent and verifiable against published standards.  If you need to
extend the sizing tables, consider adding new methods or loading data
from external CSV files.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class WireSizingResult:
    """Result of a wire sizing calculation."""

    gauge: str
    cross_section_mm2: float
    fuse_rating_a: float
    current_a: float
    voltage_drop_pct: float


class RuleEngine:
    """Deterministic engine for sizing wires and other components."""

    _WIRE_TABLE = [
        (10.0, "2.5\u00a0mm\u00b2", 2.5),
        (20.0, "4\u00a0mm\u00b2", 4.0),
        (32.0, "6\u00a0mm\u00b2", 6.0),
        (45.0, "10\u00a0mm\u00b2", 10.0),
        (65.0, "16\u00a0mm\u00b2", 16.0),
        (85.0, "25\u00a0mm\u00b2", 25.0),
    ]

    def size_wire(self, load_kw: float, distance_m: float, voltage: float = 230.0) -> WireSizingResult:
        """Compute an appropriate wire size for a given load and distance."""
        current_a = (load_kw * 1000.0) / voltage if voltage > 0 else 0.0
        cross_section = 25.0
        gauge = "25\u00a0mm\u00b2"
        for max_current, label, area in self._WIRE_TABLE:
            if current_a <= max_current:
                gauge = label
                cross_section = area
                break
        resistivity = 0.0175
        resistance = (resistivity * distance_m) / cross_section
        v_drop = current_a * resistance * 2
        voltage_drop_pct = (v_drop / voltage) * 100.0 if voltage > 0 else 0.0
        fuse_rating = current_a * 1.25
        return WireSizingResult(
            gauge=gauge,
            cross_section_mm2=cross_section,
            fuse_rating_a=fuse_rating,
            current_a=current_a,
            voltage_drop_pct=voltage_drop_pct,
        )


default_rule_engine = RuleEngine()
