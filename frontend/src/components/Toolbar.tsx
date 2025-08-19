import React from 'react';
import { useAppStore } from '../appStore';
import { exportAttributesToCsv } from '../utils/exportCsv';
import { reanalyze, confirmClose } from '../services/attributesApi';

const Toolbar: React.FC = () => {
  const analyzeAndExecute = useAppStore((s) => s.analyzeAndExecute);
  const undo = useAppStore((s) => s.undo);
  const redo = useAppStore((s) => s.redo);
  const historyIndex = useAppStore((s) => s.historyIndex);
  const historyLength = useAppStore((s) => s.history.length);
  const activeDatasheet = useAppStore((s) => s.activeDatasheet);
  const addStatusMessage = useAppStore((s) => s.addStatusMessage);
  const setActiveDatasheet = useAppStore((s) => s.setActiveDatasheet);
  const setRoute = useAppStore((s) => s.setRoute);
  const datasheetDirty = useAppStore((s) => s.datasheetDirty);
  const setDatasheetDirty = useAppStore((s) => s.setDatasheetDirty);
  const route = useAppStore((s) => s.route);
  const [showNewAgent, setShowNewAgent] = React.useState(false);

  const handleAnalyzeClick = async () => {
    // If a datasheet is currently open, trigger re-analysis of that datasheet
    if (activeDatasheet) {
      const proceed = window.confirm(
        'Re-analysing will discard extracted images and metadata. Continue?'
      );
      if (!proceed) return;
      try {
        addStatusMessage('Re-analysing datasheet...', 'info');
        await reanalyze(activeDatasheet.id);
        // Do NOT close the datasheet; leave it open. UI will update when parsing completes.
      } catch (err: any) {
        console.error('Failed to reanalyze datasheet', err);
        addStatusMessage('Re-Analyze failed', 'error');
      }
    } else {
      // Otherwise run the AI design validation
      analyzeAndExecute('validate my design');
    }
  };

  // Confirm & close handler for the toolbar button
  const handleConfirmClick = async () => {
    if (!activeDatasheet) return;
    try {
      await confirmClose(activeDatasheet.id);
      addStatusMessage('Datasheet confirmed', 'success');
      setDatasheetDirty(false);
      setActiveDatasheet(null);
      setRoute('components');
    } catch (err: any) {
      console.error('Failed to confirm datasheet', err);
      addStatusMessage('Failed to confirm datasheet', 'error');
    }
  };
  return (
    <section
      className="grid-in-toolbar h-12 flex items-center justify-between px-6 border-b bg-white shadow-sm"
      role="region"
      aria-label="Sub Navigation"
    >
      <div className="flex items-center gap-3">
        {/* Route-scoped toolbar actions */}
        {route !== 'agents' && (
          <>
            <button
              onClick={handleAnalyzeClick}
              className="px-3 py-1 text-sm rounded bg-gray-100 text-gray-700 hover:bg-blue-600 hover:text-white"
            >
              Analyze
            </button>
            <button className="px-3 py-1 text-sm rounded bg-gray-100 hover:bg-gray-200">
              Filter
            </button>
            <button
              onClick={async () => {
                if (activeDatasheet) {
                  try {
                    await exportAttributesToCsv(activeDatasheet.id);
                  } catch (err) {
                    console.error('Export failed', err);
                  }
                }
              }}
              className="px-3 py-1 text-sm rounded bg-gray-100 hover:bg-gray-200"
            >
              Export
            </button>
          </>
        )}
        {route === 'agents' && (
          <>
            <button
              onClick={() => setShowNewAgent(true)}
              className="px-3 py-1 text-sm rounded bg-gray-100 text-gray-700 hover:bg-blue-600 hover:text-white"
            >
              New Agent
            </button>
            <button
              onClick={() => window.dispatchEvent(new CustomEvent('of:agents:refresh'))}
              className="px-3 py-1 text-sm rounded bg-gray-100 hover:bg-gray-200"
              title="Refresh agents list"
            >
              Refresh
            </button>
          </>
        )}

        {/* Confirm & Close appears only when a datasheet is open. Disable until dirty */}
        {activeDatasheet && (
          <button
            onClick={handleConfirmClick}
            disabled={!datasheetDirty}
            className={`px-3 py-1 text-sm rounded border border-transparent shadow-sm focus:outline-none ${
              !datasheetDirty
                ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                : 'bg-blue-600 text-white hover:bg-blue-700'
            }`}
          >
            Confirm & Close
          </button>
        )}
        {/* Undo/Redo buttons */}
        <button
          onClick={undo}
          disabled={historyIndex <= 0}
          className="px-2 py-1 text-sm rounded bg-gray-100 hover:bg-gray-200 disabled:opacity-50"
        >
          Undo
        </button>
        <button
          onClick={redo}
          disabled={historyIndex < 0 || historyIndex >= historyLength - 1}
          className="px-2 py-1 text-sm rounded bg-gray-100 hover:bg-gray-200 disabled:opacity-50"
        >
          Redo
        </button>
      </div>
      <div className="text-xs text-gray-500 italic">
        {route === 'agents' ? 'Agents Catalog' : 'Sub-nav active'}
      </div>

      {/* Lightweight modal for creating a new agent via JSON spec (MVP). */}
      {route === 'agents' && showNewAgent && (
        <NewAgentModal onClose={() => setShowNewAgent(false)} />
      )}
    </section>
  );
};

