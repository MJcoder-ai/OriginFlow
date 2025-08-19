import asyncio
import json
import re
import pytest
from fastapi import FastAPI, Response, HTTPException
from fastapi.testclient import TestClient

from backend.observability.metrics import (
    METRICS_ENABLED,
    generate_latest,
    CONTENT_TYPE_LATEST,
)
import importlib.util
import types
from pathlib import Path

# Dynamic imports to avoid heavy package side effects
_root = Path(__file__).resolve().parents[2]

# Create minimal backend.services package stub
services_pkg = types.ModuleType("backend.services")
services_pkg.__path__ = []  # type: ignore[attr-defined]
sys_modules = __import__("sys").modules
sys_modules["backend.services"] = services_pkg

spec_ts = importlib.util.spec_from_file_location(
    "backend.services.tenant_settings_service", _root / "backend/services/tenant_settings_service.py"
)
ts_module = importlib.util.module_from_spec(spec_ts)
spec_ts.loader.exec_module(ts_module)  # type: ignore
sys_modules["backend.services.tenant_settings_service"] = ts_module
services_pkg.tenant_settings_service = ts_module

spec_pc = importlib.util.spec_from_file_location(
    "backend.services.policy_cache", _root / "backend/services/policy_cache.py"
)
policy_cache_module = importlib.util.module_from_spec(spec_pc)
sys_modules["backend.services.policy_cache"] = policy_cache_module
spec_pc.loader.exec_module(policy_cache_module)  # type: ignore
PolicyCache = policy_cache_module.PolicyCache

spec_ap = importlib.util.spec_from_file_location(
    "backend.services.approval_policy_service", _root / "backend/services/approval_policy_service.py"
)
approval_module = importlib.util.module_from_spec(spec_ap)
sys_modules["backend.services.approval_policy_service"] = approval_module
spec_ap.loader.exec_module(approval_module)  # type: ignore
ApprovalPolicyService = approval_module.ApprovalPolicyService

from backend.utils.tenant_context import set_tenant_id

app = FastAPI()

@app.get("/metrics")
async def metrics_endpoint():
    if not METRICS_ENABLED:
        raise HTTPException(status_code=503, detail="Metrics disabled")
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)

TENANT = "e2e-tenant"

class FakeRedis:
    def __init__(self):
        self.store = {}
    async def get(self, key: str):
        return self.store.get(key)
    async def setex(self, key: str, ttl: int, val: str):
        self.store[key] = val
        return True
    async def delete(self, key: str):
        self.store.pop(key, None)
        return True

class DummySession:
    class _Row:
        def to_dict(self):
            return {
                "tenant_id": TENANT,
                "auto_approve_enabled": True,
                "risk_threshold_default": 0.8,
                "action_whitelist": {"actions": []},
                "action_blacklist": {"actions": []},
                "enabled_domains": {"domains": []},
                "feature_flags": {},
                "version": 1,
            }
    async def scalar(self, _):
        return DummySession._Row()

def scrape_metric(body: bytes, name: str, labels: dict[str, str]) -> float:
    """Return the value of the metric with matching labels (order agnostic)."""
    text = body.decode("utf-8")
    pattern = re.compile(rf'^{re.escape(name)}\{{([^}}]*)\}}\s+([0-9\.eE+-]+)$', re.MULTILINE)
    val = 0.0
    for lbls, v in pattern.findall(text):
        parsed = {}
        for item in lbls.split(","):
            k, _, value = item.partition("=")
            parsed[k] = value.strip('"')
        if all(parsed.get(k) == str(v) for k, v in labels.items()):
            val = float(v)
    return val

