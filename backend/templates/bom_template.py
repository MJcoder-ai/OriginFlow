"""Implementation of the bill of materials aggregation template.

The ``BillOfMaterialsTemplate`` aggregates component quantities from
design results recorded in the context contract or returned by prior
templates.  It produces a list of items with their quantity and unit
price (when available) and computes the total estimated cost.  To
avoid key collisions when merging results from multiple templates, the
total cost is stored under the key ``bom_total_cost`` rather than
``total_cost``.  The template relies on the domain pack component data
to look up descriptions and prices.  It supports multiple domain packs
(e.g. ``solar`` and ``battery``) and will include items from each pack
when relevant.  Counts of panels, inverters and batteries are retrieved
from the contract's ``inputs`` (preferred) or from recorded decisions.
In later versions this template can integrate with supplier APIs and
apply discounts or taxes.
"""

from __future__ import annotations

from typing import Any, Dict, List

from backend.domain import load_domain_pack
from backend.models.context_contract import ContextContract
from backend.utils.validator import validate_envelope
from backend.utils.recovery import recover
from .agent_template import AgentTemplate


class BillOfMaterialsTemplate(AgentTemplate):
    """Concrete template for bill of materials aggregation."""

    name: str = "BillOfMaterials"
    cognitive_mode: str = "analyze"
    protocol_steps: List[str] = [
        "situation_analysis",
        "hypothesis_generation",
        "synthesis",
        "verification",
        "reflection",
    ]
    output_schema: Dict[str, Any] = {
        "bill_of_materials": {"type": "array", "items": {"type": "object"}},
        "bom_total_cost": {"type": "number"},
    }

    def __init__(
        self, domains: List[str] | None = None, version: str = "v1"
    ) -> None:
        if domains is None:
            domains = ["solar"]
        self.domain_data = {d: load_domain_pack(d, version) for d in domains}

    async def run(
        self, contract: ContextContract, policy: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Aggregate bill of materials items and compute cost.

        Args:
            contract: Context contract with inputs such as component counts.
            policy: Governance policies (unused in this implementation).

        Returns:
            A dictionary representing a standard envelope containing
            the bill of materials and the ``bom_total_cost``.
        """

        inputs = contract.inputs

        panel_count = _to_int(inputs.get("panel_count"))
        inverter_count = _to_int(inputs.get("inverter_count"))
        battery_count = _to_int(inputs.get("battery_count"))

        components_catalog: Dict[str, List[Dict[str, Any]]] = {}
        for data in self.domain_data.values():
            comps = data.get("components", {})
            for kind, items in comps.items():
                existing = components_catalog.setdefault(kind, [])
                existing.extend(items or [])

        bom: List[Dict[str, Any]] = []
        total_cost = 0.0

        def add_item(kind: str, count: int) -> None:
            nonlocal total_cost
            if count <= 0:
                return
            comp_list = (
                components_catalog.get(f"{kind}s")
                or components_catalog.get(kind)
            )
            if not comp_list:
                return
            comp = comp_list[0]
            item: Dict[str, Any] = {
                "type": kind,
                "id": comp.get("id"),
                "description": comp.get("name"),
                "quantity": count,
            }
            price = comp.get("price")
            if price is not None:
                item["unit_price"] = price
                total_cost += count * price
            bom.append(item)

        add_item("panel", panel_count)
        add_item("inverter", inverter_count)
        add_item("battery", battery_count)

        result = {
            "bill_of_materials": bom,
            "bom_total_cost": total_cost,
        }

        envelope: Dict[str, Any] = {
            "status": "complete",
            "result": result,
            "card": {
                "template": self.name,
                "cognitive_mode": self.cognitive_mode,
                "confidence": 1.0,
            },
            "metrics": {},
            "validations": [],
            "errors": [],
        }
        valid, _ = validate_envelope(envelope)
        if not valid:
            return recover(envelope, valid=False, agent=self.name)
        return envelope


def _to_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0
