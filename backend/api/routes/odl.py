"""ODL graph and session management API endpoints."""
from __future__ import annotations

from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends, Body
from pydantic import BaseModel

from backend.services import odl_graph_service
from backend.agents.planner_agent import PlannerAgent
from backend.agents.odl_domain_agents import PVDesignAgent
from backend.agents.component_selector_agent import ComponentSelectorAgent
from backend.agents.wiring_agent import WiringAgent
from backend.agents.structural_agent import StructuralAgent
from backend.schemas.odl import (
    ActOnTaskRequest, 
    GraphResponse,
    CreateSessionRequest,
    CreateSessionResponse,
    RequirementsUpdateRequest,
    RequirementsUpdateResponse,
    ComponentSelectionRequest,
    ComponentSelectionResponse,
    ODLTextResponse,
    PlaceholderAnalysisResponse,
    DesignRequirements
)
import uuid
import time


router = APIRouter(prefix="/odl", tags=["odl"])


@router.post("/sessions", response_model=CreateSessionResponse)
async def create_session(request: CreateSessionRequest = Body(...)) -> CreateSessionResponse:
    """Create a new ODL design session."""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Validate session_id format if provided
        session_id = request.session_id or str(uuid.uuid4())
        
        if request.session_id and (len(request.session_id) < 3 or len(request.session_id) > 100):
            raise HTTPException(
                status_code=400, 
                detail="Session ID must be between 3 and 100 characters"
            )
        
        # Create the graph
        logger.info(f"Creating ODL session: {session_id}")
        graph = await odl_graph_service.create_graph(session_id)

        if graph is None:
            logger.error(f"Failed to create graph for session: {session_id}")
            raise HTTPException(status_code=500, detail="Failed to create session")
        
        logger.info(f"Successfully created ODL session: {session_id}")
        return CreateSessionResponse(session_id=session_id)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error creating session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/sessions/{session_id}/plan")
