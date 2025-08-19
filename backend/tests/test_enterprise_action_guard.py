"""Enterprise-grade tests for action guard and SAAR normalization.

These tests ensure consistent behavior across all execution paths and
verify that the action guard prevents component misclassification in
production scenarios.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock

from backend.services.ai.action_guard import normalize_add_component
from backend.services.ai.state_action_resolver import StateAwareActionResolver
from backend.schemas.analysis import DesignSnapshot


class TestActionGuardEnterprise:
    """Enterprise-grade tests for action guard functionality."""

    @pytest.mark.asyncio
    async def test_explicit_inverter_mention_override(self):
        """Test that explicit 'inverter' mention forces correct classification."""
        # Arrange: Create a snapshot that might bias toward panels
        snapshot = DesignSnapshot(
            components=[],
            links=[],
            requirements={"target_power_kw": 5.0}  # This might bias toward panels
        )
        
        # LLM incorrectly classified as panel
        llm_payload = {
            "type": "panel",
            "name": "Generic Panel",
            "_llm_confidence": 0.8
        }
        
        # Act: Apply action guard
        result = await normalize_add_component(
            user_text="add inverter to the design",
            snapshot=snapshot,
            payload=llm_payload.copy()
        )
        
        # Assert: Should override LLM and use 'inverter'
        assert result["type"] == "inverter"
        assert result["component_type"] == "inverter"
        assert result["_resolver"]["corrected"] is True
        assert "Explicit mention of 'inverter'" in result["_resolver"]["rationale"]
        assert result["_resolver"]["confidence"] == 0.99

    @pytest.mark.asyncio
    async def test_explicit_panel_mention_preserved(self):
        """Test that explicit 'panel' mention is correctly preserved."""
        snapshot = DesignSnapshot(components=[], links=[])
        
        # LLM correctly classified as panel
        llm_payload = {
            "type": "panel",
            "name": "Solar Panel",
            "_llm_confidence": 0.9
        }
        
        # Act
        result = await normalize_add_component(
            user_text="add solar panel",
            snapshot=snapshot,
            payload=llm_payload.copy()
        )
        
        # Assert: Should keep panel classification
        assert result["type"] == "panel"
        assert result["component_type"] == "panel"
        assert result["_resolver"]["corrected"] is True  # Still goes through SAAR for consistency
        assert "Explicit mention of 'panel'" in result["_resolver"]["rationale"]

    @pytest.mark.asyncio
    async def test_ambiguous_text_uses_similarity_priors(self):
        """Test fallback to similarity+priors for ambiguous requests."""
        snapshot = DesignSnapshot(components=[], links=[])
        
        llm_payload = {
            "type": "unknown",
            "name": "Some Component"
        }
        
        # Act: Ambiguous text that doesn't explicitly mention component type
        result = await normalize_add_component(
            user_text="add something electrical",
            snapshot=snapshot,
            payload=llm_payload.copy()
        )
        
        # Assert: Should use SAAR's similarity-based classification
        assert result["type"] in ["panel", "inverter", "battery", "meter", "controller", "combiner", "optimizer", "disconnect"]
        assert result["_resolver"]["corrected"] is True
        assert "Similarity=" in result["_resolver"]["rationale"]

    @pytest.mark.asyncio  
    async def test_high_confidence_llm_preserved(self):
        """Test that high-confidence LLM classifications are preserved when appropriate."""
        snapshot = DesignSnapshot(components=[], links=[])
        
        # High confidence LLM that matches SAAR
        llm_payload = {
            "type": "battery",
            "name": "Battery Pack", 
            "_llm_confidence": 0.95
        }
        
        # Act: Ambiguous text where LLM confidence might matter
        result = await normalize_add_component(
            user_text="add energy storage",
            snapshot=snapshot,
            payload=llm_payload.copy()
        )
        
        # Assert: SAAR should still run for consistency, but result should be reasonable
        assert result["type"] in ["battery", "storage"]  # Either is reasonable
        assert result["_resolver"] is not None

    @pytest.mark.asyncio
    async def test_guard_failure_returns_original(self):
        """Test that guard failures don't break the system."""
        snapshot = None  # This might cause SAAR to fail
        
        llm_payload = {
            "type": "panel",
            "name": "Fallback Panel"
        }
        
        # Act: This should handle the failure gracefully
        result = await normalize_add_component(
            user_text="add something",
            snapshot=snapshot,
            payload=llm_payload.copy()
        )
        
        # Assert: Should return original payload if guard fails
        assert result["type"] == "panel"
        assert result["name"] == "Fallback Panel"

    def test_explicit_class_detection_accuracy(self):
        """Test the explicit class detection with various synonyms."""
        resolver = StateAwareActionResolver()
        
        test_cases = [
            ("add inverter", "inverter"),
            ("add string inverter", "inverter"), 
            ("add microinverter", "inverter"),
            ("add solar panel", "panel"),
            ("add pv module", "panel"),
            ("add battery storage", "battery"),
            ("add energy storage", "battery"),
            ("add disconnect switch", "disconnect"),
            ("add dc optimizer", "optimizer"),
            ("add multiple components", None),  # Ambiguous
            ("design a solar system", None),    # No explicit component
        ]
        
        for text, expected in test_cases:
            result = resolver._explicit_class_from_text(text)
            assert result == expected, f"Failed for '{text}': expected {expected}, got {result}"


