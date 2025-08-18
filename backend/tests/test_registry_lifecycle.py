import sys
from pathlib import Path

# Add project root to Python path for imports
sys.path.append(str(Path(__file__).resolve().parents[2]))

import backend.agents  # noqa: F401, E402
from backend.agents.registry import _REGISTRY  # noqa: E402


def test_register_instance_only():
    assert "component_agent" in _REGISTRY
    assert hasattr(_REGISTRY["component_agent"], "handle")
