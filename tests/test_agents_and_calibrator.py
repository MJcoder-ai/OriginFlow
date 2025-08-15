"""
End-to-End scenario tests for OriginFlow agents and calibration.

These tests exercise the behaviour of the meta-cognition and consensus
agents as well as the confidence calibrator. They simulate user
interactions and verify that the agents produce the expected ADPF
envelopes and that the calibrator adjusts confidence scores and
thresholds based on feedback.

To run these tests install pytest and execute ``pytest -q`` in the
repository root. The tests use asyncio's event loop to call async
methods. Note that these tests assume that ``backend.utils.adpf``
provides a ``wrap_response`` function as in the full OriginFlow codebase.
If the module is missing, these tests will skip meta-cognition and
consensus tests.
"""

import importlib
import importlib.util
import sys
import types
from pathlib import Path

import pytest


def _has_adpf_wrap() -> bool:
    """Check whether backend.utils.adpf.wrap_response is available."""
    try:
        mod = importlib.import_module("backend.utils.adpf")
        return hasattr(mod, "wrap_response")
    except ImportError:
        return False


def _load_agent_class(module_file: str, class_name: str):
    """Load an agent class without triggering heavy registry imports."""
    # Ensure package placeholders for backend.agents and submodules
    if "backend.agents" not in sys.modules:
        pkg = types.ModuleType("backend.agents")
        pkg.__path__ = []  # type: ignore[attr-defined]
        sys.modules["backend.agents"] = pkg
    if "backend.agents.registry" not in sys.modules:
        registry = types.ModuleType("backend.agents.registry")
        registry.register = lambda agent: agent
        registry.register_spec = lambda **kwargs: None
        sys.modules["backend.agents.registry"] = registry
    # Load base module normally
    if "backend.agents.base" not in sys.modules:
        spec_base = importlib.util.spec_from_file_location(
            "backend.agents.base", Path("backend/agents/base.py")
        )
        base_module = importlib.util.module_from_spec(spec_base)
        assert spec_base and spec_base.loader
        spec_base.loader.exec_module(base_module)
        sys.modules["backend.agents.base"] = base_module
    # Load the desired agent module
    spec = importlib.util.spec_from_file_location(
        f"backend.agents.{Path(module_file).stem}", Path(module_file)
    )
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return getattr(module, class_name)


@pytest.mark.asyncio
@pytest.mark.skipif(not _has_adpf_wrap(), reason="wrap_response not available")
async def test_meta_cognition_questions():
    """MetaCognitionAgent should generate questions for missing items."""
    MetaCognitionAgent = _load_agent_class(
        "backend/agents/meta_cognition_agent.py", "MetaCognitionAgent"
    )
    agent = MetaCognitionAgent()
    resp = await agent.execute(
        session_id="s1", tid="meta_cognition", missing=["panel orientation", "datasheet"]
    )
    assert resp["status"] == "blocked"
    card = resp["output"]["card"]
    # Ensure questions are present and correspond to missing items
    assert "questions" in card
    assert len(card["questions"]) == 2
    assert "panel orientation" in card["questions"][0]
    assert "datasheet" in card["questions"][1]


@pytest.mark.asyncio
@pytest.mark.skipif(not _has_adpf_wrap(), reason="wrap_response not available")
async def test_meta_cognition_reason():
    """MetaCognitionAgent should generate a single question for a reason string."""
    MetaCognitionAgent = _load_agent_class(
        "backend/agents/meta_cognition_agent.py", "MetaCognitionAgent"
    )
    agent = MetaCognitionAgent()
    resp = await agent.execute(
        session_id="s2", tid="meta_cognition", reason="missing PV layout"
    )
    card = resp["output"]["card"]
    assert len(card["questions"]) == 1
    assert "missing PV layout" in card["questions"][0]


@pytest.mark.asyncio
@pytest.mark.skipif(not _has_adpf_wrap(), reason="wrap_response not available")
async def test_consensus_agent_selects_highest_confidence():
    """ConsensusAgent should choose the candidate with highest confidence."""
    ConsensusAgent = _load_agent_class(
        "backend/agents/consensus_agent.py", "ConsensusAgent"
    )
    candidates = [
        {
            "output": {
                "card": {"confidence": 0.6, "title": "Design A"},
                "patch": {"id": "patchA"},
            }
        },
        {
            "output": {
                "card": {"confidence": 0.85, "title": "Design B"},
                "patch": {"id": "patchB"},
            }
        },
    ]
    agent = ConsensusAgent()
    resp = await agent.execute(
        session_id="s3", tid="consensus", candidates=candidates
    )
    card = resp["output"]["card"]
    # The selected card should correspond to the highest confidence design
    selected = card["selected_card"]
    assert selected["title"] == "Design B"
    assert resp["output"]["patch"]["id"] == "patchB"


def test_confidence_calibrator():
    """ConfidenceCalibrator should update confidence and thresholds based on feedback."""
    from backend.utils.confidence_calibration import ConfidenceCalibrator

    calibrator = ConfidenceCalibrator()
    # Record mixed feedback for a single action
    calibrator.record_feedback(
        agent_name="test_agent", action_type="add_component", confidence=0.8, approved=True
    )
    calibrator.record_feedback(
        agent_name="test_agent", action_type="add_component", confidence=0.6, approved=False
    )
    # Acceptance rate is 0.5 -> calibrated confidence drifts halfway towards 0.5
    calibrated = calibrator.calibrate_confidence(
        agent_name="test_agent", action_type="add_component", original_confidence=0.7
    )
    assert abs(calibrated - 0.6) < 1e-6
    # Base threshold remains unchanged when acceptance rate is 0.5
    threshold = calibrator.get_threshold(
        agent_name="test_agent", action_type="add_component", base_threshold=0.75
    )
    assert abs(threshold - 0.75) < 1e-6

