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

    async def run(
        self, contract: ContextContract, policy: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Recommend PV components based on simple heuristics.

        This template reads the component catalogue from the loaded
        domain pack and produces ranked recommendations for PV modules
        and inverters.  Panels are scored by the ratio of their
        efficiency to price; inverters by capacity to price.  The
        highest‑scoring candidates (up to three each) are selected.

        Where possible the template estimates the quantity of each
        candidate required to meet the session's target power.  The
        target power is taken from ``contract.inputs['target_power']``
        (in watts).  If no target power is provided the quantity is
        omitted.  This helps downstream users understand how many
        units of each recommended component would be needed.  An
        approximate cost is also provided by multiplying the unit
        price by the recommended quantity.

        A user‑supplied budget is taken into account by checking
        whether the lowest‑cost pair of a panel and an inverter can
        meet the target power within the budget; if not a validation
        warning is recorded.  Future iterations will incorporate
        more sophisticated scoring based on user preferences, technical
        constraints, pricing and risk factors.

        Args:
            contract: Context with user inputs.  Relevant fields include
                ``budget`` and ``target_power``.
            policy: Governance policies (unused in this implementation).

        Returns:
            A dictionary representing a standard envelope containing
            component recommendations and any validation warnings.
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
        # Hypothesis generation: sort panels by efficiency and price;
        # inverters by capacity.
        def panel_score(p: Dict[str, Any]) -> float:
            # Higher efficiency yields higher score; lower price yields
            # higher score.
            eff = p.get("efficiency", 0.0)
            price = p.get("price", 1.0)
            return eff / price

        def inverter_score(inv: Dict[str, Any]) -> float:
            cap = inv.get("capacity", 0.0)
            price = inv.get("price", 1.0)
            return cap / price

        top_panels = sorted(panels, key=panel_score, reverse=True)[:3]
        top_inverters = sorted(inverters, key=inverter_score, reverse=True)[:3]

        # Determine target power to compute quantities
        try:
            target_power_w = (
                float(contract.inputs.get("target_power"))
                if contract.inputs.get("target_power")
                else None
            )
        except (TypeError, ValueError):
            target_power_w = None

        # Synthesis: combine panel and inverter recommendations, computing
        # recommended quantities and estimated costs when target_power
        # is known.
        recommendations: List[Dict[str, Any]] = []
        for p in top_panels:
            rec: Dict[str, Any] = {
                "type": "panel",
                "id": p.get("id"),
                "name": p.get("name"),
                "score": round(panel_score(p), 4),
                "power": p.get("power"),
                "price": p.get("price"),
                "reason": "High efficiency to price ratio",
            }
            panel_power = p.get("power") or 0
            if target_power_w and panel_power:
                qty = int((target_power_w + panel_power - 1) // panel_power)
                rec["recommended_quantity"] = qty
                rec["estimated_cost"] = qty * p.get("price", 0)
            recommendations.append(rec)
        for inv in top_inverters:
            rec: Dict[str, Any] = {
                "type": "inverter",
                "id": inv.get("id"),
                "name": inv.get("name"),
                "score": round(inverter_score(inv), 4),
                "capacity": inv.get("capacity"),
                "price": inv.get("price"),
                "reason": "High capacity to price ratio",
            }
            inverter_capacity = inv.get("capacity") or 0
            if target_power_w and inverter_capacity:
                qty = int(
                    (target_power_w + inverter_capacity - 1)
                    // inverter_capacity
                )
                rec["recommended_quantity"] = qty
                rec["estimated_cost"] = qty * inv.get("price", 0)
            recommendations.append(rec)

        # Reflection: note if budget constraints might affect recommendations.
        validations: List[str] = []
        if budget_float is not None and target_power_w:
            cheapest_panel = min(panels, key=lambda p: p.get("price", 0))
            cheapest_inverter = min(
                inverters, key=lambda inv: inv.get("price", 0)
            )
            panel_qty = int(
                (target_power_w + cheapest_panel.get("power", 0) - 1)
                // max(cheapest_panel.get("power", 1), 1)
            )
            inverter_qty = int(
                (target_power_w + cheapest_inverter.get("capacity", 0) - 1)
                // max(cheapest_inverter.get("capacity", 1), 1)
            )
            est_total = (
                panel_qty * cheapest_panel.get("price", 0)
                + inverter_qty * cheapest_inverter.get("price", 0)
            )
            if est_total > budget_float:
                validations.append(
                    "Available budget may be insufficient for a system "
                    "meeting the target power; recommendations may "
                    "exceed budget."
                )
        elif budget_float is not None:
            lowest_panel_price = min(p.get("price", 0) for p in panels)
            lowest_inverter_price = min(
                inv.get("price", 0) for inv in inverters
            )
            if lowest_panel_price + lowest_inverter_price > budget_float:
                validations.append(
                    "Available budget may be insufficient for a complete "
                    "system; recommendations may exceed budget."
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
