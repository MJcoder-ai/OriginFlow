"""Domain calculation engines.

This module provides skeleton implementations of domain‑specific
calculation engines for PV, HVAC and water pumping systems.  These
engines compute sizing and performance parameters based on user
requirements and the current design snapshot.  At present, they
provide only basic or placeholder calculations; future versions
should integrate detailed models and real component parameters.

Usage::

    from backend.services.calculation_engines import PVCalculationEngine
    engine = PVCalculationEngine()
    result = await engine.compute(requirements, snapshot)
    print(result['panel_count'])  # e.g. number of panels needed
"""

from __future__ import annotations

from math import ceil
from typing import Any, Dict

from backend.schemas.analysis import DesignSnapshot


class BaseCalculationEngine:
    """Base class for domain calculation engines.

    Subclasses must override :meth:`compute`.
    """

    domain: str

    async def compute(
        self, requirements: Dict[str, Any], snapshot: DesignSnapshot
    ) -> Dict[str, Any]:
        """Compute sizing metrics for the given domain.

        Args:
            requirements: A dictionary of user requirements (e.g.
                target power).
            snapshot: The current design snapshot (may be
                incomplete).

        Returns:
            A dictionary of calculated metrics.  The keys and
            meanings vary by domain.
        """
        raise NotImplementedError


class PVCalculationEngine(BaseCalculationEngine):
    """Simple PV sizing engine.

    Computes the number of panels required to meet a target power.
    This implementation assumes a fixed panel capacity of 300 W.
    Real implementations should inspect the specific panel models in
    the snapshot or component library to obtain accurate ratings.
    """

    domain = "pv"

    async def compute(
        self, requirements: Dict[str, Any], snapshot: DesignSnapshot
    ) -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        target_power = requirements.get("target_power")
        if target_power:
            # Assume each panel supplies 300 W
            panel_power = 300.0
            panel_count = ceil(float(target_power) / panel_power)
            result["panel_count"] = panel_count
        # Future fields: string sizing, inverter ratings, etc.
        return result


class HVACCalculationEngine(BaseCalculationEngine):
    """Skeleton HVAC sizing engine.

    This engine could compute the required compressor or indoor unit
    capacity based on thermal load requirements.  Currently it
    returns an empty result.
    """

    domain = "hvac"

    async def compute(
        self, requirements: Dict[str, Any], snapshot: DesignSnapshot
    ) -> Dict[str, Any]:
        # TODO: Implement HVAC load calculations
        return {}


class WaterCalculationEngine(BaseCalculationEngine):
    """Skeleton water pumping sizing engine.

    Computes pump sizing based on flow and head requirements.  At
    present it returns an empty result.
    """

    domain = "water"

    async def compute(
        self, requirements: Dict[str, Any], snapshot: DesignSnapshot
    ) -> Dict[str, Any]:
        # TODO: Implement water pump sizing calculations
        return {}
