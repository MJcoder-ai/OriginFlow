import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import ApprovalsDiffModal from './ApprovalsDiffModal';

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
  const [serverApply, setServerApply] = useState(true);
  const [showPreview, setShowPreview] = useState(false);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewError, setPreviewError] = useState<string | null>(null);
  const [previewBefore, setPreviewBefore] = useState<any | null>(null);
  const [previewAfter, setPreviewAfter] = useState<any | null>(null);
  const [previewNote, setPreviewNote] = useState<string | null>(null);
  const [previewDiff, setPreviewDiff] = useState<any | null>(null);
  const [previewItem, setPreviewItem] = useState<Item | null>(null);

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

  // Live updates via SSE
  useEffect(() => {
    const es = new EventSource('/api/v1/approvals/stream');
    es.onmessage = (ev) => {
      try {
        const msg = JSON.parse(ev.data || '{}');
        if (!msg || !msg.type) return;
        if (msg.type === 'heartbeat' || msg.type === 'hello') return;
        const item = msg.item;
        if (!item) return;
        setItems((prev) => {
          const idx = prev.findIndex((p) => p.id === item.id);
          const matches =
            (!status || status === '' || item.status === status) &&
            (!filterSession || item.session_id === filterSession) &&
            (!filterProject || item.project_id === filterProject);
          if (idx === -1) {
            return matches ? [item, ...prev] : prev;
          }
          const next = prev.slice();
          next[idx] = { ...prev[idx], ...item };
          const stillMatches =
            (!status || status === '' || next[idx].status === status) &&
            (!filterSession || next[idx].session_id === filterSession) &&
            (!filterProject || next[idx].project_id === filterProject);
          if (!stillMatches) {
            next.splice(idx, 1);
          }
          return next;
        });
      } catch (_e) {
        // ignore malformed payloads
      }
    };
    es.onerror = () => {
      // browser will auto-reconnect
    };
    return () => {
      es.close();
    };
  }, [status, filterSession, filterProject]);

  async function approve(it: Item) {
    const r = await api.approveApproval(it.id, note || undefined, serverApply);
    const approved = r.approved as Item;
    if (!serverApply && approved?.session_id && r.apply_client_side && approved.payload) {
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

  async function openPreview(it: Item) {
    setPreviewItem(it);
    setShowPreview(true);
    setPreviewLoading(true);
    setPreviewError(null);
    setPreviewBefore(null);
    setPreviewAfter(null);
    setPreviewNote(null);
    setPreviewDiff(null);
    try {
      const res = await api.getApprovalDiff(it.id);
      setPreviewBefore(res?.before_snapshot?.graph || null);
      setPreviewAfter(res?.after_preview?.graph || null);
      setPreviewNote(res?.after_preview?.note || null);
      setPreviewDiff(res?.diff || null);
    } catch (e: any) {
      setPreviewError(e?.message || 'Failed to load preview');
    } finally {
      setPreviewLoading(false);
    }
  }

  async function approveAndApplyFromModal() {
    if (!previewItem) return;
    await approve({ ...previewItem } as Item);
    setShowPreview(false);
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
        <label className="ml-2 text-sm flex items-center gap-2">
          <input type="checkbox" checked={serverApply} onChange={(e) => setServerApply(e.target.checked)} />
          Apply server-side
        </label>
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
                onClick={() => openPreview(it)}
                className="px-2 py-1 rounded bg-gray-700 text-white"
              >
                Preview
              </button>
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
    <ApprovalsDiffModal
      open={showPreview}
      onClose={() => setShowPreview(false)}
      loading={previewLoading}
      error={previewError}
      beforeGraph={previewBefore}
      afterGraph={previewAfter}
      note={previewNote}
      diff={previewDiff}
      onApproveAndApply={approveAndApplyFromModal}
    />
  );
}

