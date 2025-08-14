"""Implementation of the photovoltaic design template.

The ``PVDesignTemplate`` performs a physics-first design of a solar
photovoltaic (PV) system.  It uses domain knowledge supplied via a
domain pack to compute the number of modules and inverters needed to
meet the user's target power, taking into account panel specifications
and basic constraints.  The template follows the five-step reasoning
scaffold defined by ADPF: situation analysis, hypothesis generation,
synthesis, verification and reflection.  For Sprint 3–4 a simplified
computation is provided; later sprints will enrich this with rule
checks, alternative generation and context contract updates.
"""
from __future__ import annotations

from math import ceil
from typing import Any, Dict, List

from backend.domain import load_domain_pack
from backend.models.context_contract import ContextContract
from backend.models.standard_envelope import StandardEnvelope
from backend.utils.validator import validate_envelope
from backend.utils.recovery import recover
from .agent_template import AgentTemplate


class PVDesignTemplate(AgentTemplate):
    """Concrete template for PV system design."""

    name: str = "PVDesign"
    cognitive_mode: str = "design"
    protocol_steps: List[str] = [
        "situation_analysis",
        "hypothesis_generation",
        "synthesis",
        "verification",
        "reflection",
    ]
    # Output schema: for now we indicate that ``design`` is returned in the result.
    output_schema: Dict[str, Any] = {
        "design": {"type": "object"},
    }

    def __init__(self, domain: str = "solar", version: str = "v1") -> None:
        # Load the domain pack once during initialisation.
        self.domain_data = load_domain_pack(domain, version)

    async def run(self, contract: ContextContract, policy: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a preliminary PV design.

        Args:
            contract: The context contract containing user inputs such as
                target power and roof area.
            policy: Governance and safety policy (unused in this simple implementation).

        Returns:
            A dictionary representing a standard envelope with ``status``,
            ``result``, ``card``, ``metrics``, ``validations`` and ``errors``.
        """
        inputs = contract.inputs
        target_power = inputs.get("target_power")
        # Default to a 5 kW system if no target power is provided.
        try:
            target_power_float = float(target_power) if target_power else 5000.0
        except (ValueError, TypeError):
            target_power_float = 5000.0
        roof_area = inputs.get("roof_area")
        roof_area_float = None
        if roof_area is not None:
            try:
                roof_area_float = float(roof_area)
            except (ValueError, TypeError):
                roof_area_float = None

        # Extract component specs from the domain data.
        components = self.domain_data.get("components", {})
        panels: List[Dict[str, Any]] = components.get("panels", [])
        inverters: List[Dict[str, Any]] = components.get("inverters", [])
        if not panels or not inverters:
            # Domain pack incomplete; return degraded envelope.
            return {
                "status": "error",
                "result": None,
                "card": {"template": self.name, "confidence": 0.0},
                "errors": ["Domain pack missing panel or inverter data"],
            }

        # Select the first (default) panel and inverter.  In future this will
        # use a scoring mechanism and consider user preferences.
        panel = panels[0]
        inverter = inverters[0]
        panel_power = panel.get("power", 400)
        panel_area = panel.get("area", 1.8)
        inverter_capacity = inverter.get("capacity", 5000)

        # Situation analysis: capture assumptions.
        assumptions = {
            "panel_power": panel_power,
            "panel_area": panel_area,
            "inverter_capacity": inverter_capacity,
        }

        # Hypothesis generation: propose counts based on formulas.
        panel_count = max(1, ceil(target_power_float / panel_power))
        array_power = panel_count * panel_power
        inverter_count = max(1, ceil(array_power / inverter_capacity))

        # Verification: check simple roof area constraint if provided.
        validations: List[str] = []
        if roof_area_float is not None:
            used_area = panel_count * panel_area
            if used_area > roof_area_float:
                validations.append(
                    f"Panel area {used_area:.2f} m^2 exceeds available roof area {roof_area_float:.2f} m^2"
                )

        # Reflection: summarise design rationale.
        rationale = (
            f"Designed a {array_power/1000:.1f} kW PV array using {panel_count} modules "
            f"and {inverter_count} inverters."
        )

        design = {
            "panel_count": panel_count,
            "inverter_count": inverter_count,
            "panel_type": panel.get("name"),
            "inverter_type": inverter.get("name"),
            "array_power_w": array_power,
            "assumptions": assumptions,
            "rationale": rationale,
        }

        # Construct envelope.
        envelope: Dict[str, Any] = {
            "status": "complete" if not validations else "warning",
            "result": {
                "design": design,
            },
            "card": {
                "template": self.name,
                "cognitive_mode": self.cognitive_mode,
                "confidence": 1.0 if not validations else 0.7,
            },
            "metrics": {},
            "validations": validations,
            "errors": [],
        }
        # Validate envelope schema.
        valid, schema_errors = validate_envelope(envelope)
        if not valid:
            return recover(envelope, valid=False, agent=self.name)
        return envelope
