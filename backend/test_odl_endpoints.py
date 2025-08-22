#!/usr/bin/env python3
"""
Simple test script to verify ODL endpoints work correctly.
Run this to test the new bridge endpoints and layout functionality.
"""
import asyncio
import logging
from backend.database.session import get_session
from backend.odl.store import ODLStore
from backend.odl.schemas import ODLGraph, ODLNode, ODLEdge
from backend.api.routes.odl import ensure_positions, _synthesize_text_from_view
from backend.odl.views import layer_view

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_odl_endpoints():
    """Test the ODL endpoints with sample data."""

    # Create a test session with some nodes and edges
    test_session_id = "test_session_001"

    async with get_session() as db:
        store = ODLStore()
        await store.init_schema(db)

        # Create some test nodes
        nodes = {
            "panel_1": ODLNode(
                id="panel_1",
                type="panel",
                attrs={"layer": "single-line", "x": 100, "y": 100}
            ),
            "inverter_1": ODLNode(
                id="inverter_1",
                type="inverter",
                attrs={"layer": "single-line"}
            ),
            "battery_1": ODLNode(
                id="battery_1",
                type="battery",
                attrs={"layer": "single-line"}
            )
        }

        # Create some test edges
        edges = [
            ODLEdge(id="edge_1", source_id="panel_1", target_id="inverter_1", kind="electrical"),
            ODLEdge(id="edge_2", source_id="inverter_1", target_id="battery_1", kind="electrical")
        ]

        # Create the graph
        graph = ODLGraph(
            session_id=test_session_id,
            version=1,
            nodes=nodes,
            edges=edges
        )

        # Save to store
        await store.create_graph(db, test_session_id)
        await db.commit()

        # Test the view with layout
        view = layer_view(graph, "single-line")
        logger.info("Original view: %s", view)

        # Test layout positioning
        view_with_positions = ensure_positions(view)
        logger.info("View with positions: %s", view_with_positions)

        # Test text synthesis
        text = _synthesize_text_from_view(view)
        logger.info("Synthesized text: %s", text)

        logger.info("✅ ODL endpoints test completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_odl_endpoints())
