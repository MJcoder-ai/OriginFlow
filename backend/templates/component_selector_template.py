"""Implementation of the component selection template.

The ``ComponentSelectorTemplate`` recommends specific photovoltaic
modules and inverters based on the user's requirements and the
available component catalog.  In Sprint 3–4 this template selects
components using a simple heuristic: highest efficiency panels and
highest capacity inverters within basic budget considerations.  Later
sprints will incorporate more sophisticated scoring based on user
preferences, technical constraints, pricing and risk factors.
"""
from __future__ import annotations

from typing import Any, Dict, List

from backend.domain import load_domain_pack
from backend.models.context_contract import ContextContract
from backend.utils.validator import validate_envelope
from backend.utils.recovery import recover
from .agent_template import AgentTemplate


class ComponentSelectorTemplate(AgentTemplate):
    """Concrete template for component selection."""

    name: str = "ComponentSelector"
    cognitive_mode: str = "select"
    protocol_steps: List[str] = [
        "situation_analysis",
        "hypothesis_generation",
        "synthesis",
        "verification",
        "reflection",
    ]
    output_schema: Dict[str, Any] = {
        "recommendations": {"type": "array", "items": {"type": "object"}},
    }

    def __init__(self, domain: str = "solar", version: str = "v1") -> None:
        self.domain_data = load_domain_pack(domain, version)

    async def run(self, contract: ContextContract, policy: Dict[str, Any]) -> Dict[str, Any]:
        """Recommend PV components based on simple heuristics.

        Args:
            contract: Context with user inputs.  Relevant fields include
                budget and target power.
            policy: Governance policies (unused in this implementation).

        Returns:
            A dictionary representing a standard envelope containing
            component recommendations.
        """
        inputs = contract.inputs
        budget = inputs.get("budget")
        try:
            budget_float = float(budget) if budget else None
        except (ValueError, TypeError):
            budget_float = None

        components = self.domain_data.get("components", {})
        panels: List[Dict[str, Any]] = components.get("panels", [])
        inverters: List[Dict[str, Any]] = components.get("inverters", [])
        if not panels or not inverters:
            return {
                "status": "error",
                "result": None,
                "card": {"template": self.name, "confidence": 0.0},
                "errors": ["Domain pack missing panels or inverters"],
            }

        # Situation analysis: check budget or fallback.
        # Hypothesis generation: sort panels by efficiency and price; inverters by capacity.
        def panel_score(p: Dict[str, Any]) -> float:
            # Higher efficiency yields higher score; lower price yields higher score.
            eff = p.get("efficiency", 0.0)
            price = p.get("price", 1.0)
            return eff / price

        def inverter_score(inv: Dict[str, Any]) -> float:
            cap = inv.get("capacity", 0.0)
            price = inv.get("price", 1.0)
            return cap / price

        top_panels = sorted(panels, key=panel_score, reverse=True)[:3]
        top_inverters = sorted(inverters, key=inverter_score, reverse=True)[:3]

        # Synthesis: combine panel and inverter recommendations.
        recommendations: List[Dict[str, Any]] = []
        for p in top_panels:
            recommendations.append(
                {
                    "type": "panel",
                    "id": p.get("id"),
                    "name": p.get("name"),
                    "score": round(panel_score(p), 4),
                    "power": p.get("power"),
                    "price": p.get("price"),
                    "reason": "High efficiency to price ratio",
                }
            )
        for inv in top_inverters:
            recommendations.append(
                {
                    "type": "inverter",
                    "id": inv.get("id"),
                    "name": inv.get("name"),
                    "score": round(inverter_score(inv), 4),
                    "capacity": inv.get("capacity"),
                    "price": inv.get("price"),
                    "reason": "High capacity to price ratio",
                }
            )

        # Reflection: note if budget constraints might affect recommendations.
        validations: List[str] = []
        if budget_float is not None:
            # Estimate cost of top recommendation.
            lowest_panel_price = min(p.get("price", 0) for p in panels)
            lowest_inverter_price = min(inv.get("price", 0) for inv in inverters)
            if lowest_panel_price + lowest_inverter_price > budget_float:
                validations.append(
                    "Available budget may be insufficient for a complete system; recommendations may exceed budget."
                )

        envelope: Dict[str, Any] = {
            "status": "complete" if not validations else "warning",
            "result": {
                "recommendations": recommendations,
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
        valid, schema_errors = validate_envelope(envelope)
        if not valid:
            return recover(envelope, valid=False, agent=self.name)
        return envelope
