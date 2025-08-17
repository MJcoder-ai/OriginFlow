# OriginFlow Plug‑in Development Guide

This document explains how to extend OriginFlow by writing custom
agent plug‑ins.  Each agent encapsulates a domain or task and is
discovered at runtime via :class:`backend.agents.plugin_registry.PluginRegistry`.

## Architecture overview

Agents inherit from :class:`backend.agents.base.AgentBase`, which now
supports optional metadata for discovery:

| Attribute      | Required | Description                                   |
|----------------|----------|-----------------------------------------------|
| ``name``       | Yes      | Unique identifier for the agent.              |
| ``domain``     | No       | High‑level domain (``pv``, ``hvac``, etc.).    |
| ``risk_class`` | No       | Risk tag for auto‑approval policies.          |
| ``capabilities`` | No    | Keywords describing capabilities.             |
| ``examples``   | No       | Sample commands for documentation and UIs.    |
| ``handle``     | Yes      | Process a natural language command.           |
| ``execute``    | Yes      | Perform work for a given task identifier.     |
| ``can_handle`` | No       | Decide if a command should be handled.        |

Existing agents can ignore the new metadata fields and continue to
implement ``handle`` and ``execute`` as before.

## Registering a plug‑in agent

Place a module inside the ``backend/plugins`` package and register the
agent class with :class:`PluginRegistry` when the module is imported:

```python
from backend.agents.base import AgentBase
from backend.agents.plugin_registry import PluginRegistry


class PVExampleAgent(AgentBase):
    name = "pv_example"
    domain = "pv"
    risk_class = "low"
    capabilities = ["example"]
    examples = ["add an example component"]

    async def handle(self, command: str, **kwargs):
        return []

    async def execute(self, session_id: str, tid: str, **kwargs):
        return {"actions": [], "message": "stub"}


PluginRegistry.register(PVExampleAgent)
```

## Loading plug‑ins

Call :func:`backend.agents.plugin_registry.load_plugins` during
application start‑up.  This imports every module in ``backend.plugins``
and registers the contained agents.

```python
from backend.agents.plugin_registry import load_plugins

load_plugins()  # loads from backend.plugins by default
```

You can pass a different package name to load plug‑ins from another
location.

## Routing to plug‑in agents

The router can iterate over all registered agent classes and delegate a
command to the first one that claims it can handle it:

```python
from backend.agents.plugin_registry import PluginRegistry


async def route_command(command: str, graph):
    for agent_cls in PluginRegistry.all():
        agent = agent_cls()
        if agent.can_handle(command):
            return await agent.execute(graph)
    raise ValueError(f"No agent found for command: {command}")
```

## Error isolation

Plug‑in code runs in the same process as the core.  Consider executing
agents in separate processes or imposing timeouts to prevent a faulty
plug‑in from affecting stability.  This is left to future iterations.

