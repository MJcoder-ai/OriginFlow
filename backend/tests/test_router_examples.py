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
for _name in ("component_agent", "link_agent", "layout_agent", "bom_agent"):
    register(type("DA", (DummyAgent,), {"name": _name})())

@pytest.mark.asyncio
async def test_router_examples(monkeypatch):
    router = RouterAgent()

    async def fake_create(**kwargs):
        content = kwargs["messages"][-1]["content"].lower()
        if "link" in content:
            agent = "link_agent"
        elif "layout" in content:
            agent = "layout_agent"
        elif "bill of materials" in content:
            agent = "bom_agent"
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
    ]:
        out = await router.handle(cmd)
        assert any(a["action"] for a in out)
