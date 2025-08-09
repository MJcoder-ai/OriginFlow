import os
import sys
from pathlib import Path

# ensure settings load with dummy env vars
os.environ.setdefault("OPENAI_API_KEY", "test")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test.db")

sys.path.append(str(Path(__file__).resolve().parents[2]))

from backend.policy.confidence import get_thresholds_for_action
from backend.schemas.ai import AiActionType


def test_policy_thresholds_applied():
    thr = get_thresholds_for_action(AiActionType.add_component)
    assert 0 < thr.human_review_min < thr.auto_approve_min <= 1


def test_validation_actions_never_auto_approve():
    thr = get_thresholds_for_action(AiActionType.validation)
    assert thr.auto_approve_min > 1.0
    assert thr.human_review_min == 0.0
