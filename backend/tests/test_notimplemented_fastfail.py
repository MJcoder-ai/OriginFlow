import inspect
import backend.agents.router_agent as mod


def test_ellipsis_removed():
    src = inspect.getsource(mod)
    assert "..." not in src or "NotImplementedError" in src
