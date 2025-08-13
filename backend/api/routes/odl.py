"""ODL graph and planning routes."""
from __future__ import annotations

from typing import List, Dict, Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Body

from backend.schemas.ai import AiCommandRequest, PlanTask
from backend.schemas.odl import (
    ActOnTaskRequest, 
    CreateSessionResponse, 
    CreateSessionRequest, 
    GraphResponse,
    RequirementsStatusResponse,
    TaskExecutionResponse,
    VersionDiffResponse,
    VersionRevertRequest,
    VersionRevertResponse
)
from backend.agents.planner_agent import PlannerAgent
from backend.agents.registry import registry
from backend.services import odl_graph_service
from backend.services.component_db_service import ComponentDBService

router = APIRouter(prefix="/odl", tags=["odl"])

planner_agent = PlannerAgent()
component_db_service = ComponentDBService()


@router.post("/sessions", response_model=CreateSessionResponse)
async def create_session(cmd: CreateSessionRequest | None = None) -> CreateSessionResponse:
    """Create a new design session and initialise its graph.

    Accepts an optional body; when a `session_id` is provided by the
    frontend, reuse it to allow stable sessions across refreshes.
    """
    # Prefer client-provided id when present
    provided_session_id = None
    provided_session_id = getattr(cmd, "session_id", None) if cmd else None
    session_id = provided_session_id or str(uuid4())
    await odl_graph_service.create_graph(session_id)
    return CreateSessionResponse(session_id=session_id)


@router.get("/requirements/{session_id}/status", response_model=RequirementsStatusResponse)
async def get_requirements_status(session_id: str) -> RequirementsStatusResponse:
    """
    Return the status of requirements and components for a session.
    
    This endpoint checks which requirement fields are missing (target_power, 
    roof_area, budget) and whether necessary components (panels, inverters) 
    exist in the component database. The frontend can use this information 
    to decide when to show requirement forms or component upload widgets.
    """
    # Get the current graph
    graph = await odl_graph_service.get_graph(session_id)
    if not graph:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    # Check requirements completeness
    requirements = graph.graph.get("requirements", {})
    required_fields = ["target_power", "roof_area", "budget"]
    missing_requirements = [field for field in required_fields if not requirements.get(field)]
    requirements_complete = len(missing_requirements) == 0
    
    # Check component availability
    panel_available = await component_db_service.exists(category="panel")
    inverter_available = await component_db_service.exists(category="inverter")
    missing_components = []
    if not panel_available:
        missing_components.append("panel")
    if not inverter_available:
        missing_components.append("inverter")
    components_available = len(missing_components) == 0
    
    # Determine if we can proceed with design generation
    can_proceed = requirements_complete and components_available
    
    # Get graph summary using our new helper
    graph_summary = odl_graph_service.describe_graph(graph)
    
    return RequirementsStatusResponse(
        missing_requirements=missing_requirements,
        missing_components=missing_components,
        requirements_complete=requirements_complete,
        components_available=components_available,
        can_proceed=can_proceed,
        graph_summary=graph_summary
    )


@router.post("/{session_id}/plan", response_model=List[PlanTask])
async def get_plan(session_id: str, cmd: AiCommandRequest) -> List[PlanTask]:
    """
    Return a dynamic list of tasks for this session.  The request may
    include partial requirements (target power, roof area, budget) which are
    saved on the graph.  The planner then inspects the graph and user
    inputs to determine which tasks are needed.
    """
    requirements = getattr(cmd, "requirements", None)
    if requirements:
        graph = await odl_graph_service.get_graph(session_id)
        graph.graph.setdefault("requirements", {}).update(requirements)
        await odl_graph_service.save_graph(session_id, graph)
    tasks = await planner_agent.plan(session_id, cmd.command, requirements=requirements)
    return [PlanTask(**t) for t in tasks]


