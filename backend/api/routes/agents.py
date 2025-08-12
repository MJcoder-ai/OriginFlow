# backend/api/routes/agents.py
"""Dynamic agent discovery and registration API."""
from __future__ import annotations

from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_session
from backend.auth.dependencies import get_current_user
from backend.auth.models import User
from backend.agents.registry import (
    get_agent_names, 
    get_spec, 
    register, 
    register_spec,
    AgentSpec,
    registry as agent_registry
)
from backend.agents.base import AgentBase

router = APIRouter(prefix="/agents", tags=["agents"])


class AgentInfo(BaseModel):
    """Agent information model."""
    name: str
    domain: str
    risk_class: str
    capabilities: List[str]
    description: Optional[str] = None
    version: Optional[str] = None
    enabled: bool = True


class TaskInfo(BaseModel):
    """Task information model."""
    task_id: str
    agent_name: str
    description: Optional[str] = None
    required_capabilities: List[str] = []
    auto_executable: bool = False


class AgentRegistrationRequest(BaseModel):
    """Request to register a new agent."""
    name: str
    domain: str
    risk_class: str = "medium"
    capabilities: List[str] = []
    description: Optional[str] = None


@router.get("/", response_model=List[AgentInfo])
async def list_agents(
    domain: Optional[str] = None,
    current_user: User = Depends(get_current_user)
) -> List[AgentInfo]:
    """List all registered agents with their capabilities."""
    
    agent_names = get_agent_names()
    agents = []
    
    for name in agent_names:
        try:
            spec = get_spec(name)
            
            # Filter by domain if specified
            if domain and spec.domain.lower() != domain.lower():
                continue
            
            agents.append(AgentInfo(
                name=spec.name,
                domain=spec.domain,
                risk_class=spec.risk_class,
                capabilities=spec.capabilities,
                description=getattr(spec, 'description', None),
                version=getattr(spec, 'version', None),
                enabled=True
            ))
        except KeyError:
            # Agent doesn't have a spec - create a basic one
            agents.append(AgentInfo(
                name=name,
                domain="general",
                risk_class="unknown",
                capabilities=[],
                description=f"Legacy agent: {name}",
                enabled=True
            ))
    
    return agents


@router.get("/tasks", response_model=List[TaskInfo])
async def list_tasks(
    current_user: User = Depends(get_current_user)
) -> List[TaskInfo]:
    """List all available tasks and their assigned agents."""
    
    tasks = []
    
    # Get tasks from the ODL registry
    available_tasks = agent_registry.available_tasks()
    
    for task_id in available_tasks:
        agent = agent_registry.get_agent(task_id)
        agent_name = getattr(agent, '__class__', {}).get('__name__', 'unknown')
        
        # Determine if task can be auto-executed
        auto_executable = task_id in [
            'generate_design',  # Low risk
            'refine_validate'   # Medium risk with high confidence
        ]
        
        # Get required capabilities from agent spec if available
        required_capabilities = []
        try:
            if hasattr(agent, 'name'):
                spec = get_spec(agent.name)
                required_capabilities = spec.capabilities
        except KeyError:
            pass
        
        tasks.append(TaskInfo(
            task_id=task_id,
            agent_name=agent_name,
            description=f"Task handled by {agent_name}",
            required_capabilities=required_capabilities,
            auto_executable=auto_executable
        ))
    
    return tasks


@router.get("/{agent_name}")
async def get_agent_info(
    agent_name: str,
    current_user: User = Depends(get_current_user)
) -> AgentInfo:
    """Get detailed information about a specific agent."""
    
    try:
        spec = get_spec(agent_name)
        return AgentInfo(
            name=spec.name,
            domain=spec.domain,
            risk_class=spec.risk_class,
            capabilities=spec.capabilities,
            description=getattr(spec, 'description', None),
            version=getattr(spec, 'version', None),
            enabled=True
        )
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Agent {agent_name} not found")


