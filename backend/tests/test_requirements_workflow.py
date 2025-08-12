import os
import sys
from pathlib import Path
from uuid import uuid4

import pytest
# No web components needed for planner test
import importlib.util

os.environ.setdefault("OPENAI_API_KEY", "test")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test.db")

sys.path.append(str(Path(__file__).resolve().parents[2]))

from backend.services import odl_graph_service  # noqa: E402

spec_planner = importlib.util.spec_from_file_location(
    "planner_agent",
    Path(__file__).resolve().parents[1] / "agents" / "planner_agent.py",
)
planner_mod = importlib.util.module_from_spec(spec_planner)
assert spec_planner.loader is not None
spec_planner.loader.exec_module(planner_mod)  # type: ignore
PlannerAgent = planner_mod.PlannerAgent



@pytest.mark.asyncio
async def test_generate_design_blocked_until_ready():
    session_id = f"plan-{uuid4()}"
    await odl_graph_service.create_graph(session_id)
    planner = PlannerAgent()

    tasks = await planner.plan(session_id, "design system")
    gen_task = next(t for t in tasks if t["id"] == "generate_design")
    assert gen_task["status"] == "blocked"

    graph = await odl_graph_service.get_graph(session_id)
    graph.graph["requirements"] = {"target_power": 5000, "roof_area": 20, "budget": 10000}
    await odl_graph_service.save_graph(session_id, graph)

    await planner.component_db_service.ingest("panel", "P1", {"power": 400, "area": 2, "price": 250})
    await planner.component_db_service.ingest("inverter", "I1", {"capacity": 5000, "price": 1000})

    tasks = await planner.plan(session_id, "design system")
    assert not any(t["id"] == "gather_requirements" for t in tasks)
    gen_task = next(t for t in tasks if t["id"] == "generate_design")
    assert gen_task["status"] == "pending"
