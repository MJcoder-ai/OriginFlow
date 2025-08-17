import pytest
import importlib.util
import sys
import types
from pathlib import Path

def _load_component_agent():
    if "backend" not in sys.modules:
        pkg_root = types.ModuleType("backend")
        pkg_root.__path__ = [str(Path("backend"))]  # type: ignore[attr-defined]
        sys.modules["backend"] = pkg_root
    if "backend.agents" not in sys.modules:
        pkg = types.ModuleType("backend.agents")
        pkg.__path__ = [str(Path("backend/agents"))]  # type: ignore[attr-defined]
        sys.modules["backend.agents"] = pkg
    if "backend.services" not in sys.modules:
        services_pkg = types.ModuleType("backend.services")
        services_pkg.__path__ = []  # type: ignore[attr-defined]
        sys.modules["backend.services"] = services_pkg
    if "backend.services.component_service" not in sys.modules:
        comp_service = types.ModuleType("backend.services.component_service")
        async def find_component_by_name(name: str):
            return None
        comp_service.find_component_by_name = find_component_by_name
        sys.modules["backend.services.component_service"] = comp_service
    if "backend.services.ai_clients" not in sys.modules:
        ai_clients = types.ModuleType("backend.services.ai_clients")
        def get_openai_client():
            class _Client:
                pass
            return _Client()
        ai_clients.get_openai_client = get_openai_client
        sys.modules["backend.services.ai_clients"] = ai_clients
    if "backend.services.component_db_service" not in sys.modules:
        comp_db = types.ModuleType("backend.services.component_db_service")
        async def _stub_db_service():
            class _Svc:
                async def get_by_part_number(self, part_number: str):
                    return None

                async def search(self, category: str):
                    return []

            yield _Svc()
        comp_db.get_component_db_service = _stub_db_service
        sys.modules["backend.services.component_db_service"] = comp_db
    if "backend.agents.registry" not in sys.modules:
        registry = types.ModuleType("backend.agents.registry")
        registry.register = lambda agent: agent
        registry.register_spec = lambda **kwargs: None
        sys.modules["backend.agents.registry"] = registry
    spec = importlib.util.spec_from_file_location(
        "backend.agents.component_agent", Path("backend/agents/component_agent.py")
    )
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module

component_agent = _load_component_agent()
ComponentAgent = component_agent.ComponentAgent

class DummyClient:
    """Minimal stub OpenAI client."""
    pass

class DummyComponentService:
    async def get_by_part_number(self, part_number: str):
        return None

    async def search(self, category: str):
        return []

async def _dummy_service():
    yield DummyComponentService()

@pytest.mark.asyncio
async def test_generic_placeholder_when_library_empty(monkeypatch):
    """Agent should add a generic component when library has none."""
    monkeypatch.setattr(component_agent, "get_component_db_service", _dummy_service)
    agent = ComponentAgent(DummyClient())
    actions = await agent.handle("add solar panel")
    from backend.schemas.ai import AiActionType
    assert actions[0]["action"] == AiActionType.add_component
    assert actions[0]["payload"]["name"] == "generic_panel"
    assert actions[0]["payload"]["type"] == "panel"
    assert actions[1]["action"] == AiActionType.validation
    assert "generic placeholder" in actions[1]["payload"]["message"]