export default Toolbar;

// --- Local modal component (MVP). For larger UX, lift into /components/agents later.
const NewAgentModal: React.FC<{ onClose: () => void }> = ({ onClose }) => {
  const [templates, setTemplates] = React.useState<any[]>([]);
  const [spec, setSpec] = React.useState<string>('');
  const addStatusMessage = useAppStore((s) => s.addStatusMessage);
  React.useEffect(() => {
    (async () => {
      try {
        const res = await fetch('/api/v1/agents/templates');
        const data = await res.json();
        setTemplates(data?.templates ?? []);
        if (data?.templates?.[0]?.spec) {
          setSpec(JSON.stringify(data.templates[0].spec, null, 2));
        }
      } catch {
        // Use a minimal fallback template if server not available
        setTemplates([]);
        setSpec(
          JSON.stringify(
            {
              name: 'custom_agent',
              display_name: 'Custom Agent',
              domain: 'general',
              version: '0.0.1',
              capabilities: ['analyze', 'suggest'],
              risk_class: 'low',
              examples: ['say hello', 'summarize the design'],
            },
            null,
            2,
          ),
        );
      }
    })();
  }, []);
  const handleCreate = async () => {
    try {
      const payload = JSON.parse(spec);
      const resp = await fetch('/api/v1/agents/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!resp.ok) throw new Error(await resp.text());
      addStatusMessage('Agent registered', 'success');
      window.dispatchEvent(new CustomEvent('of:agents:refresh'));
      onClose();
    } catch (err: any) {
      console.error(err);
      addStatusMessage('Failed to register agent', 'error');
      alert(`Invalid spec or server error:\n${err?.message ?? err}`);
    }
  };
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-xl w-[800px] max-w-[95vw] p-4 flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">Create New Agent</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-black">
            ✕
          </button>
        </div>
        <div className="flex gap-3">
          <select
            className="border rounded p-2 text-sm"
            onChange={(e) => {
              try {
                const t = templates.find((t) => t.id === e.target.value);
                if (t?.spec) setSpec(JSON.stringify(t.spec, null, 2));
              } catch {}
            }}
          >
            <option value="">Select a template…</option>
            {templates.map((t) => (
              <option key={t.id} value={t.id}>
                {t.title}
              </option>
            ))}
          </select>
          <div className="text-xs text-gray-500 self-center">
            Start from a template or paste a JSON spec below.
          </div>
        </div>
        <textarea
          className="font-mono text-xs border rounded p-2 h-72 w-full"
          value={spec}
          onChange={(e) => setSpec(e.target.value)}
        />
        <div className="flex justify-end gap-2">
          <button onClick={onClose} className="px-3 py-1 text-sm rounded bg-gray-100 hover:bg-gray-200">
            Cancel
          </button>
          <button onClick={handleCreate} className="px-3 py-1 text-sm rounded bg-blue-600 text-white hover:bg-blue-700">
            Create
          </button>
        </div>
      </div>
    </div>
  );
};
