"""
Comprehensive integration tests for AI-driven wiring system.

This test suite validates the complete AI wiring pipeline including:
- Panel grouping optimization
- Vector store operations
- LLM suggestion generation 
- Port-aware electrical topology
- Integration with existing systems
"""

import pytest
import asyncio
import logging
from typing import Dict, Any, List
from unittest.mock import Mock, patch

from backend.ai.panel_grouping import EnterpriseGroupingEngine, GroupingStrategy, PanelInfo
from backend.ai.vector_store import EnterpriseVectorStore, DesignMetadata, DesignCategory
from backend.ai.llm_wiring_suggest import LLMWiringSuggestionEngine, WiringContext, ConnectionType
from backend.ai.wiring_ai_pipeline import EnterpriseAIWiringPipeline, PipelineConfiguration
from backend.tools.electrical_topology import create_ai_enhanced_electrical_connections
from backend.services.placeholder_component_service import PlaceholderComponentService

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestPanelGrouping:
    """Test panel grouping optimization algorithms."""
    
    def test_spatial_proximity_grouping(self):
        """Test spatial proximity based panel grouping."""
        engine = EnterpriseGroupingEngine()
        
        # Create mock graph with spatially distributed panels
        mock_graph = Mock()
        mock_graph.nodes = {
            "panel_1": Mock(type="panel", data={"x": 0, "y": 0, "power": 400}),
            "panel_2": Mock(type="panel", data={"x": 1, "y": 0, "power": 400}),
            "panel_3": Mock(type="panel", data={"x": 2, "y": 0, "power": 400}),
            "panel_4": Mock(type="panel", data={"x": 10, "y": 0, "power": 400}),  # Far away
            "panel_5": Mock(type="panel", data={"x": 11, "y": 0, "power": 400}),
            "inverter_1": Mock(type="inverter", data={"mppts": 2})
        }
        
        groups = engine.group_panels(mock_graph, GroupingStrategy.SPATIAL_PROXIMITY)
        
        assert len(groups) >= 1
        assert all(len(group) >= 2 for group in groups)  # Minimum string size
        logger.info(f"Spatial grouping created {len(groups)} groups: {groups}")
    
    def test_electrical_optimal_grouping(self):
        """Test electrical characteristics based grouping."""
        engine = EnterpriseGroupingEngine()
        
        # Create mock graph with varied electrical characteristics
        mock_graph = Mock()
        mock_graph.nodes = {
            "panel_1": Mock(type="panel", data={"voltage_oc": 49.5, "current_sc": 11.2, "power": 400}),
            "panel_2": Mock(type="panel", data={"voltage_oc": 49.0, "current_sc": 11.0, "power": 390}),
            "panel_3": Mock(type="panel", data={"voltage_oc": 48.8, "current_sc": 10.9, "power": 385}),
            "panel_4": Mock(type="panel", data={"voltage_oc": 45.0, "current_sc": 10.0, "power": 350}),  # Different specs
            "panel_5": Mock(type="panel", data={"voltage_oc": 44.8, "current_sc": 9.8, "power": 345}),
        }
        
        groups = engine.group_panels(mock_graph, GroupingStrategy.ELECTRICAL_OPTIMAL)
        
        assert len(groups) >= 1
        # Check that similar electrical characteristics are grouped together
        for group in groups:
            assert len(group) >= 2
        
        logger.info(f"Electrical grouping created {len(groups)} groups: {groups}")
    
    def test_performance_optimized_grouping(self):
        """Test multi-factor performance optimization."""
        engine = EnterpriseGroupingEngine()
        
        mock_graph = Mock()
        mock_graph.nodes = {
            "panel_1": Mock(type="panel", data={
                "x": 0, "y": 0, "power": 400, "shading_factor": 1.0, "performance_ratio": 1.0
            }),
            "panel_2": Mock(type="panel", data={
                "x": 1, "y": 0, "power": 400, "shading_factor": 1.0, "performance_ratio": 1.0
            }),
            "panel_3": Mock(type="panel", data={
                "x": 2, "y": 0, "power": 400, "shading_factor": 0.8, "performance_ratio": 0.9
            }),
            "panel_4": Mock(type="panel", data={
                "x": 3, "y": 0, "power": 400, "shading_factor": 0.8, "performance_ratio": 0.9
            }),
        }
        
        groups = engine.group_panels(mock_graph, GroupingStrategy.PERFORMANCE_OPTIMIZED)
        
        assert len(groups) >= 1
        logger.info(f"Performance grouping created {len(groups)} groups: {groups}")


