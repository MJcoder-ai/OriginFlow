import React, { useEffect, useState } from 'react';
import {
  fetchTenantSettings,
  updateTenantSettings,
  listApprovals,
  approveAction,
  rejectAction,
} from '../../services/governance';

interface TenantSettings {
  tenant_id: string;
  ai_auto_approve: boolean;
  risk_threshold_low: number;
  risk_threshold_medium: number;
  risk_threshold_high: number;
  whitelisted_actions?: { items: string[] };
  enabled_domains?: { items: string[] };
  feature_flags?: Record<string, boolean>;
}

const GovernanceTab: React.FC = () => {
  const [tenantId, setTenantId] = useState('tenant_default');
  const [settings, setSettings] = useState<TenantSettings | null>(null);
  const [pending, setPending] = useState<any[]>([]);
  const [statusFilter, setStatusFilter] = useState<'pending' | 'approved' | 'rejected'>('pending');

  const loadAll = async () => {
    const s = await fetchTenantSettings(tenantId);
    setSettings(s);
    const q = await listApprovals(tenantId, statusFilter);
    setPending(q);
  };

  useEffect(() => {
    loadAll();
    const t = setInterval(loadAll, 10000);
    return () => clearInterval(t);
  }, [tenantId, statusFilter]);

  if (!settings) return <div className="p-4">Loading governance settings…</div>;

  const save = async () => {
    const payload = {
      ai_auto_approve: settings.ai_auto_approve,
      risk_threshold_low: settings.risk_threshold_low,
      risk_threshold_medium: settings.risk_threshold_medium,
      risk_threshold_high: settings.risk_threshold_high,
      whitelisted_actions: settings.whitelisted_actions,
      enabled_domains: settings.enabled_domains,
      feature_flags: settings.feature_flags,
    };
    const s = await updateTenantSettings(tenantId, payload);
    setSettings(s);
  };

  return (
    <div className="space-y-6">
      <div className="flex gap-2 items-center">
        <label className="text-sm">Tenant</label>
        <input
          className="border rounded px-2 py-1"
          value={tenantId}
          onChange={(e) => setTenantId(e.target.value)}
        />
      </div>

      <section className="border rounded p-4 space-y-3">
        <h3 className="font-medium">Auto-Approval Policy</h3>
        <div className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={settings.ai_auto_approve}
            onChange={(e) => setSettings({ ...settings!, ai_auto_approve: e.target.checked })}
          />
          <span>Enable auto-approval (still constrained by risk thresholds)</span>
        </div>
        <div className="grid grid-cols-3 gap-3">
          <div>
            <label className="text-sm block">Low Threshold</label>
            <input
              type="number"
              step="0.01"
              className="border rounded px-2 py-1 w-full"
              value={settings.risk_threshold_low}
              onChange={(e) =>
                setSettings({ ...settings!, risk_threshold_low: parseFloat(e.target.value) })
              }
            />
          </div>
          <div>
            <label className="text-sm block">Medium Threshold</label>
            <input
              type="number"
              step="0.01"
              className="border rounded px-2 py-1 w-full"
              value={settings.risk_threshold_medium}
              onChange={(e) =>
                setSettings({ ...settings!, risk_threshold_medium: parseFloat(e.target.value) })
              }
            />
          </div>
          <div>
            <label className="text-sm block">High Threshold</label>
            <input
              type="number"
              step="0.01"
              className="border rounded px-2 py-1 w-full"
              value={settings.risk_threshold_high}
              onChange={(e) =>
                setSettings({ ...settings!, risk_threshold_high: parseFloat(e.target.value) })
              }
            />
          </div>
        </div>
        <div>
          <label className="text-sm block">Whitelisted action types (comma-separated)</label>
          <input
            className="border rounded px-2 py-1 w-full"
            value={(settings.whitelisted_actions?.items || []).join(',')}
            onChange={(e) =>
              setSettings({
                ...settings!,
                whitelisted_actions: {
                  items: e.target.value
                    .split(',')
                    .map((s) => s.trim())
                    .filter(Boolean),
                },
              })
            }
          />
        </div>
        <button className="bg-black text-white rounded px-3 py-1" onClick={save}>
          Save
        </button>
      </section>

      <section className="border rounded p-4 space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="font-medium">Approval Queue</h3>
          <select
            className="border rounded px-2 py-1"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as any)}
          >
            <option value="pending">Pending</option>
            <option value="approved">Approved</option>
            <option value="rejected">Rejected</option>
          </select>
        </div>
        <div className="border rounded divide-y">
          {pending.map((item) => (
            <div key={item.id} className="p-3 flex items-start justify-between gap-4">
              <div className="text-sm">
                <div className="font-mono text-xs text-gray-500">
                  #{item.id} · {item.status}
                </div>
                <div>
                  <b>{item.action_type}</b> by <code>{item.agent_name}</code> (risk: {item.risk_class},
                  conf: {item.confidence.toFixed(2)})
                </div>
                <pre className="bg-gray-50 p-2 rounded mt-2 overflow-auto text-xs">
                  {JSON.stringify(item.payload, null, 2)}
                </pre>
              </div>
              <div className="flex gap-2">
                {item.status === 'pending' ? (
                  <>
                    <button
                      className="bg-green-600 text-white rounded px-3 py-1"
                      onClick={() => approveAction(item.id).then(loadAll)}
                    >
                      Approve
                    </button>
                    <button
                      className="bg-red-600 text-white rounded px-3 py-1"
                      onClick={() => rejectAction(item.id).then(loadAll)}
                    >
                      Reject
                    </button>
                  </>
                ) : (
                  <div className="text-xs text-gray-600">
                    {item.status === 'approved' ? 'Approved' : 'Rejected'}
                    {item.decided_by ? ` by ${item.decided_by}` : ''}
                    {item.decision_reason ? ` · ${item.decision_reason}` : ''}
                  </div>
                )}
              </div>
            </div>
          ))}
          {pending.length === 0 && (
            <div className="p-6 text-center text-sm text-gray-500">No items</div>
          )}
        </div>
      </section>
    </div>
  );
};

export default GovernanceTab;

