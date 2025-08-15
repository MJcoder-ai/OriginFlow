"""Deterministic rule engine for electrical, conduit and structural sizing.

This module defines simple deterministic functions for sizing electrical
conductors, protective devices (fuses), conduits and structural mounts, as
well as validation helpers to check installed components against recommended
standards.  It deliberately avoids any AI/ML models, instead relying on
published tables, empirical formulas and basic physics.

The initial implementation covers:

* **Wire sizing** – compute gauge, cross\u2011section and fuse ratings for a given
  load and distance, and validate installed wires and fuses.
* **Conduit sizing** – calculate the required conduit cross\u2011section and
  diameter based on the total cross\u2011section of conductors and a fill factor,
  and validate installed conduits against recommended fill ratios.
* **Structural mount sizing** – estimate required load capacity for mounting
  structures based on the number of panels, panel weight and wind load
  factors, and validate installed mounts against these requirements.

Future expansions may include pipe/duct sizing for plumbing, battery pack
configuration, lightning protection and other deterministic engineering checks.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List


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

    # ------------------------------------------------------------------
    # Conduit sizing and validation

    @dataclass
    class ConduitSizingResult:
        """Result of sizing a conduit for a set of conductors."""

        num_conductors: int
        total_cross_section_mm2: float
        recommended_conduit_cross_section_mm2: float
        recommended_conduit_diameter_mm: float

    @dataclass
    class ConduitValidation:
        """Result of validating an existing conduit against recommended sizing."""

        installed_conduit_cross_section_mm2: float
        installed_conduit_diameter_mm: float
        recommended_conduit_cross_section_mm2: float
        recommended_conduit_diameter_mm: float
        fill_ratio: float
        is_conduit_size_compliant: bool

    def size_conduit(
        self,
        *,
        cross_sections_mm2: List[float],
        fill_factor: float = 0.4,
    ) -> "RuleEngine.ConduitSizingResult":
        """Compute recommended conduit size based on conductor cross-sections.

        Conduit sizing follows typical electrical code requirements where the
        sum of conductor areas must not exceed a certain percentage of the
        conduit’s internal area (fill factor).  Given a list of conductor
        cross-section areas (in mm²), this function calculates the total area,
        divides by the fill factor to obtain the minimum conduit cross-section,
        and converts that area to an approximate circular diameter.

        Args:
            cross_sections_mm2: List of cross-sectional areas for each conductor.
            fill_factor: Maximum allowable fill ratio (default 40%).

        Returns:
            A ``ConduitSizingResult`` with the recommended cross-section and
            diameter.
        """
        import math

        total_area = sum(cross_sections_mm2)
        if total_area <= 0.0:
            # Avoid division by zero; recommend a nominal 20 mm conduit.
            return self.ConduitSizingResult(
                num_conductors=len(cross_sections_mm2),
                total_cross_section_mm2=0.0,
                recommended_conduit_cross_section_mm2=100.0,
                recommended_conduit_diameter_mm=20.0,
            )
        recommended_area = total_area / fill_factor
        # area = π * (d/2)^2 → d = 2 * sqrt(area/π)
        recommended_diameter = 2.0 * math.sqrt(recommended_area / math.pi)
        return self.ConduitSizingResult(
            num_conductors=len(cross_sections_mm2),
            total_cross_section_mm2=total_area,
            recommended_conduit_cross_section_mm2=recommended_area,
            recommended_conduit_diameter_mm=recommended_diameter,
        )

    def validate_conduit(
        self,
        *,
        installed_cross_section_mm2: float,
        installed_diameter_mm: float,
        cross_sections_mm2: List[float],
        fill_factor: float = 0.4,
    ) -> "RuleEngine.ConduitValidation":
        """Validate an installed conduit size against recommended sizing.

        This function computes the recommended conduit size based on the
        provided conductor cross-sections and compares it to the installed
        conduit’s cross-section.  Compliance is determined by whether the fill
        ratio (total conductor area divided by installed conduit area) is
        within the allowable fill factor.  The diameter check is advisory.

        Args:
            installed_cross_section_mm2: Cross-sectional area of the installed conduit.
            installed_diameter_mm: Internal diameter of the installed conduit.
            cross_sections_mm2: List of conductor cross-sectional areas.
            fill_factor: Maximum allowable fill ratio (default 40%).

        Returns:
            A ``ConduitValidation`` summarising the comparison and compliance.
        """
        # Compute recommended sizing
        rec = self.size_conduit(
            cross_sections_mm2=cross_sections_mm2, fill_factor=fill_factor
        )
        total_area = rec.total_cross_section_mm2
        # Avoid divide-by-zero if installed size is zero
        if installed_cross_section_mm2 <= 0.0:
            fill_ratio = float("inf")
            is_compliant = False
        else:
            fill_ratio = total_area / installed_cross_section_mm2
            is_compliant = fill_ratio <= fill_factor
        return self.ConduitValidation(
            installed_conduit_cross_section_mm2=installed_cross_section_mm2,
            installed_conduit_diameter_mm=installed_diameter_mm,
            recommended_conduit_cross_section_mm2=rec.recommended_conduit_cross_section_mm2,
            recommended_conduit_diameter_mm=rec.recommended_conduit_diameter_mm,
            fill_ratio=fill_ratio,
            is_conduit_size_compliant=is_compliant,
        )

    # ------------------------------------------------------------------
    # Structural mount sizing and validation

    @dataclass
    class MountLoadSizingResult:
        """Result of sizing mount load capacity for a set of panels."""

        num_panels: int
        total_weight_kg: float
        wind_load_factor: float
        recommended_mount_capacity_kg: float

    @dataclass
    class MountValidation:
        """Result of validating an existing mount against recommended capacity."""

        installed_mount_capacity_kg: float
        recommended_mount_capacity_kg: float
        is_mount_capacity_compliant: bool

    def size_mount_load(
        self,
        *,
        num_panels: int,
        panel_weight_kg: float = 20.0,
        wind_load_factor: float = 1.3,
    ) -> "RuleEngine.MountLoadSizingResult":
        """Estimate required mount load capacity for PV panels.

        This function calculates the total static weight of all panels and
        applies a wind load factor to determine the minimum load capacity
        required for structural mounts.  Default values assume 20\u00a0kg per
        panel and a 30% increase due to wind.

        Args:
            num_panels: Number of panels to be mounted.
            panel_weight_kg: Weight of each panel in kilograms (default 20\u00a0kg).
            wind_load_factor: Multiplicative factor to account for wind loads
                (default 1.3 \u2192 30% increase).

        Returns:
            A ``MountLoadSizingResult`` containing the recommended mount capacity.
        """
        total_weight = num_panels * panel_weight_kg
        recommended_capacity = total_weight * wind_load_factor
        return self.MountLoadSizingResult(
            num_panels=num_panels,
            total_weight_kg=total_weight,
            wind_load_factor=wind_load_factor,
            recommended_mount_capacity_kg=recommended_capacity,
        )

    def validate_mount(
        self,
        *,
        installed_capacity_kg: float,
        num_panels: int,
        panel_weight_kg: float = 20.0,
        wind_load_factor: float = 1.3,
    ) -> "RuleEngine.MountValidation":
        """Validate an installed mount against recommended load capacity.

        This function calculates the recommended mount capacity for the given
        number of panels and compares it to the installed mount’s load
        rating.  It returns a ``MountValidation`` with a compliance flag.

        Args:
            installed_capacity_kg: Load rating of the installed mounting system.
            num_panels: Number of panels supported by the mount.
            panel_weight_kg: Weight of each panel (default 20\u00a0kg).
            wind_load_factor: Wind load factor (default 1.3).

        Returns:
            A ``MountValidation`` summarising the comparison and compliance.
        """
        rec = self.size_mount_load(
            num_panels=num_panels,
            panel_weight_kg=panel_weight_kg,
            wind_load_factor=wind_load_factor,
        )
        is_compliant = installed_capacity_kg >= rec.recommended_mount_capacity_kg
        return self.MountValidation(
            installed_mount_capacity_kg=installed_capacity_kg,
            recommended_mount_capacity_kg=rec.recommended_mount_capacity_kg,
            is_mount_capacity_compliant=is_compliant,
        )


default_rule_engine = RuleEngine()
