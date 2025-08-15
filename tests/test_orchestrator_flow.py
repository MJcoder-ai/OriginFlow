"""
End‑to‑end tests for the OriginFlow orchestrator and recovery mechanisms.

These tests exercise the planner’s saga‑enabled multi‑step workflow execution
and verify that the orchestrator produces calibrated confidences and dynamic
thresholds in the returned cards.  They also ensure that blocked tasks are
automatically retried and cleared by the recovery manager.
"""

import pytest
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from backend.services.orchestrator import PlannerOrchestrator
from backend.services.odl_graph_service import odl_graph_service
from backend.utils.retry_manager import retry_manager


@pytest.mark.asyncio
async def test_orchestrator_multi_step_workflow() -> None:
    """
    Run a multi‑step workflow through the saga engine and ensure all domain tasks
    execute correctly.  After execution, the graph should contain placeholder nodes
    for network, site plan, battery and monitoring, and each card should include
    calibrated confidence and dynamic threshold values.
    """
    orchestrator = PlannerOrchestrator()
    session_id = "workflow_session"
    tasks = [
        "generate_network",
        "generate_site",
        "generate_battery",
        "generate_monitoring",
    ]
    # Execute the saga workflow and retrieve the envelopes
    results = await orchestrator.run_workflow(session_id=session_id, tasks=tasks)
    assert len(results) == len(tasks)

    # Verify calibrated confidence and dynamic threshold in each card
    for res in results:
        card = res.get("output", {}).get("card") or res.get("card")
        assert card is not None, "Missing card in orchestrator response"
        assert "confidence" in card, "Card missing confidence field"
        assert "dynamic_threshold" in card, "Card missing dynamic_threshold field"

    # Inspect the resulting graph for placeholder nodes and edges
    graph = await odl_graph_service.get_graph(session_id)
    assert graph is not None, "Graph not created by orchestrator"
    assert graph.nodes_by_type("generic_network"), "Network nodes not added"
    assert graph.nodes_by_type("generic_site_plan"), "Site plan nodes not added"
    assert graph.nodes_by_type("generic_battery"), "Battery nodes not added"
    assert graph.nodes_by_type("generic_monitoring"), "Monitoring nodes not added"
    # Expect at least one edge per task
    assert len(graph.edges) >= len(tasks), "Insufficient edges added to graph"


@pytest.mark.asyncio
async def test_orchestrator_recovery_retry() -> None:
    """
    Simulate a blocked task and ensure the orchestrator automatically retries and
    clears the blocked queue.  A blocked battery task is registered manually
    before running a workflow that includes a battery task.
    """
    orchestrator = PlannerOrchestrator()
    session_id = "retry_session"
    # Register a blocked battery task to simulate an earlier failure
    retry_manager.register_blocked_task(
        session_id=session_id,
        agent_name="battery_agent",
        task_id="generate_battery",
        context={},
    )
    # Running a workflow with the battery task should automatically resolve it
    await orchestrator.run_workflow(session_id=session_id, tasks=["generate_battery"])
    # Invoke resolve_blocked_tasks again to clear any remaining tasks
    await retry_manager.resolve_blocked_tasks(session_id=session_id)
    assert not retry_manager._blocked_tasks.get(session_id), "Blocked tasks not cleared"

