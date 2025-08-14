import os
import sys
from pathlib import Path
from uuid import uuid4

import pytest


os.environ.setdefault("OPENAI_API_KEY", "test")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test.db")

sys.path.append(str(Path(__file__).resolve().parents[2]))

from backend.services import odl_graph_service  # noqa: E402
from backend.agents.planner_agent import PlannerAgent  # noqa: E402


@pytest.mark.asyncio
async def test_accept_placeholder_design_generates_follow_up_tasks():
    session_id = f"session-{uuid4()}"
    await odl_graph_service.create_graph(session_id)

    graph = await odl_graph_service.get_graph(session_id)
    assert graph is not None

    # Set requirements so planner knows a design exists
    graph.graph["requirements"] = {
        "target_power": 5000,
        "roof_area": 20,
        "budget": 10000,
    }

    # Add placeholder panel and inverter connected with provisional edge
    graph.add_node("placeholder_panel_0", type="generic_panel", placeholder=True)
    graph.add_node("placeholder_inverter_0", type="generic_inverter", placeholder=True)
    graph.add_edge(
        "placeholder_panel_0",
        "placeholder_inverter_0",
        provisional=True,
        type="electrical",
        connection_type="electrical",
    )

    await odl_graph_service.save_graph(session_id, graph)

    planner = PlannerAgent()
    tasks = await planner.plan(session_id, "accept_placeholder_design")

    task_ids = [t["id"] for t in tasks]
    assert "generate_structural" in task_ids
    assert "generate_wiring" in task_ids
    assert task_ids[-1] == "refine_validate"

    # The provisional edge should now be confirmed
    updated = await odl_graph_service.get_graph(session_id)
    assert updated is not None
    assert (
        updated.edges["placeholder_panel_0", "placeholder_inverter_0"].get("provisional")
        is False
    )

