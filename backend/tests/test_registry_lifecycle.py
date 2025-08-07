import backend.agents  # noqa: F401
from backend.agents.registry import _REGISTRY


def test_register_instance_only():
    assert "component_agent" in _REGISTRY
    assert hasattr(_REGISTRY["component_agent"], "handle")