async def get_session_plan(session_id: str, command: str = "design system") -> Dict[str, Any]:
    """Get the current planning state for a session."""
    import logging
    logger = logging.getLogger(__name__)
    
    # Validate inputs
    if not session_id or len(session_id.strip()) == 0:
        raise HTTPException(status_code=400, detail="Session ID is required")
    
    if len(session_id) > 100:
        raise HTTPException(status_code=400, detail="Session ID too long")
    
    if len(command) > 500:
        raise HTTPException(status_code=400, detail="Command too long (max 500 characters)")
    
    try:
        logger.info(f"Getting plan for session: {session_id}, command: {command}")
        planner = PlannerAgent()
        tasks = await planner.plan(session_id, command)
        
        if not isinstance(tasks, list):
            logger.error(f"Planner returned invalid tasks type: {type(tasks)}")
            raise HTTPException(status_code=500, detail="Invalid planner response")
        
        result = {
            "session_id": session_id,
            "tasks": tasks,
            "total_tasks": len(tasks),
            "completed_tasks": len([t for t in tasks if t.get("status") == "complete"]),
            "blocked_tasks": len([t for t in tasks if t.get("status") == "blocked"]),
            "pending_tasks": len([t for t in tasks if t.get("status") == "pending"])
        }
        
        logger.info(f"Plan generated for {session_id}: {len(tasks)} tasks")
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting plan for session {session_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate plan")


@router.post("/sessions/{session_id}/act", response_model=GraphResponse)
async def act_on_task(session_id: str, request: ActOnTaskRequest) -> GraphResponse:
    """Execute a task from the dynamic plan."""
    import logging
    logger = logging.getLogger(__name__)
    start_time = time.time()
    
    # Validate inputs
    if not session_id or len(session_id.strip()) == 0:
        raise HTTPException(status_code=400, detail="Session ID is required")
    
    if not request.task_id or len(request.task_id.strip()) == 0:
        raise HTTPException(status_code=400, detail="Task ID is required")
    
    if len(request.task_id) > 100:
        raise HTTPException(status_code=400, detail="Task ID too long")
    
    try:
        logger.info(f"Executing task {request.task_id} for session {session_id}")
        
        # Check for version conflicts
        if request.graph_version is not None:
            current_graph = await odl_graph_service.get_graph(session_id)
            if current_graph is not None:
                current_version = current_graph.graph.get("version", 1)
                
                if request.graph_version != current_version:
                    logger.warning(f"Version conflict detected: client={request.graph_version}, server={current_version}")
                    raise HTTPException(
                        status_code=409, 
                        detail=f"Version conflict: client has {request.graph_version}, server has {current_version}"
                    )
        
        # Route task to appropriate agent
        task_id = request.task_id.lower().strip()
        
        if task_id in ["gather_requirements", "generate_design", "refine_validate"]:
            agent = PVDesignAgent()
            result = await agent.execute(session_id, task_id, action=request.action)
            
        elif task_id == "generate_structural":
            agent = StructuralAgent()
            result = await agent.execute(session_id, task_id)
            
        elif task_id == "generate_wiring":
            agent = WiringAgent()
            result = await agent.execute(session_id, task_id)
            
        elif task_id == "populate_real_components":
            agent = ComponentSelectorAgent()
            result = await agent.execute(session_id, task_id)
            
        # Note: generate_battery and generate_monitoring would be implemented here
        # when those agents are created
            
        else:
            raise HTTPException(status_code=400, detail=f"Unknown task: {task_id}")
        
        # Apply patch if provided
        if result.get("patch"):
            try:
                await odl_graph_service.apply_patch(session_id, result["patch"])
                
                # Update version in result
                updated_graph = await odl_graph_service.get_graph(session_id)
                if updated_graph is not None:
                    result["version"] = updated_graph.graph.get("version", 1)
            except Exception as e:
                logger.warning(f"Error applying patch: {e}")
                # Continue with the response even if patch fails
        
        # Add execution time
        execution_time = int((time.time() - start_time) * 1000)
        result["execution_time_ms"] = execution_time
        
        # Add confidence scoring if not present
        if "card" in result and "confidence" not in result["card"]:
            try:
                from backend.agents.learning_agent import LearningAgent
                learning_agent = LearningAgent()
                confidence = await learning_agent.score_action(f"{task_id}_{result.get('status', 'unknown')}")
                result["card"]["confidence"] = confidence
            except Exception:
                result["card"]["confidence"] = 0.5  # Default confidence
        
        return GraphResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error executing task {request.task_id} for session {session_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Task execution failed")


@router.put("/sessions/{session_id}/requirements", response_model=RequirementsUpdateResponse)
async def update_requirements(
    session_id: str, 
    request: RequirementsUpdateRequest
) -> RequirementsUpdateResponse:
    """Update design requirements for a session."""
    try:
        # Convert request to dict for the service
        requirements_dict = request.requirements.model_dump(exclude_none=True)
        
        success = await odl_graph_service.update_requirements(session_id, requirements_dict)
        
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Get updated requirements
        graph = await odl_graph_service.get_graph(session_id)
        updated_requirements = DesignRequirements(**graph.graph.get("requirements", {}))
        
        # Determine which tasks might be affected
        affected_tasks = []
        if requirements_dict.get("target_power"):
            affected_tasks.extend(["generate_design", "generate_structural", "generate_wiring"])
        if requirements_dict.get("backup_hours"):
            affected_tasks.append("generate_battery")
        if requirements_dict.get("budget"):
            affected_tasks.extend(["generate_design", "populate_real_components"])
        
        return RequirementsUpdateResponse(
            success=True,
            message="Requirements updated successfully",
            updated_requirements=updated_requirements,
            affected_tasks=affected_tasks
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating requirements: {str(e)}")


@router.get("/sessions/{session_id}/text", response_model=ODLTextResponse)
async def get_odl_text(session_id: str) -> ODLTextResponse:
    """Get ODL text representation of the graph."""
    try:
        graph_data = await odl_graph_service.get_graph_with_text(session_id)
        if graph_data is None:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return ODLTextResponse(
            text=graph_data["text"],
            version=graph_data["version"],
            last_updated=graph_data.get("last_updated"),
            node_count=graph_data["node_count"],
            edge_count=graph_data["edge_count"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting ODL text: {str(e)}")


@router.get("/sessions/{session_id}/analysis", response_model=PlaceholderAnalysisResponse)
async def analyze_placeholders(session_id: str) -> PlaceholderAnalysisResponse:
    """Get placeholder analysis for the session."""
    try:
        graph = await odl_graph_service.get_graph(session_id)
        if graph is None:
            raise HTTPException(status_code=404, detail="Session not found")
        
        analysis = odl_graph_service.analyze_placeholder_status(graph)
        
        # TODO: Enhance with actual component availability checking
        # For now, return the basic analysis
        return PlaceholderAnalysisResponse(**analysis)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing placeholders: {str(e)}")


@router.post("/sessions/{session_id}/select-component", response_model=ComponentSelectionResponse)
async def select_component(
    session_id: str,
    request: ComponentSelectionRequest
) -> ComponentSelectionResponse:
    """Replace a placeholder component with a real component."""
    try:
        component_selector = ComponentSelectorAgent()
        
        result = await component_selector.replace_placeholder(
            session_id, request.placeholder_id, request.component
        )
        
        # Apply the patch if one was generated
        if result.get("patch"):
            await odl_graph_service.apply_patch(session_id, result["patch"])
        
        # Get updated design summary
        graph = await odl_graph_service.get_graph(session_id)
        design_summary = odl_graph_service.describe_graph(graph) if graph is not None else "No design"
        
        return ComponentSelectionResponse(
            success=result.get("status") == "complete",
            message=result.get("card", {}).get("body", "Component selected"),
            replaced_nodes=[request.placeholder_id] if result.get("status") == "complete" else [],
            patch=result.get("patch", {}),
            updated_design_summary=design_summary
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error selecting component: {str(e)}")


@router.get("/sessions/{session_id}/versions")
async def list_versions(session_id: str) -> Dict[str, Any]:
    """List all versions for a session."""
    try:
        versions = await odl_graph_service.list_versions(session_id)
        return {
            "session_id": session_id,
            "versions": versions,
            "total_versions": len(versions)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing versions: {str(e)}")


@router.post("/sessions/{session_id}/revert")
async def revert_version(session_id: str, target_version: int) -> Dict[str, Any]:
    """Revert to a specific version."""
    try:
        success = await odl_graph_service.revert_to_version(session_id, target_version)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to revert to version")
        
        # Get updated graph info
        graph = await odl_graph_service.get_graph(session_id)
        current_version = graph.graph.get("version", 1) if graph is not None else 1
        graph_summary = odl_graph_service.describe_graph(graph) if graph is not None else "Empty design"
        
        return {
            "success": True,
            "message": f"Reverted to version {target_version}",
            "current_version": current_version,
            "graph_summary": graph_summary
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reverting version: {str(e)}")


@router.get("/agents")
async def list_agents() -> Dict[str, Any]:
    """List available agents and their supported tasks."""
    return {
        "agents": {
            "PVDesignAgent": {
                "tasks": ["gather_requirements", "generate_design", "refine_validate"],
                "description": "Photovoltaic system design agent"
            },
            "ComponentSelectorAgent": {
                "tasks": ["populate_real_components"],
                "description": "Component selection and placeholder replacement"
            },
            "StructuralAgent": {
                "tasks": ["generate_structural"],
                "description": "Structural design and mounting systems"
            },
            "WiringAgent": {
                "tasks": ["generate_wiring"],
                "description": "Electrical wiring and protection devices"
            },
            "PlannerAgent": {
                "tasks": ["plan"],
                "description": "Dynamic task planning and orchestration"
            }
        },
        "task_types": [
            "gather_requirements",
            "generate_design", 
            "generate_structural",
            "generate_wiring",
            "populate_real_components",
            "refine_validate"
        ]
    }
 
# --- ODL round-trip authoritative update ------------------------------------
from pydantic import BaseModel
from typing import Literal
from backend.services.odl_parser import parse_odl_text
from backend.services.odl_sync import rebuild_odl_for_session

try:  # pragma: no cover - optional repos
    from backend.repositories.components import ComponentRepo  # type: ignore
    from backend.repositories.links import LinkRepo  # type: ignore
    from backend.services.snapshot_provider import get_current_snapshot  # type: ignore
except Exception:  # pragma: no cover
    ComponentRepo = None  # type: ignore
    LinkRepo = None  # type: ignore
    get_current_snapshot = None  # type: ignore


class OdlUpdate(BaseModel):
    session_id: str
    odl_text: str
    mode: Literal["merge", "replace"] = "merge"


@router.post("/set")
async def set_odl(update: OdlUpdate):
    if get_current_snapshot is None or ComponentRepo is None or LinkRepo is None:
        raise HTTPException(status_code=500, detail="Repositories unavailable")
    snap = await get_current_snapshot(session_id=update.session_id)  # type: ignore
    if snap is None:
        raise HTTPException(status_code=404, detail="Session not found")
    desired = parse_odl_text(update.odl_text)
    comp_repo = ComponentRepo()  # type: ignore
    link_repo = LinkRepo()  # type: ignore
    for dc in desired.components:
        cur = next((c for c in snap.components if c.id == dc.id), None)
        if cur:
            for lay, pos in (dc.layout or {}).items():
                cur.layout = {**(cur.layout or {}), lay: {"x": pos["x"], "y": pos["y"]}}
                cur.locked_in_layers = {**(cur.locked_in_layers or {}), lay: True}
            await comp_repo.save_component(cur)  # type: ignore
        elif update.mode == "replace":
            await comp_repo.create_component_for_session(update.session_id, dc)  # type: ignore
    for dl in desired.links:
        cur = next((l for l in snap.links if l.source_id == dl.source_id and l.target_id == dl.target_id), None)
        if cur:
            for lay, pts in (dl.path_by_layer or {}).items():
                cur.path_by_layer[lay] = pts
            await link_repo.save_link(cur)  # type: ignore
        else:
            await link_repo.create_link_for_session(update.session_id, dl)  # type: ignore
    await rebuild_odl_for_session(update.session_id)
    return {"status": "ok"}
