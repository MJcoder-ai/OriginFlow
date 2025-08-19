import React, { useEffect, useState } from 'react';
import { api } from '../services/api';

type Item = {
  id: number;
  tenant_id: string;
  project_id?: string | null;
  session_id?: string | null;
  agent_name?: string | null;
  action_type: string;
  payload: any;
  confidence?: number | null;
  status: string;
  reason?: string | null;
  requested_by_id?: string | null;
  approved_by_id?: string | null;
  created_at: string;
};

export default function ApprovalsPanel() {
  const [items, setItems] = useState<Item[]>([]);
  const [status, setStatus] = useState<string>('pending');
  const [filterSession, setFilterSession] = useState('');
  const [filterProject, setFilterProject] = useState('');
  const [note, setNote] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    try {
      const res = await api.listApprovals({
        status: status || undefined,
        session_id: filterSession || undefined,
        project_id: filterProject || undefined,
        limit: 100,
      });
      setItems(res.items || []);
      setError(null);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function approve(it: Item) {
    const r = await api.approveApproval(it.id, note || undefined);
    const approved = r.approved as Item;
    if (approved?.session_id && r.apply_client_side && approved.payload) {
      await api.postSessionAct(approved.session_id, approved.payload);
    }
    setNote('');
    await load();
  }

  async function reject(it: Item) {
    await api.rejectApproval(it.id, note || undefined);
    setNote('');
    await load();
  }

  return (
    <div className="p-4 space-y-4">
      <h1 className="text-xl font-semibold">Approvals</h1>
      <div className="flex flex-wrap gap-2 items-center">
        <label className="text-sm text-gray-500">Status</label>
        <select
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          className="border rounded px-2 py-1"
        >
          <option value="pending">pending</option>
          <option value="">(all)</option>
          <option value="approved">approved</option>
          <option value="rejected">rejected</option>
          <option value="applied">applied</option>
        </select>
        <input
          placeholder="session id"
          value={filterSession}
          onChange={(e) => setFilterSession(e.target.value)}
          className="border rounded px-2 py-1"
        />
        <input
          placeholder="project id"
          value={filterProject}
          onChange={(e) => setFilterProject(e.target.value)}
          className="border rounded px-2 py-1"
        />
        <button onClick={load} className="px-3 py-1 rounded bg-blue-600 text-white">
          Reload
        </button>
        <input
          placeholder="decision note..."
          value={note}
          onChange={(e) => setNote(e.target.value)}
          className="border rounded px-2 py-1 flex-1"
        />
      </div>
      {error && <div className="text-red-600 text-sm">{error}</div>}
      <div className="border rounded">
        <div className="grid grid-cols-8 gap-2 px-3 py-2 bg-gray-50 text-xs font-medium">
          <div>ID</div>
          <div>Session</div>
          <div>Agent</div>
          <div>Action</div>
          <div>Conf</div>
          <div>Status</div>
          <div>Reason</div>
          <div>Decide</div>
        </div>
        {items.map((it) => (
          <div
            key={it.id}
            className="grid grid-cols-8 gap-2 px-3 py-2 border-t items-center text-sm"
          >
            <div>{it.id}</div>
            <div className="truncate" title={it.session_id || ''}>
              {it.session_id || '-'}
            </div>
            <div>{it.agent_name || '-'}</div>
            <div>{it.action_type}</div>
            <div>{it.confidence != null ? it.confidence.toFixed(2) : '-'}</div>
            <div>{it.status}</div>
            <div className="truncate" title={it.reason || ''}>
              {it.reason || '-'}
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => approve(it)}
                className="px-2 py-1 rounded bg-emerald-600 text-white"
              >
                Approve
              </button>
              <button
                onClick={() => reject(it)}
                className="px-2 py-1 rounded bg-rose-600 text-white"
              >
                Reject
              </button>
            </div>
            <div className="col-span-8 bg-gray-50 rounded p-2 text-xs font-mono overflow-auto">
              <pre className="whitespace-pre-wrap">
                {JSON.stringify(it.payload, null, 2)}
              </pre>
            </div>
          </div>
        ))}
        {!loading && items.length === 0 && (
          <div className="px-3 py-4 text-sm text-gray-500">No items</div>
        )}
      </div>
    </div>
  );
}

