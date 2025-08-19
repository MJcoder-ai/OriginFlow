import React from 'react';
import { useAppStore } from '../../appStore';
import { api } from '../../services/api';

type AgentLite = {
  name: string;
  display_name?: string;
  version?: string;
  domain?: string;
  risk_class?: string;
  capabilities?: string[];
};

const AgentsPanel: React.FC = () => {
  const addStatusMessage = useAppStore((s) => s.addStatusMessage);
  const [agents, setAgents] = React.useState<AgentLite[]>([]);
  const [query, setQuery] = React.useState('');
  const [domain, setDomain] = React.useState<string>('');
  const [selected, setSelected] = React.useState<string | null>(null);
  const [detail, setDetail] = React.useState<any | null>(null);
  const [loading, setLoading] = React.useState(false);

  const load = React.useCallback(async () => {
    try {
      setLoading(true);
      const list = await api.listAgents();
      setAgents(list);
    } catch (e) {
      console.error(e);
      addStatusMessage('Failed to load agents', 'error');
    } finally {
      setLoading(false);
    }
  }, [addStatusMessage]);

  React.useEffect(() => {
    load();
    const onRefresh = () => load();
    window.addEventListener('of:agents:refresh', onRefresh as any);
    return () => window.removeEventListener('of:agents:refresh', onRefresh as any);
  }, [load]);

  const filtered = agents.filter((a) => {
    const q = query.trim().toLowerCase();
    const okQ =
      !q || a.name.toLowerCase().includes(q) || (a.display_name ?? '').toLowerCase().includes(q) || (a.domain ?? '').toLowerCase().includes(q);
    const okD = !domain || a.domain === domain;
    return okQ && okD;
  });

  const openDetail = async (name: string) => {
    try {
      setSelected(name);
      setDetail(null);
      const d = await api.getAgent(name);
      setDetail(d);
    } catch (e) {
      console.error(e);
      addStatusMessage('Failed to load agent detail', 'error');
    }
  };

  return (
    <section className="flex flex-col h-full overflow-hidden">
      <header className="flex items-center gap-2 p-2">
        <input
          placeholder="Search agents…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="border rounded px-2 py-1 text-sm w-64"
        />
        <select className="border rounded px-2 py-1 text-sm" value={domain} onChange={(e) => setDomain(e.target.value)}>
          <option value="">All domains</option>
          <option value="pv">PV</option>
          <option value="battery">Battery</option>
          <option value="structural">Structural</option>
          <option value="monitoring">Monitoring</option>
          <option value="network">Network</option>
          <option value="general">General</option>
        </select>
        {loading && <span className="text-xs text-gray-500">Loading…</span>}
      </header>
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3 p-2 overflow-auto">
        {filtered.map((a) => (
          <article
            key={a.name}
            className="bg-white rounded-xl border hover:shadow-md transition cursor-pointer p-3"
            onClick={() => openDetail(a.name)}
            role="button"
          >
            <div className="flex items-center justify-between">
              <h3 className="font-semibold">{a.display_name ?? a.name}</h3>
              <span className="text-xs bg-gray-100 rounded px-2 py-[2px]">{a.version ?? '—'}</span>
            </div>
            <div className="mt-1 text-sm text-gray-600">Domain: {a.domain ?? '—'}</div>
            <div className="mt-1 text-sm text-gray-600">Risk: {a.risk_class ?? '—'}</div>
            {a.capabilities?.length ? (
              <div className="mt-2 flex flex-wrap gap-1">
                {a.capabilities.map((c) => (
                  <span key={c} className="text-[10px] bg-gray-100 rounded px-2 py-[1px]">
                    {c}
                  </span>
                ))}
              </div>
            ) : null}
          </article>
        ))}
        {!filtered.length && !loading && <div className="p-6 text-sm text-gray-600">No agents match your filters.</div>}
      </div>

      {selected && detail && (
        <AgentDetailDrawer
          detail={detail}
          onClose={() => {
            setSelected(null);
            setDetail(null);
          }}
          onChanged={() => window.dispatchEvent(new CustomEvent('of:agents:refresh'))}
        />
      )}
    </section>
  );
};

const AgentDetailDrawer: React.FC<{ detail: any; onClose: () => void; onChanged: () => void }> = ({ detail, onClose, onChanged }) => {
  const addStatusMessage = useAppStore((s) => s.addStatusMessage);
  const name = detail?.name ?? detail?.spec?.name ?? 'agent';
  const enabled = Boolean(detail?.enabled ?? true);
  const spec = detail?.spec ?? detail;
  const toggle = async () => {
    try {
      if (enabled) {
        await api.disableAgent(name);
        addStatusMessage(`Disabled ${name}`, 'info');
      } else {
        await api.enableAgent(name);
        addStatusMessage(`Enabled ${name}`, 'success');
      }
      onChanged();
      onClose();
    } catch (e) {
      console.error(e);
      addStatusMessage('Failed to toggle agent', 'error');
    }
  };
  return (
    <div className="fixed inset-0 z-40">
      <div className="absolute inset-0 bg-black/30" onClick={onClose} />
      <aside className="absolute right-0 top-0 h-full w-[520px] max-w-[95vw] bg-white shadow-2xl p-4 overflow-y-auto">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">{spec?.display_name ?? name}</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-black">
            ✕
          </button>
        </div>
        <div className="text-sm text-gray-600 mt-1">Domain: {spec?.domain ?? '—'}</div>
        <div className="text-sm text-gray-600">Version: {spec?.version ?? '—'}</div>
        <div className="text-sm text-gray-600">Risk: {spec?.risk_class ?? '—'}</div>
        {spec?.capabilities?.length ? (
          <div className="mt-2 flex flex-wrap gap-1">
            {spec.capabilities.map((c: string) => (
              <span key={c} className="text-[10px] bg-gray-100 rounded px-2 py-[1px]">
                {c}
              </span>
            ))}
          </div>
        ) : null}
        <h3 className="mt-4 font-medium">Specification</h3>
        <pre className="mt-2 p-2 bg-gray-50 border rounded text-xs overflow-auto max-h-[45vh]">
{JSON.stringify(spec, null, 2)}
        </pre>
        <div className="mt-4 flex gap-2">
          <button onClick={toggle} className="px-3 py-1 text-sm rounded bg-blue-600 text-white hover:bg-blue-700">
            {enabled ? 'Disable' : 'Enable'}
          </button>
          <button onClick={onClose} className="px-3 py-1 text-sm rounded bg-gray-100 hover:bg-gray-200">
            Close
          </button>
        </div>
      </aside>
    </div>
  );
};

export default AgentsPanel;

