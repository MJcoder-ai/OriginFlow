import React, { useEffect, useState } from 'react';
import { api } from '../services/api';

type Policy = {
  tenant_id: string;
  auto_approve_enabled: boolean;
  risk_threshold_default: number;
  action_whitelist: { actions: string[] };
  action_blacklist: { actions: string[] };
  enabled_domains: { domains: string[] };
  feature_flags: Record<string, boolean>;
  data: Record<string, any>;
  version: number;
  updated_at?: string;
  updated_by_id?: string;
};

export default function TenantPolicyPage() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [policy, setPolicy] = useState<Policy | null>(null);
  const [dirty, setDirty] = useState(false);
  const [testActionType, setTestActionType] = useState('component.create');
  const [testConfidence, setTestConfidence] = useState(0.9);
  const [testAgent, setTestAgent] = useState('');
  const [testResult, setTestResult] = useState<any | null>(null);

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        const p = await api.getTenantPolicy();
        setPolicy(p);
      } catch (e: any) {
        setError(e?.message || 'Failed to load');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  function mutate(mut: Partial<Policy>) {
    if (!policy) return;
    setPolicy({ ...policy, ...mut });
    setDirty(true);
  }

  function updateList(field: 'action_whitelist' | 'action_blacklist' | 'enabled_domains', str: string) {
    const parts = str
      .split(',')
      .map((s) => s.trim())
      .filter(Boolean);
    if (!policy) return;
    const val = field === 'enabled_domains' ? { domains: parts } : { actions: parts };
    mutate({ [field]: val } as any);
  }

  async function save() {
    if (!policy) return;
    try {
      setSaving(true);
      const payload = {
        version: policy.version,
        auto_approve_enabled: policy.auto_approve_enabled,
        risk_threshold_default: policy.risk_threshold_default,
        action_whitelist: policy.action_whitelist,
        action_blacklist: policy.action_blacklist,
        enabled_domains: policy.enabled_domains,
        feature_flags: policy.feature_flags,
        data: policy.data,
      };
      const updated = await api.updateTenantPolicy(payload);
      setPolicy(updated);
      setDirty(false);
    } catch (e: any) {
      alert(e?.message || 'Save failed');
    } finally {
      setSaving(false);
    }
  }

  async function testPolicy() {
    try {
      const r = await api.testTenantPolicy({
        action_type: testActionType,
        confidence: testConfidence,
        agent_name: testAgent || undefined,
      });
      setTestResult(r);
    } catch (e: any) {
      setTestResult({ error: e?.message || 'Failed' });
    }
  }

  if (loading) return <div className="p-4 text-sm text-gray-600">Loading policy…</div>;
  if (error) return <div className="p-4 text-sm text-red-600">{error}</div>;
  if (!policy) return <div className="p-4 text-sm">No policy found.</div>;

  return (
    <div className="p-4 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-lg font-semibold">Tenant Policy</div>
          <div className="text-xs text-gray-500">
            Tenant: {policy.tenant_id} • Version: {policy.version} • Updated by: {policy.updated_by_id || '-'} • Updated at:
            {policy.updated_at || '-'}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            disabled={!dirty || saving}
            onClick={save}
            className={`px-3 py-1 rounded ${dirty ? 'bg-blue-600 text-white' : 'bg-gray-300 text-gray-700'}`}
          >
            {saving ? 'Saving…' : 'Save'}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="border rounded p-3 space-y-3">
          <div className="font-medium">Auto-approval</div>
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={policy.auto_approve_enabled}
              onChange={(e) => mutate({ auto_approve_enabled: e.target.checked })}
            />
            Enable auto-approval
          </label>
          <div className="text-sm">
            <div>Risk threshold (0–1):</div>
            <input
              type="range"
              min={0}
              max={1}
              step={0.01}
              value={policy.risk_threshold_default}
              onChange={(e) => mutate({ risk_threshold_default: parseFloat(e.target.value) })}
              className="w-full"
            />
            <div className="text-xs text-gray-600 mt-1">
              Current: {policy.risk_threshold_default.toFixed(2)}
            </div>
          </div>
        </div>

        <div className="border rounded p-3 space-y-3">
          <div className="font-medium">Domains</div>
          <div className="text-sm">Enabled domains (comma separated):</div>
          <input
            className="border rounded px-2 py-1 w-full"
            value={(policy.enabled_domains?.domains || []).join(', ')}
            onChange={(e) => updateList('enabled_domains', e.target.value)}
            placeholder="pv, wiring, structural, battery"
          />
          <div className="text-xs text-gray-600">
            Agents in disabled domains won’t register/run for this tenant.
          </div>
        </div>

        <div className="border rounded p-3 space-y-3">
          <div className="font-medium">Whitelists & Blacklists</div>
          <div className="text-sm">Whitelist actions (comma separated):</div>
          <input
            className="border rounded px-2 py-1 w-full"
            value={(policy.action_whitelist?.actions || []).join(', ')}
            onChange={(e) => updateList('action_whitelist', e.target.value)}
            placeholder="component.create, link.create"
          />
          <div className="text-sm mt-2">Blacklist actions (comma separated):</div>
          <input
            className="border rounded px-2 py-1 w-full"
            value={(policy.action_blacklist?.actions || []).join(', ')}
            onChange={(e) => updateList('action_blacklist', e.target.value)}
            placeholder="remove_link, structural.delete"
          />
          <div className="text-xs text-gray-600">
            Blacklist always denies; whitelist always approves (overrides threshold).
          </div>
        </div>

        <div className="border rounded p-3 space-y-3">
          <div className="font-medium">Feature flags</div>
          <div className="text-xs text-gray-600">Toggle platform features for this tenant.</div>
          <div className="grid grid-cols-2 gap-2 text-sm">
            {[
              'placeholder_fallback_enabled',
              'server_side_apply_default',
              'live_updates_enabled',
              'agent_registry_hydrate_on_request',
            ].map((key) => (
              <label key={key} className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={!!policy.feature_flags?.[key]}
                  onChange={(e) => {
                    const ff = { ...(policy.feature_flags || {}) };
                    ff[key] = e.target.checked;
                    mutate({ feature_flags: ff });
                  }}
                />
                {key}
              </label>
            ))}
          </div>
        </div>
      </div>

      <div className="border rounded p-3 space-y-3">
        <div className="font-medium">Dry-run policy test</div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-2 text-sm">
          <div>
            <div>Action type</div>
            <input
              className="border rounded px-2 py-1 w-full"
              value={testActionType}
              onChange={(e) => setTestActionType(e.target.value)}
              placeholder="component.create"
            />
          </div>
          <div>
            <div>Confidence</div>
            <input
              type="number"
              min={0}
              max={1}
              step={0.01}
              className="border rounded px-2 py-1 w-full"
              value={testConfidence}
              onChange={(e) => setTestConfidence(parseFloat(e.target.value))}
            />
          </div>
          <div>
            <div>Agent (optional)</div>
            <input
              className="border rounded px-2 py-1 w-full"
              value={testAgent}
              onChange={(e) => setTestAgent(e.target.value)}
              placeholder="component_agent"
            />
          </div>
          <div className="flex items-end">
            <button
              onClick={testPolicy}
              className="px-3 py-1 rounded bg-gray-800 text-white w-full"
            >
              Test
            </button>
          </div>
        </div>
        {testResult && (
          <div className="text-xs font-mono mt-2 bg-gray-50 rounded p-2 overflow-auto">
            <pre>{JSON.stringify(testResult, null, 2)}</pre>
          </div>
        )}
      </div>
    </div>
  );
}
