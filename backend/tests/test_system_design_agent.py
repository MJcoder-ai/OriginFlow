from types import SimpleNamespace

import pytest

from backend.agents import system_design_agent as sda
from backend.schemas.ai import AiActionType


class EmptyService:
    async def search(self, **kwargs):  # pragma: no cover - simple stub
        return []


async def empty_service_provider():  # pragma: no cover - simple stub
    yield EmptyService()


class FakeService:
    def __init__(self) -> None:
        self.panels = [
            SimpleNamespace(
                name="CheapPanel",
                category="panel",
                part_number="CP-400",
                price=100.0,
                power=400.0,
            ),
            SimpleNamespace(
                name="ExpensivePanel",
                category="panel",
                part_number="EP-500",
                price=150.0,
                power=500.0,
            ),
        ]
        self.inverters = [
            SimpleNamespace(
                name="Inverter5000",
                category="inverter",
                part_number="INV-5000",
                price=500.0,
                power=5000.0,
            ),
            SimpleNamespace(
                name="Inverter6000",
                category="inverter",
                part_number="INV-6000",
                price=600.0,
                power=6000.0,
            ),
        ]
        self.batteries = [
            SimpleNamespace(
                name="Battery100",
                category="battery",
                part_number="BAT-100",
                price=1000.0,
                power=None,
            ),
            SimpleNamespace(
                name="Battery200",
                category="battery",
                part_number="BAT-200",
                price=1200.0,
                power=None,
            ),
        ]

    async def search(self, category=None, min_power=None, **kwargs):  # pragma: no cover - simple stub
        if category == "panel":
            return self.panels
        if category == "inverter":
            return [c for c in self.inverters if (c.power or 0) >= (min_power or 0)]
        if category == "battery":
            return self.batteries
        return []


async def fake_service_provider():  # pragma: no cover - simple stub
    yield FakeService()


@pytest.mark.asyncio
async def test_missing_components_prompts_upload(monkeypatch):
    monkeypatch.setattr(sda, "get_component_db_service", empty_service_provider)
    agent = sda.SystemDesignAgent()
    actions = await agent.handle("design 5 kW solar system")
    assert actions[0]["action"] == AiActionType.validation
    assert "upload" in actions[0]["payload"]["message"].lower()


@pytest.mark.asyncio
async def test_selects_best_available_components(monkeypatch):
    monkeypatch.setattr(sda, "get_component_db_service", fake_service_provider)
    agent = sda.SystemDesignAgent()
    actions = await agent.handle("design 5 kW solar system")

    panel_actions = [
        a
        for a in actions
        if a["action"] == AiActionType.add_component
        and a["payload"]["type"] == "panel"
    ]
    inverter_action = next(
        a
        for a in actions
        if a["action"] == AiActionType.add_component and a["payload"]["type"] == "inverter"
    )
    battery_action = next(
        a
        for a in actions
        if a["action"] == AiActionType.add_component and a["payload"]["type"] == "battery"
    )

    assert panel_actions[0]["payload"]["standard_code"] == "CP-400"
    assert inverter_action["payload"]["standard_code"] == "INV-5000"
    assert battery_action["payload"]["standard_code"] == "BAT-100"
    assert len(panel_actions) == 13
    assert "CP-400" in actions[-1]["payload"]["message"]

