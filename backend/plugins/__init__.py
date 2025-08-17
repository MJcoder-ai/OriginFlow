"""Namespace package for OriginFlow agent plug‑ins.

Custom agent modules placed in this package are automatically imported
when :func:`backend.agents.plugin_registry.load_plugins` is invoked.  Each
module should define an :class:`~backend.agents.base.AgentBase` subclass
and register it with :class:`backend.agents.plugin_registry.PluginRegistry`.

Example plug‑in module ``backend/plugins/pv_example.py``::

    from backend.agents.base import AgentBase
    from backend.agents.plugin_registry import PluginRegistry

    class PVExampleAgent(AgentBase):
        name = "pv_example"
        domain = "pv"
        risk_class = "low"
        capabilities = ["example"]
        examples = ["example command"]

        async def handle(self, command: str, **kwargs):
            return []

        async def execute(self, session_id: str, tid: str, **kwargs):
            return {"message": "example"}

    PluginRegistry.register(PVExampleAgent)

"""

__all__: list[str] = []