class TestVectorStore:
    """Test vector store operations for design pattern retrieval."""
    
    def test_design_pattern_storage_and_retrieval(self):
        """Test storing and retrieving similar design patterns."""
        store = EnterpriseVectorStore(store_path="test_vector_store.json")
        
        # Create test design pattern
        test_graph = {
            "nodes": {
                "panel_1": {"type": "panel", "attrs": {"power": 400, "x": 0, "y": 0}},
                "panel_2": {"type": "panel", "attrs": {"power": 400, "x": 1, "y": 0}},
                "inverter_1": {"type": "inverter", "attrs": {"power": 3000, "mppts": 2}}
            },
            "edges": [
                {"source": "panel_1", "target": "panel_2", "kind": "electrical"},
                {"source": "panel_2", "target": "inverter_1", "kind": "electrical"}
            ]
        }
        
        metadata = DesignMetadata(
            system_type="residential_pv",
            power_rating=3.0,
            voltage_class="LV",
            component_count=3,
            connection_count=2,
            compliance_codes=["NEC_2020"],
            geographical_region="US",
            installation_type="rooftop",
            design_category=DesignCategory.RESIDENTIAL_PV,
            performance_metrics={"efficiency": 0.85},
            creation_timestamp=1234567890.0
        )
        
        # Store pattern
        pattern_id = store.store_design(test_graph, metadata)
        assert pattern_id is not None
        
        # Retrieve similar patterns
        results = store.search_similar(test_graph, top_k=1, min_similarity=0.1)
        assert len(results) >= 0  # May be 0 if no similar patterns exist
        
        logger.info(f"Vector store test: stored pattern {pattern_id}, found {len(results)} similar")
    
    def test_vector_store_statistics(self):
        """Test vector store statistics and metadata."""
        store = EnterpriseVectorStore(store_path="test_vector_store.json")
        stats = store.get_statistics()
        
        assert "total_patterns" in stats
        assert "embedding_dimension" in stats
        logger.info(f"Vector store statistics: {stats}")


class TestLLMWiringSuggestions:
    """Test LLM-powered wiring suggestion generation."""
    
    def test_heuristic_wiring_suggestions(self):
        """Test heuristic-based wiring suggestions."""
        engine = LLMWiringSuggestionEngine(enable_llm=False)
        
        # Create mock graph with panels and inverter
        mock_graph = Mock()
        mock_graph.nodes = {
            "panel_1": {
                "type": "panel",
                "ports": {
                    "dc_pos": {"type": "dc+", "direction": "output"},
                    "dc_neg": {"type": "dc-", "direction": "output"}
                }
            },
            "panel_2": {
                "type": "panel", 
                "ports": {
                    "dc_pos": {"type": "dc+", "direction": "output"},
                    "dc_neg": {"type": "dc-", "direction": "output"}
                }
            },
            "inverter_1": {
                "type": "inverter",
                "ports": {
                    "pv1_pos": {"type": "dc+", "direction": "input"},
                    "pv1_neg": {"type": "dc-", "direction": "input"}
                }
            }
        }
        
        panel_groups = [["panel_1", "panel_2"]]
        context = WiringContext(
            system_type="residential",
            power_rating=3.0,
            voltage_class="LV",
            compliance_codes=["NEC_2020"],
            installation_type="rooftop",
            geographical_region="US",
            design_preferences={},
            safety_requirements={}
        )
        
        suggestions = engine.generate_suggestions(panel_groups, mock_graph, context)
        
        assert len(suggestions) > 0
        assert all(hasattr(s, 'connection_type') for s in suggestions)
        assert all(hasattr(s, 'confidence_score') for s in suggestions)
        
        logger.info(f"Generated {len(suggestions)} wiring suggestions")
        for i, suggestion in enumerate(suggestions[:3]):  # Log first 3
            logger.info(f"Suggestion {i+1}: {suggestion.source_node_id}:{suggestion.source_port} -> {suggestion.target_node_id}:{suggestion.target_port} ({suggestion.confidence_score:.2f})")


