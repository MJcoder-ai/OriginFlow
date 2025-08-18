import pytest
import sys
from pathlib import Path

# Add project root to Python path for imports
sys.path.append(str(Path(__file__).resolve().parents[2]))

from backend.services.ai_service import _check_capabilities  # noqa: E402
from backend.schemas.ai import AiAction, AiActionType  # noqa: E402


def test_missing_capability_raises():
    action = AiAction(action=AiActionType.remove_link, payload={}, version=1)
    with pytest.raises(PermissionError):
        _check_capabilities("component_agent", action)