@router.post("/{session_id}/act", response_model=GraphResponse)
async def act_on_task(session_id: str, req: ActOnTaskRequest) -> GraphResponse:
    """Execute a task on the current graph."""
    task_id = req.task_id.lower().strip()
    agent = registry.get_agent(task_id)
    if agent:
        result = await agent.execute(session_id, task_id)
    else:
        result = {
            "card": {"title": "Unknown task", "body": f"Task {req.task_id} not supported."},
            "patch": None,
            "status": "error",
        }
    patch = result.get("patch")
    if patch:
        graph = await odl_graph_service.get_graph(session_id)
        patch_with_version = dict(patch)
        # Prefer client-observed version for optimistic concurrency if provided
        client_version = req.graph_version
        patch_with_version["version"] = (
            client_version if client_version is not None else graph.graph.get("version", 0)
        )
        success, error = await odl_graph_service.apply_patch(session_id, patch_with_version)
        if not success:
            raise HTTPException(status_code=409, detail=error)
        # Load updated version to return
        graph = await odl_graph_service.get_graph(session_id)
        current_version = graph.graph.get("version", None)
    else:
        graph = await odl_graph_service.get_graph(session_id)
        current_version = graph.graph.get("version", None)
    return GraphResponse(
        card=result["card"],
        patch=patch,
        status=result.get("status", "pending"),
        version=current_version,
    )


@router.post("/{session_id}/act-enhanced", response_model=TaskExecutionResponse)
async def act_on_task_enhanced(session_id: str, req: ActOnTaskRequest) -> TaskExecutionResponse:
    """
    Execute a task on the current graph with enhanced status tracking.
    
    This enhanced version provides:
    - Automatic plan refresh after task execution
    - Next recommended task suggestion
    - Execution time tracking
    - Updated task list with current statuses
    """
    import time
    start_time = time.time()
    
    task_id = req.task_id.lower().strip()
    agent = registry.get_agent(task_id)
    
    # Execute the task (same as original)
    if agent:
        result = await agent.execute(session_id, task_id)
    else:
        result = {
            "card": {"title": "Unknown task", "body": f"Task {req.task_id} not supported."},
            "patch": None,
            "status": "error",
        }
    
    # Apply patch if provided (same as original)
    patch = result.get("patch")
    if patch:
        graph = await odl_graph_service.get_graph(session_id)
        patch_with_version = dict(patch)
        client_version = req.graph_version
        patch_with_version["version"] = (
            client_version if client_version is not None else graph.graph.get("version", 0)
        )
        success, error = await odl_graph_service.apply_patch(session_id, patch_with_version)
        if not success:
            raise HTTPException(status_code=409, detail=error)
        # Load updated version to return
        graph = await odl_graph_service.get_graph(session_id)
        current_version = graph.graph.get("version", None)
    else:
        graph = await odl_graph_service.get_graph(session_id)
        current_version = graph.graph.get("version", None)
    
    # Enhanced features: Refresh plan and suggest next task
    updated_tasks = None
    next_recommended_task = None
    
    if result.get("status") == "complete":
        try:
            # Refresh the plan after successful task completion
            updated_tasks_raw = await planner_agent.plan(
                session_id, "design system", requirements=graph.graph.get("requirements", {})
            )
            updated_tasks = updated_tasks_raw
            
            # Find next pending task as recommendation
            for task in updated_tasks_raw:
                if task.get("status") == "pending":
                    next_recommended_task = task.get("id")
                    break
                    
        except Exception as e:
            # Don't fail the whole request if plan refresh fails
            print(f"Plan refresh failed: {e}")
    
    # Calculate execution time
    execution_time_ms = int((time.time() - start_time) * 1000)
    
    return TaskExecutionResponse(
        card=result["card"],
        patch=patch,
        status=result.get("status", "pending"),
        version=current_version,
        updated_tasks=updated_tasks,
        next_recommended_task=next_recommended_task,
        execution_time_ms=execution_time_ms
    )


@router.get("/versions/{session_id}/diff", response_model=VersionDiffResponse)
async def get_version_diff(
    session_id: str, 
    from_version: int, 
    to_version: int
) -> VersionDiffResponse:
    """
    Get the differences between two versions of a session graph.
    
    This endpoint returns a summary of changes made between two versions,
    useful for undo/redo functionality and change tracking.
    
    Args:
        session_id: Session identifier
        from_version: Starting version number
        to_version: Ending version number
        
    Returns:
        Detailed diff with change summary
    """
    # Validate session exists
    graph = await odl_graph_service.get_graph(session_id)
    if not graph:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    current_version = graph.graph.get("version", 0)
    
    # Validate version numbers
    if from_version < 0 or to_version < 0:
        raise HTTPException(status_code=400, detail="Version numbers must be non-negative")
    
    if to_version > current_version:
        raise HTTPException(status_code=400, detail=f"to_version {to_version} exceeds current version {current_version}")
    
    # Get patch differences
    patches = odl_graph_service.get_patch_diff(session_id, from_version, to_version)
    
    if patches is None:
        changes = []
        summary = f"No changes between versions {from_version} and {to_version}"
    else:
        changes = patches
        
        # Generate summary
        total_additions = sum(
            len(patch.get("add_nodes", [])) + len(patch.get("add_edges", []))
            for patch in patches
        )
        total_removals = sum(
            len(patch.get("remove_nodes", [])) + len(patch.get("remove_edges", []))
            for patch in patches
        )
        
        summary_parts = []
        if total_additions > 0:
            summary_parts.append(f"{total_additions} addition{'s' if total_additions != 1 else ''}")
        if total_removals > 0:
            summary_parts.append(f"{total_removals} removal{'s' if total_removals != 1 else ''}")
        
        if summary_parts:
            summary = f"Changes from v{from_version} to v{to_version}: {', '.join(summary_parts)}"
        else:
            summary = f"No net changes between versions {from_version} and {to_version}"
    
    return VersionDiffResponse(
        from_version=from_version,
        to_version=to_version,
        changes=changes,
        summary=summary
    )


