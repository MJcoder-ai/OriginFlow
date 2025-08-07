from backend.policy.confidence import get_thresholds_for_action
from backend.schemas.ai import AiActionType


def test_policy_thresholds_applied():
    thr = get_thresholds_for_action(AiActionType.add_component)
    assert 0 < thr.human_review_min < thr.auto_approve_min <= 1