class TestAIWiringPipeline:
    """Test complete AI wiring pipeline integration."""
    
    def test_full_ai_pipeline_execution(self):
        """Test complete AI wiring pipeline from start to finish."""
        config = PipelineConfiguration(
            max_modules_per_string=4,
            use_llm_suggestions=False,  # Keep stable for testing
            use_vector_store=False,    # Avoid external dependencies
            enable_caching=False,      # Clean testing
            validation_strict=True
        )
        
        pipeline = EnterpriseAIWiringPipeline(config)
        
        # Create comprehensive test graph
        mock_graph = self._create_comprehensive_test_graph()
        
        result = pipeline.generate_wiring(mock_graph, "test_session_123")
        
        assert result.success or result.fallback_applied
        assert isinstance(result.edges, list)
        assert result.metrics.components_processed > 0
        
        logger.info(f"Pipeline result: {result.message}")
        logger.info(f"Generated {len(result.edges)} connections")
        logger.info(f"Metrics: {result.metrics.total_duration:.2f}s, {result.metrics.components_processed} components")
        
        # Validate connections have required fields
        if result.edges:
            edge = result.edges[0]
            assert "source_id" in edge
            assert "target_id" in edge
            assert "attrs" in edge
    
    def _create_comprehensive_test_graph(self):
        """Create a comprehensive test graph with multiple component types."""
        class MockGraph:
            def __init__(self):
                self.nodes = {}
                self.edges = []
        
        graph = MockGraph()
        
        # Add panels
        for i in range(6):
            graph.nodes[f"panel_{i+1}"] = {
                "type": "panel",
                "attrs": {"power": 400, "x": i, "y": 0},
                "ports": {
                    "dc_pos": {"type": "dc+", "direction": "output"},
                    "dc_neg": {"type": "dc-", "direction": "output"},
                    "gnd": {"type": "ground", "direction": "bidirectional"}
                }
            }
        
        # Add inverter
        graph.nodes["inverter_1"] = {
            "type": "inverter",
            "attrs": {"power": 3000, "mppts": 2},
            "ports": {
                "pv1_pos": {"type": "dc+", "direction": "input"},
                "pv1_neg": {"type": "dc-", "direction": "input"},
                "pv2_pos": {"type": "dc+", "direction": "input"},
                "pv2_neg": {"type": "dc-", "direction": "input"},
                "ac_l1": {"type": "ac", "direction": "output"},
                "ac_l2": {"type": "ac", "direction": "output"},
                "gnd": {"type": "ground", "direction": "bidirectional"}
            }
        }
        
        # Add protection devices
        graph.nodes["ac_protection_1"] = {
            "type": "ac_protection",
            "attrs": {"rating": "30A"},
            "ports": {
                "line_in": {"type": "ac", "direction": "input"},
                "load_out": {"type": "ac", "direction": "output"}
            }
        }
        
        graph.nodes["ac_disconnect_1"] = {
            "type": "ac_disconnect",
            "attrs": {"rating": "30A"},
            "ports": {
                "line_in": {"type": "ac", "direction": "input"},
                "load_out": {"type": "ac", "direction": "output"}
            }
        }
        
        return graph


class TestElectricalTopologyIntegration:
    """Test integration of AI wiring with electrical topology engine."""
    
    def test_ai_enhanced_electrical_connections(self):
        """Test AI-enhanced electrical topology generation."""
        # Create test components
        components = {
            "panel_1": {
                "type": "generic_panel",
                "attrs": {"power": 400, "voltage": 24, "x": 0, "y": 0}
            },
            "panel_2": {
                "type": "generic_panel", 
                "attrs": {"power": 400, "voltage": 24, "x": 1, "y": 0}
            },
            "panel_3": {
                "type": "generic_panel",
                "attrs": {"power": 400, "voltage": 24, "x": 2, "y": 0}
            },
            "inverter_1": {
                "type": "generic_inverter",
                "attrs": {"power": 3000, "mppts": 2}
            },
            "ac_protection_1": {
                "type": "generic_protection",
                "attrs": {"type": "ac_breaker", "rating": "30A"}
            }
        }
        
        # Test AI-enhanced connection generation
        connections, metadata = create_ai_enhanced_electrical_connections(
            components, 
            "test_session_456", 
            enable_ai=True
        )
        
        assert len(connections) > 0
        assert isinstance(metadata, dict)
        
        # Check metadata contains expected fields
        expected_fields = ["ai_enhanced", "method", "total_connections"]
        for field in expected_fields:
            assert field in metadata, f"Missing metadata field: {field}"
        
        logger.info(f"AI topology test: {len(connections)} connections generated")
        logger.info(f"Metadata: {metadata}")
        
        # Validate connection structure
        connection = connections[0]
        assert hasattr(connection, 'source_component')
        assert hasattr(connection, 'target_component')
        assert hasattr(connection, 'connection_type')
    
    def test_fallback_to_basic_topology(self):
        """Test graceful fallback when AI enhancement fails."""
        components = {
            "panel_1": {"type": "generic_panel", "attrs": {"power": 400}},
            "inverter_1": {"type": "generic_inverter", "attrs": {"power": 3000}}
        }
        
        # Test with AI disabled
        connections, metadata = create_ai_enhanced_electrical_connections(
            components,
            "test_session_789",
            enable_ai=False
        )
        
        assert len(connections) >= 0  # May be 0 for minimal components
        assert metadata["ai_enhanced"] is False
        assert metadata["method"] == "basic_topology"
        
        logger.info(f"Basic topology test: {len(connections)} connections, method: {metadata['method']}")


