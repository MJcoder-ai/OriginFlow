import asyncio

from backend.planner.long_planner import LongPlanner


async def _run():
    planner = LongPlanner()
    card = await planner.plan(session_id="s1", text="design a 3 kW system", layer="single-line")
    return card


def test_plan_tasks():
    card = asyncio.run(_run())
    plan = card.plan
    assert plan.session_id == "s1"
    assert plan.layer == "single-line"
    assert len(plan.tasks) >= 5
    assert plan.tasks[0].id == "select_equipment"
