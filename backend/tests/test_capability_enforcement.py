import pytest

from backend.services.ai_service import _check_capabilities
from backend.schemas.ai import AiAction, AiActionType


def test_missing_capability_raises():
    action = AiAction(action=AiActionType.remove_link, payload={}, version=1)
    with pytest.raises(PermissionError):
        _check_capabilities("component_agent", action)