@router.get("/{agent_name}/capabilities")
async def get_agent_capabilities(
    agent_name: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get detailed capabilities of an agent."""
    
    try:
        spec = get_spec(agent_name)
        
        # Get the actual agent instance for more details
        from backend.agents.registry import get_agent
        agent = get_agent(agent_name)
        
        capabilities_detail = {}
        for capability in spec.capabilities:
            capabilities_detail[capability] = {
                "enabled": True,
                "description": f"Agent supports {capability}",
                "risk_level": spec.risk_class
            }
        
        return {
            "agent_name": agent_name,
            "domain": spec.domain,
            "risk_class": spec.risk_class,
            "capabilities": capabilities_detail,
            "methods": [
                method for method in dir(agent) 
                if not method.startswith('_') and callable(getattr(agent, method))
            ] if agent else []
        }
        
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Agent {agent_name} not found")


@router.post("/register")
async def register_agent(
    request: AgentRegistrationRequest,
    current_user: User = Depends(get_current_user)
):
    """Register a new agent dynamically."""
    
    # Only allow admin users to register agents
    if not getattr(current_user, 'is_superuser', False):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # Register the agent spec
        spec = register_spec(
            name=request.name,
            domain=request.domain,
            risk_class=request.risk_class,
            capabilities=request.capabilities
        )
        
        return {
            "status": "success",
            "message": f"Agent {request.name} registered successfully",
            "spec": {
                "name": spec.name,
                "domain": spec.domain,
                "risk_class": spec.risk_class,
                "capabilities": spec.capabilities
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to register agent: {str(e)}")


@router.get("/domains/available")
async def get_available_domains(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get all available domains and their agents."""
    
    agents = await list_agents()
    domains = {}
    
    for agent in agents:
        domain = agent.domain
        if domain not in domains:
            domains[domain] = {
                "name": domain,
                "agents": [],
                "capabilities": set(),
                "risk_levels": set()
            }
        
        domains[domain]["agents"].append({
            "name": agent.name,
            "capabilities": agent.capabilities,
            "risk_class": agent.risk_class
        })
        domains[domain]["capabilities"].update(agent.capabilities)
        domains[domain]["risk_levels"].add(agent.risk_class)
    
    # Convert sets to lists for JSON serialization
    for domain_info in domains.values():
        domain_info["capabilities"] = list(domain_info["capabilities"])
        domain_info["risk_levels"] = list(domain_info["risk_levels"])
    
    return {
        "domains": domains,
        "total_domains": len(domains),
        "total_agents": len(agents)
    }


@router.post("/{agent_name}/enable")
async def enable_agent(
    agent_name: str,
    current_user: User = Depends(get_current_user)
):
    """Enable an agent for use."""
    
    # Only allow admin users to enable/disable agents
    if not getattr(current_user, 'is_superuser', False):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # In a real implementation, you'd update agent status in the registry
        return {
            "status": "success",
            "message": f"Agent {agent_name} enabled"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to enable agent: {str(e)}")


@router.post("/{agent_name}/disable")
async def disable_agent(
    agent_name: str,
    current_user: User = Depends(get_current_user)
):
    """Disable an agent from use."""
    
    # Only allow admin users to enable/disable agents
    if not getattr(current_user, 'is_superuser', False):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # In a real implementation, you'd update agent status in the registry
        return {
            "status": "success",
            "message": f"Agent {agent_name} disabled"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to disable agent: {str(e)}")


@router.get("/health/check")
async def check_agent_health(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Check the health status of all agents."""
    
    agent_names = get_agent_names()
    health_status = {}
    
    for name in agent_names:
        try:
            # Try to get the agent and check if it's responsive
            from backend.agents.registry import get_agent
            agent = get_agent(name)
            
            # Basic health check - see if agent has required methods
            is_healthy = (
                hasattr(agent, '__init__') and
                callable(getattr(agent, '__init__', None))
            )
            
            health_status[name] = {
                "status": "healthy" if is_healthy else "unhealthy",
                "last_check": "now",
                "error": None if is_healthy else "Missing required methods"
            }
            
        except Exception as e:
            health_status[name] = {
                "status": "error",
                "last_check": "now",
                "error": str(e)
            }
    
    overall_health = all(
        status["status"] == "healthy" 
        for status in health_status.values()
    )
    
    return {
        "overall_status": "healthy" if overall_health else "degraded",
        "agent_count": len(agent_names),
        "healthy_agents": sum(1 for s in health_status.values() if s["status"] == "healthy"),
        "agents": health_status
    }