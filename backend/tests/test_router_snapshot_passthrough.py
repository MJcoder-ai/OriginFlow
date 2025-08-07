import pytest

from backend.agents.router_agent import RouterAgent
from backend.agents.component_agent import ComponentAgent


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
