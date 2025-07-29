import asyncio
import json
import os
import sys
from pathlib import Path

import pytest

os.environ.setdefault("OPENAI_API_KEY", "test")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test.db")

sys.path.append(str(Path(__file__).resolve().parents[2]))

from backend.agents import router_agent  # noqa: E402
from backend.agents.router_agent import RouterAgent
from backend.agents.registry import register
from backend.agents.base import AgentBase

class DummyAgent(AgentBase):
    name = "dummy"
    description = "test"

    async def handle(self, command: str):
        return [{"action": "noop", "payload": {}, "version": 1}]

# register dummy specialist agents for routing
for _name in (
    "component_agent",
    "link_agent",
    "layout_agent",
    "bom_agent",
    "inventory_agent",
    "datasheet_fetch_agent",
    "system_design_agent",
    "wiring_agent",
    "performance_agent",
):
    register(type("DA", (DummyAgent,), {"name": _name})())

@pytest.mark.asyncio
async def test_router_examples(monkeypatch):
    router = RouterAgent()

    async def fake_create(**kwargs):
        content = kwargs["messages"][-1]["content"].lower()
        if "datasheet" in content:
            agent = "datasheet_fetch_agent"
        elif "find" in content:
            agent = "inventory_agent"
        elif "design" in content:
            agent = "system_design_agent"
        elif "link" in content:
            agent = "link_agent"
        elif "layout" in content:
            agent = "layout_agent"
        elif "bill of materials" in content:
            agent = "bom_agent"
        elif "wiring" in content:
            agent = "wiring_agent"
        elif "performance" in content:
            agent = "performance_agent"
        else:
            agent = "component_agent"
        class Choice:
            message = type("msg", (), {"tool_calls": [type("tc", (), {"function": type("f", (), {"arguments": json.dumps({"agent_names": [agent]})})()})]})()
        return type("resp", (), {"choices": [Choice]})()

    class DummyClient:
        class chat:
            class completions:
                @staticmethod
                async def create(**kw):
                    return await fake_create(**kw)

    monkeypatch.setattr(router_agent, "client", DummyClient())
    for cmd, expected in [
        ("add battery", "component_agent"),
        ("link X to Y", "link_agent"),
        ("organise layout", "layout_agent"),
        ("what is the bill of materials", "bom_agent"),
        ("design a 5 kW solar system", "system_design_agent"),
        ("find panels 500", "inventory_agent"),
        ("datasheet for ABC123", "datasheet_fetch_agent"),
        ("size wiring for 5 kW over 20 m", "wiring_agent"),
        ("estimate system performance", "performance_agent"),
    ]:
        out = await router.handle(cmd)
        assert any(a["action"] for a in out)

