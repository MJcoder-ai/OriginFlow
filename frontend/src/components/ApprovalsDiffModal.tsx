import React from 'react';

type Diff = {
  added_nodes: any[];
  removed_nodes: any[];
  modified_nodes: any[];
  added_edges: any[];
  removed_edges: any[];
};

type Props = {
  open: boolean;
  onClose: () => void;
  loading: boolean;
  error?: string | null;
  beforeGraph?: any | null;
  afterGraph?: any | null;
  note?: string | null;
  diff?: Diff | null;
  onApproveAndApply?: () => void;
};

export default function ApprovalsDiffModal({
  open,
  onClose,
  loading,
  error,
  beforeGraph,
  afterGraph,
  note,
  diff,
  onApproveAndApply,
}: Props) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center">
      <div className="bg-white rounded-xl w-[90vw] max-w-[1200px] max-h-[85vh] overflow-hidden shadow-xl border">
        <div className="px-4 py-3 border-b flex items-center justify-between">
          <div className="font-semibold">Action Impact Preview</div>
          <div className="flex items-center gap-2">
            <button
              onClick={onApproveAndApply}
              className="px-3 py-1 rounded bg-emerald-600 text-white"
            >
              Approve & Apply
            </button>
            <button onClick={onClose} className="px-3 py-1 rounded bg-gray-200">
              Close
            </button>
          </div>
        </div>
        <div className="p-4 space-y-3 overflow-auto">
          {loading && <div className="text-sm text-gray-600">Loading preview…</div>}
          {error && <div className="text-sm text-red-600">{error}</div>}
          {!loading && !error && (
            <>
              {note && <div className="text-sm text-gray-600">Note: {note}</div>}
              <div className="grid grid-cols-2 gap-4">
                <div className="border rounded p-2">
                  <div className="text-xs font-medium text-gray-500 mb-1">
                    Before (latest snapshot)
                  </div>
                  <div className="text-xs font-mono whitespace-pre-wrap overflow-auto max-h-[40vh]">
                    <pre>{JSON.stringify(beforeGraph || { nodes: [], edges: [] }, null, 2)}</pre>
                  </div>
                </div>
                <div className="border rounded p-2">
                  <div className="text-xs font-medium text-gray-500 mb-1">
                    After (simulated)
                  </div>
                  <div className="text-xs font-mono whitespace-pre-wrap overflow-auto max-h-[40vh]">
                    <pre>{JSON.stringify(afterGraph || { nodes: [], edges: [] }, null, 2)}</pre>
                  </div>
                </div>
              </div>
              <div className="border rounded p-2">
                <div className="text-xs font-medium text-gray-500 mb-2">Changes</div>
                <div className="grid grid-cols-5 gap-2 text-xs">
                  <div>
                    <span className="font-semibold">Added nodes:</span>{' '}
                    {diff?.added_nodes?.length ?? 0}
                  </div>
                  <div>
                    <span className="font-semibold">Removed nodes:</span>{' '}
                    {diff?.removed_nodes?.length ?? 0}
                  </div>
                  <div>
                    <span className="font-semibold">Modified nodes:</span>{' '}
                    {diff?.modified_nodes?.length ?? 0}
                  </div>
                  <div>
                    <span className="font-semibold">Added edges:</span>{' '}
                    {diff?.added_edges?.length ?? 0}
                  </div>
                  <div>
                    <span className="font-semibold">Removed edges:</span>{' '}
                    {diff?.removed_edges?.length ?? 0}
                  </div>
                </div>
                <div className="mt-2 grid grid-cols-2 gap-4">
                  <div>
                    <div className="font-semibold text-xs mb-1">Node & Edge Additions</div>
                    <div className="text-xs font-mono whitespace-pre-wrap max-h-[25vh] overflow-auto">
                      <pre>
                        {JSON.stringify(
                          {
                            added_nodes: diff?.added_nodes || [],
                            added_edges: diff?.added_edges || [],
                          },
                          null,
                          2
                        )}
                      </pre>
                    </div>
                  </div>
                  <div>
                    <div className="font-semibold text-xs mb-1">
                      Node & Edge Removals / Modifications
                    </div>
                    <div className="text-xs font-mono whitespace-pre-wrap max-h-[25vh] overflow-auto">
                      <pre>
                        {JSON.stringify(
                          {
                            removed_nodes: diff?.removed_nodes || [],
                            removed_edges: diff?.removed_edges || [],
                            modified_nodes: diff?.modified_nodes || [],
                          },
                          null,
                          2
                        )}
                      </pre>
                    </div>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

