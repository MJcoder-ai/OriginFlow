"""Agent for estimating project cost.

This agent provides rough cost estimates for solar PV, HVAC and water
pumping projects based on the requested system size.  For PV systems it
calculates the number of panels needed and multiplies by an assumed
unit cost, then adds approximate costs for an inverter and battery.
For HVAC and water projects it multiplies the system size by a rough
per‑kW cost factor.  In addition, this version will query the
component master database for the lowest‑priced items in each
category when pricing information is available.  Future versions can
extend this logic to integrate with supplier APIs for real‑time
pricing and delivery estimates.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List

from backend.agents.base import AgentBase
from backend.agents.registry import register, register_spec
from backend.schemas.ai import AiAction, AiActionType
from backend.services.component_db_service import get_component_db_service


class FinancialAgent(AgentBase):
    """Cost estimation agent for PV, HVAC and water systems.

    This agent examines a user's request to determine the system size
    (specified in kW or tons) and the domain (PV, HVAC or water).  It
    then computes a cost estimate.  When pricing data exists in the
    component master database, the agent uses the lowest available
    component prices to generate a detailed breakdown.  Otherwise, it
    falls back to rough per‑kW cost assumptions.
    """

    name = "financial_agent"
    description = "Provides rough cost estimates for PV, HVAC and water projects."

    async def handle(self, command: str, **kwargs) -> List[Dict[str, Any]]:
        text = command.lower()
        # Extract system size from the command.  Accept both kW and ton units.
        size_kw: float | None = None
        kw_match = re.search(r"(\d+(?:\.\d+)?)\s*(kw|kilowatt)", text)
        ton_match = re.search(r"(\d+(?:\.\d+)?)\s*(ton|tons|tr)", text)
        if kw_match:
            try:
                size_kw = float(kw_match.group(1))
            except ValueError:
                size_kw = None
        elif ton_match:
            try:
                tons = float(ton_match.group(1))
                # Convert tons to kW (approx. 1 ton = 3.517 kW)
                size_kw = tons * 3.517
            except ValueError:
                size_kw = None

        # Infer the domain from keywords in the command.
        if any(word in text for word in ["solar", "pv"]):
            domain = "PV"
        elif any(word in text for word in ["hvac", "air", "ac"]):
            domain = "HVAC"
        elif any(word in text for word in ["pump", "water"]):
            domain = "Water"
        else:
            domain = None

        # Validate inputs
        if size_kw is None or domain is None:
            msg = (
                "To estimate cost please specify a system size and domain, e.g. "
                "'estimate cost of a 5 kW solar system'."
            )
            return [
                AiAction(
                    action=AiActionType.validation,
                    payload={"message": msg},
                    version=1,
                ).model_dump()
            ]

        # Compose cost estimate based on domain
        message: str
        if domain == "PV":
            # PV: number of panels required at 400 W each
            panel_power_w = 400.0
            num_panels = max(1, int(round((size_kw * 1000.0) / panel_power_w)))
            # Try to fetch real prices from the component DB
            panel_price: float | None = None
            inverter_price: float | None = None
            battery_price: float | None = None
            async for svc in get_component_db_service():
                panels = await svc.search(category="panel")
                priced_panels = [c for c in panels if c.price is not None]
                if priced_panels:
                    priced_panels.sort(key=lambda c: c.price)
                    panel_price = priced_panels[0].price
                inverters = await svc.search(category="inverter")
                priced_invs = [c for c in inverters if c.price is not None]
                if priced_invs:
                    priced_invs.sort(key=lambda c: c.price)
                    inverter_price = priced_invs[0].price
                batteries = await svc.search(category="battery")
                priced_bats = [c for c in batteries if c.price is not None]
                if priced_bats:
                    priced_bats.sort(key=lambda c: c.price)
                    battery_price = priced_bats[0].price
                break
            if panel_price and inverter_price and battery_price:
                total_cost = num_panels * panel_price + inverter_price + battery_price
                message = (
                    f"Cost estimate for a {size_kw:g} kW solar system (using lowest priced items in the database):\n"
                    f"- Panels: {num_panels} × ${panel_price:.2f} = ${num_panels * panel_price:.2f}\n"
                    f"- Inverter: ${inverter_price:.2f}\n"
                    f"- Battery: ${battery_price:.2f}\n"
                    f"Total ≈ ${total_cost:.2f}."
                )
            else:
                # Fallback heuristic pricing
                fallback_panel_price = 200.0
                fallback_inv_price = 1000.0
                fallback_bat_price = 500.0
                total_cost = num_panels * fallback_panel_price + fallback_inv_price + fallback_bat_price
                message = (
                    f"Estimated cost for a {size_kw:g} kW solar system: {num_panels} panels @ ${fallback_panel_price:.0f} each, "
                    f"inverter ${fallback_inv_price:.0f}, battery ${fallback_bat_price:.0f}. Total ≈ ${total_cost:.0f}."
                )
        elif domain == "HVAC":
            # HVAC: cost per kW based on compressors
            base_cost_per_kw: float | None = None
            async for svc in get_component_db_service():
                comps = await svc.search(category="compressor")
                priced_comps = [c for c in comps if c.price is not None and c.power is not None]
                if priced_comps:
                    # Sort by cost per kW
                    priced_comps.sort(key=lambda c: c.price / (c.power / 1000.0))
                    best = priced_comps[0]
                    base_cost_per_kw = best.price / (best.power / 1000.0)
                break
            if base_cost_per_kw:
                total_cost = size_kw * base_cost_per_kw
                message = (
                    f"Cost estimate for a {size_kw:g} kW HVAC system using the lowest cost per kW compressor in the database: "
                    f"${total_cost:.2f}."
                )
            else:
                # Rough assumption for HVAC equipment cost per kW
                cost_per_kw = 500.0
                total_cost = size_kw * cost_per_kw
                message = (
                    f"Estimated cost for a {size_kw:g} kW (≈ {size_kw/3.517:.1f} ton) HVAC system: ${total_cost:.0f}."
                )
        elif domain == "Water":
            # Water: cost per kW based on pump pricing
            base_cost_per_kw: float | None = None
            async for svc in get_component_db_service():
                pumps = await svc.search(category="pump")
                priced_pumps = [c for c in pumps if c.price is not None and c.power is not None]
                if priced_pumps:
                    priced_pumps.sort(key=lambda c: c.price / (c.power / 1000.0))
                    best = priced_pumps[0]
                    base_cost_per_kw = best.price / (best.power / 1000.0)
                break
            if base_cost_per_kw:
                total_cost = size_kw * base_cost_per_kw
                message = (
                    f"Cost estimate for a {size_kw:g} kW water pumping system using the lowest cost per kW pump in the database: "
                    f"${total_cost:.2f}."
                )
            else:
                cost_per_kw = 400.0
                total_cost = size_kw * cost_per_kw
                message = (
                    f"Estimated cost for a {size_kw:g} kW water pumping system: ${total_cost:.0f}."
                )
        else:
            message = "Unable to determine cost for the given input."

        return [
            AiAction(
                action=AiActionType.validation,
                payload={"message": message},
                version=1,
            ).model_dump()
        ]


# instantiate the agent
financial_agent = register(FinancialAgent())
register_spec(name="financial_agent", domain="finance", capabilities=["finance:estimate"])

