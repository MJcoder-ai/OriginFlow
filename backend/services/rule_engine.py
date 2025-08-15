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
        if voltage > 0 and current_a > 0:
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

    # ------------------------------------------------------------------
    # New validation logic for installed conductor and fuse.

    @dataclass
    class WireValidation:
        """Result of validating an existing conductor and protection device.

        This class summarises how a chosen wire gauge and fuse compare to
        recommended values for a given load and distance.  It contains
        both the installed and recommended parameters along with boolean
        flags indicating compliance with cross‑section, fuse rating and
        voltage drop limits.
        """

        installed_gauge: str
        installed_cross_section_mm2: float
        installed_fuse_rating_a: float
        recommended_gauge: str
        recommended_cross_section_mm2: float
        recommended_fuse_rating_a: float
        current_a: float
        voltage_drop_pct: float
        is_cross_section_compliant: bool
        is_fuse_rating_compliant: bool
        is_voltage_drop_within_limit: bool

    def validate_wire(
        self,
        *,
        installed_cross_section_mm2: float,
        installed_fuse_rating_a: float,
        load_kw: float,
        distance_m: float,
        voltage: float = 230.0,
        installed_gauge: str | None = None,
        max_voltage_drop_pct: float = 5.0,
    ) -> "RuleEngine.WireValidation":
        """Validate an existing wire and fuse against recommended sizing rules.

        The validation uses ``size_wire`` to compute the recommended
        cross‑section and fuse rating based on the specified load, distance
        and voltage.  It then compares the installed wire and fuse to
        these values, determines the voltage drop of the installed
        conductor and returns a ``WireValidation`` result describing
        compliance.
        """

        # Compute recommended conductor size and fuse rating.
        rec = self.size_wire(load_kw, distance_m, voltage)

        # Determine the installed gauge label if not provided.
        gauge_label = installed_gauge or f"{installed_cross_section_mm2:.0f}\u00a0mm\u00b2"

        # Calculate voltage drop for the installed conductor.
        current_a = rec.current_a
        if installed_cross_section_mm2 > 0 and voltage > 0 and current_a > 0:
            resistivity = 0.0175  # Ohm·mm²/m for copper
            resistance = (resistivity * distance_m) / installed_cross_section_mm2
            actual_v_drop = current_a * resistance * 2
            actual_v_drop_pct = (actual_v_drop / voltage) * 100.0
        else:
            actual_v_drop_pct = 0.0

        # Determine conductor ampacity from the wire table.
        conductor_ampacity = rec.current_a
        for max_current, label, area in self._WIRE_TABLE:
            conductor_ampacity = max_current
            if installed_cross_section_mm2 <= area:
                break

        # Evaluate compliance criteria.
        is_cross_section_ok = installed_cross_section_mm2 >= rec.cross_section_mm2
        min_fuse = rec.fuse_rating_a
        max_fuse = conductor_ampacity * 1.5
        is_fuse_ok = (installed_fuse_rating_a >= min_fuse) and (
            installed_fuse_rating_a <= max_fuse
        )
        is_v_drop_ok = actual_v_drop_pct <= max_voltage_drop_pct

        return self.WireValidation(
            installed_gauge=gauge_label,
            installed_cross_section_mm2=installed_cross_section_mm2,
            installed_fuse_rating_a=installed_fuse_rating_a,
            recommended_gauge=rec.gauge,
            recommended_cross_section_mm2=rec.cross_section_mm2,
            recommended_fuse_rating_a=rec.fuse_rating_a,
            current_a=rec.current_a,
            voltage_drop_pct=actual_v_drop_pct,
            is_cross_section_compliant=is_cross_section_ok,
            is_fuse_rating_compliant=is_fuse_ok,
            is_voltage_drop_within_limit=is_v_drop_ok,
        )


default_rule_engine = RuleEngine()
