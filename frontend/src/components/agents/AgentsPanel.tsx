import React, { useEffect, useState } from 'react';
import { api } from '../services/api';

interface TenantAgentRow {
  agent_name: string;
  display_name: string;
  enabled: boolean;
  pinned_version: number | null;
  effective_version: number | null;
  status: string | null;
  domain: string | null;
  capabilities: any;
}

export default function AgentsPanel() {
  const [rows, setRows] = useState<TenantAgentRow[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tenantId, setTenantId] = useState<string>('');
  const [idea, setIdea] = useState<string>('');
  const [draftSpec, setDraftSpec] = useState<string>('');
  const [refineCritique, setRefineCritique] = useState<string>('');

  async function load() {
    try {
      const data = await api.listTenantAgentState(tenantId || undefined);
      setRows(data);
      setError(null);
    } catch (e: any) {
      setError(e.message);
    }
  }

  useEffect(() => {
    load();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function toggleEnabled(row: TenantAgentRow) {
    await api.updateTenantAgentState(row.agent_name, { enabled: !row.enabled }, tenantId || undefined);
    await load();
  }

  async function pinVersion(row: TenantAgentRow, version: number | null) {
    await api.updateTenantAgentState(row.agent_name, { pinned_version: version ?? undefined }, tenantId || undefined);
    await load();
  }

  async function synthesize() {
    if (!idea.trim()) return;
    const res = await api.assistSynthesizeSpec(idea);
    setDraftSpec(JSON.stringify(res.spec, null, 2));
  }

  async function createDraft() {
    if (!draftSpec.trim()) return;
    const spec = JSON.parse(draftSpec);
    await api.createAgentDraft(spec);
    setIdea('');
    setRefineCritique('');
    await load();
  }

  async function refine() {
    if (!draftSpec.trim() || !refineCritique.trim()) return;
    const current = JSON.parse(draftSpec);
    const res = await api.assistRefineSpec(current, refineCritique);
    setDraftSpec(JSON.stringify(res.spec, null, 2));
  }

  return (
    <div className="p-4 space-y-4">
      <h1 className="text-xl font-semibold">AI Agents (Tenant Catalog)</h1>
      <div className="flex items-center gap-2">
        <label className="text-sm text-gray-500">Tenant:</label>
        <input value={tenantId} onChange={(e) => setTenantId(e.target.value)} placeholder="default" className="border px-2 py-1 rounded" />
        <button onClick={load} className="px-3 py-1 rounded bg-blue-600 text-white">Reload</button>
      </div>
      {error && <div className="text-red-600 text-sm">{error}</div>}
      <div className="border rounded">
        <div className="grid grid-cols-7 gap-2 px-3 py-2 bg-gray-50 text-xs font-medium">
          <div>Name</div>
          <div>Display</div>
          <div>Domain</div>
          <div>Enabled</div>
          <div>Effective</div>
          <div>Pinned</div>
          <div>Actions</div>
        </div>
        {rows?.map((r) => (
          <div key={r.agent_name} className="grid grid-cols-7 gap-2 px-3 py-2 border-t items-center text-sm">
            <div>{r.agent_name}</div>
            <div>{r.display_name}</div>
            <div>{r.domain || '-'}</div>
            <div>
              <button onClick={() => toggleEnabled(r)} className={`px-2 py-1 rounded ${r.enabled ? 'bg-green-600' : 'bg-gray-400'} text-white`}>
                {r.enabled ? 'Enabled' : 'Disabled'}
              </button>
            </div>
            <div>{r.effective_version ?? '-'}</div>
            <div>
              <input
                type="number"
                className="w-20 border rounded px-2 py-1"
                placeholder="version"
                onKeyDown={async (e) => {
                  if (e.key === 'Enter') {
                    const val = (e.target as HTMLInputElement).value;
                    await pinVersion(r, val ? parseInt(val, 10) : null);
                    (e.target as HTMLInputElement).value = '';
                  }
                }}
              />
            </div>
            <div className="flex gap-2">
              <button
                onClick={async () => {
                  await api.publishAgent(r.agent_name);
                  await load();
                }}
                className="px-2 py-1 rounded bg-indigo-600 text-white"
              >
                Publish latest
              </button>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-6">
        <h2 className="text-lg font-semibold">Author new/updated Agent (LLM assisted)</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <label className="text-sm text-gray-600">Idea</label>
            <textarea value={idea} onChange={(e) => setIdea(e.target.value)} rows={6} className="w-full border rounded p-2" placeholder="Describe what the agent should do..." />
            <div className="flex gap-2">
              <button onClick={synthesize} className="px-3 py-1 rounded bg-blue-600 text-white">Synthesize Spec</button>
              <button onClick={createDraft} className="px-3 py-1 rounded bg-emerald-600 text-white">Save Draft</button>
            </div>
          </div>
          <div className="space-y-2">
            <label className="text-sm text-gray-600">Draft Spec (editable JSON)</label>
            <textarea value={draftSpec} onChange={(e) => setDraftSpec(e.target.value)} rows={12} className="w-full border rounded p-2 font-mono text-xs" />
            <div className="flex gap-2">
              <input value={refineCritique} onChange={(e) => setRefineCritique(e.target.value)} className="flex-1 border rounded p-2" placeholder="Refinement critique..." />
              <button onClick={refine} className="px-3 py-1 rounded bg-purple-600 text-white">Refine</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

