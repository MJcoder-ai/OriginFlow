import importlib.util
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from backend.schemas.analysis import CanvasComponent, CanvasLink, DesignSnapshot


def _load_agent_class(module_file: str, class_name: str):
    """Load an agent class without triggering heavy registry imports."""
    if "backend.agents" not in sys.modules:
        pkg = types.ModuleType("backend.agents")
        pkg.__path__ = []  # type: ignore[attr-defined]
        sys.modules["backend.agents"] = pkg
    if "backend.agents.registry" not in sys.modules:
        registry = types.ModuleType("backend.agents.registry")
        registry.register = lambda agent: agent
        registry.register_spec = lambda **kwargs: None
        sys.modules["backend.agents.registry"] = registry
    if "backend.agents.base" not in sys.modules:
        base_module = types.ModuleType("backend.agents.base")
        class AgentBase:  # minimal stub
            pass
        base_module.AgentBase = AgentBase
        sys.modules["backend.agents.base"] = base_module
    spec = importlib.util.spec_from_file_location(
        f"backend.agents.{Path(module_file).stem}", Path(module_file)
    )
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return getattr(module, class_name)


NetworkValidationAgent = _load_agent_class(
    "backend/agents/network_validation_agent.py", "NetworkValidationAgent"
)


@pytest.mark.asyncio
async def test_network_validation_reports_missing_links() -> None:
    agent = NetworkValidationAgent()
    snapshot = DesignSnapshot(
        components=[
            CanvasComponent(id="net1", name="Network", type="generic_network", standard_code="", x=0, y=0),
            CanvasComponent(id="inv1", name="Inverter", type="inverter", standard_code="", x=0, y=0),
            CanvasComponent(id="mon1", name="Monitor", type="generic_monitoring", standard_code="", x=0, y=0),
        ],
        links=[
            CanvasLink(id="l1", source_id="inv1", target_id="net1"),
            # monitoring device unconnected
        ],
    )

    actions = await agent.handle("validate network", snapshot=snapshot.model_dump())
    assert actions, "Agent did not return any actions"
    issues = actions[0]["payload"]["issues"]
    assert any("Monitor" in issue for issue in issues)


@pytest.mark.asyncio
async def test_network_validation_accepts_domain_types() -> None:
    agent = NetworkValidationAgent()
    snapshot = DesignSnapshot(
        components=[
            CanvasComponent(id="n1", name="Net", type="network", standard_code="", x=0, y=0),
            CanvasComponent(id="i1", name="Inv", type="inverter", standard_code="", x=0, y=0),
            CanvasComponent(id="m1", name="Mon", type="monitoring", standard_code="", x=0, y=0),
        ],
        links=[
            CanvasLink(id="l1", source_id="i1", target_id="n1"),
            CanvasLink(id="l2", source_id="m1", target_id="n1"),
        ],
    )

    actions = await agent.handle("validate network", snapshot=snapshot.model_dump())
    assert actions[0]["payload"]["issues"] == []