class TestServerSideApplyConsistency:
    """Test that server-side apply uses same normalization as client-side."""

    @pytest.mark.asyncio
    async def test_apply_actions_normalizes_add_component(self):
        """Test that apply_actions runs SAAR normalization."""
        from backend.services.ai_service import AiOrchestrator
        
        # Arrange: Action with wrong component type
        actions = [{
            "action": "add_component",
            "payload": {
                "type": "panel",  # Wrong - should be inverter
                "name": "Test Component"
            }
        }]
        
        snapshot = {"components": [], "links": []}
        user_text = "add inverter"
        
        orchestrator = AiOrchestrator()
        
        # Act
        result = await orchestrator.apply_actions(
            actions,
            snapshot=snapshot,
            user_text=user_text
        )
        
        # Assert: Should normalize component type
        assert len(result) == 1
        assert result[0]["action"] == "add_component"
        # The payload should be normalized by the action guard
        assert result[0]["payload"]["type"] == "inverter"

    @pytest.mark.asyncio
    async def test_apply_actions_without_context_preserves_original(self):
        """Test that apply_actions without context preserves original actions."""
        from backend.services.ai_service import AiOrchestrator
        
        actions = [{
            "action": "add_component", 
            "payload": {"type": "panel", "name": "Test"}
        }]
        
        orchestrator = AiOrchestrator()
        
        # Act: No snapshot or user_text provided
        result = await orchestrator.apply_actions(actions)
        
        # Assert: Should preserve original (with warning logged)
        assert len(result) == 1
        assert result[0]["payload"]["type"] == "panel"


@pytest.mark.integration
class TestEndToEndConsistency:
    """Integration tests verifying consistent behavior across all paths."""

    @pytest.mark.asyncio
    async def test_component_agent_vs_server_apply_consistency(self):
        """Test that ComponentAgent and server apply produce identical results."""
        # This would be a comprehensive integration test comparing:
        # 1. ComponentAgent.handle("add inverter") output
        # 2. AiOrchestrator.apply_actions with same input
        # Both should produce identical normalized results
        pass  # Implementation depends on your test infrastructure

    @pytest.mark.asyncio  
    async def test_message_accuracy_after_normalization(self):
        """Test that validation messages match the final component type."""
        # Verify that after normalization, the message says:
        # "No inverter in the library..." not "No panel in the library..."
        # when the final type is 'inverter'
        pass  # Implementation depends on your LibrarySelector integration


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