@pytest.mark.asyncio
async def test_policy_cache_metrics_hits_and_misses(monkeypatch):
    client = TestClient(app)
    set_tenant_id(TENANT)

    # Start with no redis: ensure memory hit path works
    async def _no_redis():
        return None
    monkeypatch.setattr(PolicyCache, "_redis", staticmethod(_no_redis))

    # Force set -> populates memory
    await PolicyCache.set(TENANT, {"foo": "bar", "version": 1})
    # Baseline metrics
    before = client.get("/metrics")
    # Memory hit
    _ = await PolicyCache.get(DummySession(), TENANT)
    after = client.get("/metrics")
    labels = {"layer": "memory", "tenant_id": TENANT}
    assert scrape_metric(after.content, "policy_cache_hits_total", labels) >= scrape_metric(before.content, "policy_cache_hits_total", labels) + 1

    # Now test redis hit
    fake = FakeRedis()
    # Clear memory
    PolicyCache._mem.pop(TENANT, None)
    # Write redis payload directly
    await fake.setex(f"policy:{TENANT}", 60, json.dumps({"value": {"baz": 1}, "version": 1}))
    async def _fake_redis():
        return fake
    monkeypatch.setattr(PolicyCache, "_redis", staticmethod(_fake_redis))

    before = client.get("/metrics")
    _ = await PolicyCache.get(DummySession(), TENANT)
    after = client.get("/metrics")
    labels = {"layer": "redis", "tenant_id": TENANT}
    assert scrape_metric(after.content, "policy_cache_hits_total", labels) >= scrape_metric(before.content, "policy_cache_hits_total", labels) + 1

    # Miss path: memory & redis miss → DB load + dogpile
    PolicyCache._mem.pop(TENANT, None)
    fake.store.clear()
    before = client.get("/metrics")
    _ = await PolicyCache.get(DummySession(), TENANT)
    after = client.get("/metrics")

    miss_mem = {"layer": "memory", "tenant_id": TENANT}
    miss_redis = {"layer": "redis", "tenant_id": TENANT}
    miss_db = {"layer": "db", "tenant_id": TENANT}
    dogpile = {"tenant_id": TENANT}
    assert scrape_metric(after.content, "policy_cache_misses_total", miss_mem) >= scrape_metric(before.content, "policy_cache_misses_total", miss_mem) + 1
    assert scrape_metric(after.content, "policy_cache_misses_total", miss_redis) >= scrape_metric(before.content, "policy_cache_misses_total", miss_redis) + 1
    assert scrape_metric(after.content, "policy_cache_misses_total", miss_db) >= scrape_metric(before.content, "policy_cache_misses_total", miss_db) + 1
    assert scrape_metric(after.content, "policy_cache_dogpile_wait_total", dogpile) >= scrape_metric(before.content, "policy_cache_dogpile_wait_total", dogpile) + 1

@pytest.mark.asyncio
async def test_approval_decision_metrics_increment():
    client = TestClient(app)
    set_tenant_id(TENANT)

    policy = {
        "auto_approve_enabled": True,
        "risk_threshold_default": 0.8,
        "action_whitelist": {"actions": ["safe_action"]},
        "action_blacklist": {"actions": ["danger_action"]},
        "enabled_domains": {"domains": []},
        "feature_flags": {}
    }
    before = client.get("/metrics")
    # whitelist -> allow
    _ = await ApprovalPolicyService.is_auto_approved(policy, "safe_action", 0.1, agent_name="router")
    # blacklist -> deny
    _ = await ApprovalPolicyService.is_auto_approved(policy, "danger_action", 0.99, agent_name="router")
    # threshold allow
    _ = await ApprovalPolicyService.is_auto_approved(policy, "normal_action", 0.85, agent_name="router")
    # below threshold deny
    _ = await ApprovalPolicyService.is_auto_approved(policy, "normal_action", 0.50, agent_name="router")
    after = client.get("/metrics")

    allow = {"result": "allow", "reason": "whitelist", "action_type": "safe_action", "agent_name": "router", "tenant_id": TENANT}
    deny_bl = {"result": "deny", "reason": "blacklist", "action_type": "danger_action", "agent_name": "router", "tenant_id": TENANT}
    allow_thr = {"result": "allow", "reason": "threshold", "action_type": "normal_action", "agent_name": "router", "tenant_id": TENANT}
    deny_thr = {"result": "deny", "reason": "below_threshold_or_disabled", "action_type": "normal_action", "agent_name": "router", "tenant_id": TENANT}
    assert scrape_metric(after.content, "approval_decisions_total", allow) >= scrape_metric(before.content, "approval_decisions_total", allow) + 1
    assert scrape_metric(after.content, "approval_decisions_total", deny_bl) >= scrape_metric(before.content, "approval_decisions_total", deny_bl) + 1
    assert scrape_metric(after.content, "approval_decisions_total", allow_thr) >= scrape_metric(before.content, "approval_decisions_total", allow_thr) + 1
    assert scrape_metric(after.content, "approval_decisions_total", deny_thr) >= scrape_metric(before.content, "approval_decisions_total", deny_thr) + 1

def test_metrics_endpoint_works():
    client = TestClient(app)
    r = client.get("/metrics")
    assert r.status_code == 200
    text = r.text
    assert "approval_decisions_total" in text
    assert "policy_cache_hits_total" in text