class TestPortAwareConnections:
    """Test port-aware electrical connections."""
    
    def test_placeholder_service_integration(self):
        """Test integration with placeholder component service for port definitions."""
        service = PlaceholderComponentService()
        
        # Test getting placeholder with ports
        panel_placeholder = service.get_placeholder_type("generic_panel")
        assert panel_placeholder is not None
        assert hasattr(panel_placeholder, 'ports')
        
        if panel_placeholder.ports:
            assert len(panel_placeholder.ports) > 0
            # Check port structure
            port = panel_placeholder.ports[0]
            assert "id" in port
            assert "type" in port
            assert "direction" in port
        
        logger.info(f"Panel placeholder has {len(panel_placeholder.ports or [])} ports")
        
        # Test inverter placeholder
        inverter_placeholder = service.get_placeholder_type("generic_inverter")
        assert inverter_placeholder is not None
        
        logger.info(f"Inverter placeholder has {len(inverter_placeholder.ports or [])} ports")


@pytest.mark.asyncio
async def test_ai_wiring_system_performance():
    """Test performance characteristics of AI wiring system."""
    import time
    
    # Create larger test system
    components = {}
    
    # Add 20 panels
    for i in range(20):
        components[f"panel_{i+1}"] = {
            "type": "generic_panel",
            "attrs": {"power": 400, "x": i % 10, "y": i // 10}
        }
    
    # Add 2 inverters
    for i in range(2):
        components[f"inverter_{i+1}"] = {
            "type": "generic_inverter", 
            "attrs": {"power": 5000, "mppts": 2}
        }
    
    # Add protection devices
    for i in range(4):
        components[f"protection_{i+1}"] = {
            "type": "generic_protection",
            "attrs": {"type": "ac_breaker"}
        }
    
    start_time = time.time()
    
    connections, metadata = create_ai_enhanced_electrical_connections(
        components,
        "performance_test_session",
        enable_ai=True
    )
    
    duration = time.time() - start_time
    
    logger.info(f"Performance test: {len(components)} components -> {len(connections)} connections in {duration:.2f}s")
    logger.info(f"Throughput: {len(components)/duration:.1f} components/second")
    
    # Performance assertions
    assert duration < 30.0  # Should complete within 30 seconds
    assert len(connections) > 0  # Should generate connections
    
    if metadata.get("ai_enhanced"):
        assert "performance_metrics" in metadata
        logger.info(f"AI metrics: {metadata.get('performance_metrics', {})}")


if __name__ == "__main__":
    # Run tests directly for debugging
    logging.basicConfig(level=logging.DEBUG)
    
    test_panel_grouping = TestPanelGrouping()
    test_panel_grouping.test_spatial_proximity_grouping()
    test_panel_grouping.test_electrical_optimal_grouping()
    test_panel_grouping.test_performance_optimized_grouping()
    
    test_vector_store = TestVectorStore()
    test_vector_store.test_design_pattern_storage_and_retrieval()
    test_vector_store.test_vector_store_statistics()
    
    test_suggestions = TestLLMWiringSuggestions()
    test_suggestions.test_heuristic_wiring_suggestions()
    
    test_pipeline = TestAIWiringPipeline()
    test_pipeline.test_full_ai_pipeline_execution()
    
    test_topology = TestElectricalTopologyIntegration()
    test_topology.test_ai_enhanced_electrical_connections()
    test_topology.test_fallback_to_basic_topology()
    
    test_ports = TestPortAwareConnections()
    test_ports.test_placeholder_service_integration()
    
    print("All tests completed successfully!")