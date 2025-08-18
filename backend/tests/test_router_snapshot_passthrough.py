import pytest
import sys
from pathlib import Path

# Add project root to Python path for imports
sys.path.append(str(Path(__file__).resolve().parents[2]))

from backend.agents.router_agent import RouterAgent  # noqa: E402
from backend.agents.component_agent import ComponentAgent  # noqa: E402


@pytest.mark.asyncio
async def test_router_passes_snapshot(monkeypatch):
    called = {}

    async def fake_handle(self, command, **kwargs):
        called['snapshot'] = kwargs.get('snapshot')
        return []

    monkeypatch.setattr(ComponentAgent, 'handle', fake_handle, raising=False)

    class DummyMessage:
        tool_calls = [type('TC', (), {'function': type('F', (), {'arguments': '{"agent_names":["component_agent"]}'})})]

    class DummyResp:
        choices = [type('C', (), {'message': DummyMessage()})]

    class DummyCompletions:
        @staticmethod
        async def create(*args, **kwargs):
            return DummyResp()

    class DummyClient:
        chat = type('Chat', (), {'completions': DummyCompletions})()

    router = RouterAgent(DummyClient())
    await router.handle('cmd', snapshot={'foo': 'bar'}, trace_id='t1')
    assert called['snapshot'] is not None
