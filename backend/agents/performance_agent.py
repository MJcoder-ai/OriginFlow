from __future__ import annotations

import re
from typing import Any, Dict, List

from backend.agents.base import AgentBase
from backend.agents.registry import register, register_spec
from backend.schemas.ai import AiAction, AiActionType


class PerformanceAgent(AgentBase):
    """Estimates system performance for PV, HVAC and water projects."""

    name = "performance_agent"
    description = (
        "Roughly estimates annual energy yield or efficiency for PV, HVAC and water systems."
    )

    async def handle(self, command: str, **kwargs) -> List[Dict[str, Any]]:
        text = command.lower()
        size_kw: float | None = None
        size_tons: float | None = None
        kw_match = re.search(r"(\d+(?:\.\d+)?)\s*(kw|kilowatt)", text)
        ton_match = re.search(r"(\d+(?:\.\d+)?)\s*(ton|tons|tr)", text)
        if kw_match:
            try:
                size_kw = float(kw_match.group(1))
            except ValueError:
                size_kw = None
        if ton_match and size_kw is None:
            try:
                size_tons = float(ton_match.group(1))
                size_kw = size_tons * 3.517
            except ValueError:
                size_tons = None

        if any(word in text for word in ["solar", "pv"]):
            domain = "PV"
        elif any(word in text for word in ["hvac", "air", "ac"]):
            domain = "HVAC"
        elif any(word in text for word in ["pump", "water"]):
            domain = "Water"
        else:
            domain = None

        if size_kw is None or domain is None:
            message = (
                "To estimate performance please specify the domain and system size in kW, "
                "for example 'estimate performance of 5 kW solar system'."
            )
            return [
                AiAction(
                    action=AiActionType.validation,
                    payload={"message": message},
                    version=1,
                ).model_dump()
            ]

        if domain == "PV":
            annual_kwh = size_kw * 1000 * 4 * 365 * 0.8 / 1000.0
            message = (
                f"A {size_kw:g} kW solar system produces roughly {annual_kwh:.0f} kWh per year "
                f"(assuming 4 peak sun-hours per day and 80% system efficiency)."
            )
        elif domain == "HVAC":
            annual_kwh = size_kw * 6 * 200 / 3.0
            message = (
                f"A cooling/heating system sized at {size_kw:g} kW (≈ {size_kw/3.517:.1f} tons) "
                f"will consume roughly {annual_kwh:.0f} kWh per year assuming 6 hours of operation on 200 days per year and a COP of 3.0."
            )
        else:  # Water pumping
            annual_kwh = size_kw * 4 * 200 / 0.6
            message = (
                f"A water pumping system rated at {size_kw:g} kW will consume roughly {annual_kwh:.0f} kWh per year "
                f"assuming 4 hours of operation on 200 days per year and 60% efficiency."
            )

        action = AiAction(
            action=AiActionType.validation, payload={"message": message}, version=1
        ).model_dump()
        return [action]


performance_agent = register(PerformanceAgent())
register_spec(name="performance_agent", domain="design")