@router.post("/versions/{session_id}/revert", response_model=VersionRevertResponse)
async def revert_to_version(
    session_id: str, 
    req: VersionRevertRequest
) -> VersionRevertResponse:
    """
    Revert a session graph to a previous version.
    
    This endpoint implements the undo functionality by reverting the graph
    to a specified earlier version. All patches after the target version
    are discarded.
    
    Args:
        session_id: Session identifier
        req: Revert request with target version
        
    Returns:
        Success status and updated graph information
    """
    target_version = req.target_version
    
    # Validate session exists
    graph = await odl_graph_service.get_graph(session_id)
    if not graph:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    current_version = graph.graph.get("version", 0)
    
    # Validate target version
    if target_version < 0:
        raise HTTPException(status_code=400, detail="Target version must be non-negative")
    
    if target_version > current_version:
        raise HTTPException(status_code=400, detail=f"Target version {target_version} exceeds current version {current_version}")
    
    if target_version == current_version:
        return VersionRevertResponse(
            success=True,
            message=f"Already at version {target_version}",
            current_version=current_version,
            graph_summary=odl_graph_service.describe_graph(graph)
        )
    
    # Perform the revert
    success = await odl_graph_service.revert_to_version(session_id, target_version)
    
    if not success:
        raise HTTPException(status_code=500, detail=f"Failed to revert to version {target_version}")
    
    # Get updated graph for summary
    updated_graph = await odl_graph_service.get_graph(session_id)
    updated_version = updated_graph.graph.get("version", 0)
    graph_summary = odl_graph_service.describe_graph(updated_graph)
    
    return VersionRevertResponse(
        success=True,
        message=f"Successfully reverted from version {current_version} to {updated_version}",
        current_version=updated_version,
        graph_summary=graph_summary
    )


@router.get("/registry/tasks")
async def get_task_registry() -> Dict[str, Any]:
    """
    Get information about all registered tasks and agents.
    
    This endpoint provides comprehensive documentation about:
    - Available tasks and their descriptions
    - Domain categorization
    - Task dependencies and prerequisites
    - Agent capabilities
    
    Useful for frontend documentation and dynamic UI generation.
    """
    from backend.agents.registry import registry
    
    tasks = {}
    
    # Get all task information
    for task_id in registry.available_tasks():
        task_info = registry.get_task_info(task_id)
        tasks[task_id] = task_info
    
    # Add domain and dependency information
    domains = registry.get_all_domains()
    dependency_map = registry.get_dependency_map()
    
    return {
        "tasks": tasks,
        "domains": domains,
        "dependencies": dependency_map,
        "task_count": len(tasks),
        "domain_breakdown": {
            domain: registry.get_tasks_by_domain(domain) 
            for domain in domains
        }
    }


@router.post("/registry/validate-sequence")
async def validate_task_sequence(
    task_sequence: List[str] = Body(..., embed=False)
) -> Dict[str, Any]:
    """
    Validate a proposed task sequence for dependency violations.
    
    This endpoint helps validate task execution order and identifies
    any missing prerequisites or circular dependencies.
    
    Args:
        task_sequence: Ordered list of task IDs to validate
        
    Returns:
        Validation results with any errors or warnings
    """
    from backend.agents.registry import registry
    
    errors = registry.validate_task_sequence(task_sequence)
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "task_sequence": task_sequence,
        "suggestion": "Fix dependency violations before executing tasks" if errors else "Task sequence is valid"
    }
