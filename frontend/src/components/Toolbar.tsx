import React from 'react';
import { useAppStore } from '../appStore';

const Toolbar: React.FC = () => {
  const analyzeAndExecute = useAppStore((s) => s.analyzeAndExecute);
  const undo = useAppStore((s) => s.undo);
  const redo = useAppStore((s) => s.redo);
  const historyIndex = useAppStore((s) => s.historyIndex);
  const historyLength = useAppStore((s) => s.history.length);
  return (
    <section
      className="grid-in-toolbar h-12 flex items-center justify-between px-6 border-b bg-white shadow-sm"
      role="region"
      aria-label="Sub Navigation"
    >
      <div className="flex items-center gap-3">
        <button
          onClick={() => analyzeAndExecute('validate my design')}
          className="px-3 py-1 text-sm rounded bg-blue-600 text-white hover:bg-blue-700"
        >
          Analyze
        </button>
        <button className="px-3 py-1 text-sm rounded bg-gray-100 hover:bg-gray-200">
          Filter
        </button>
        <button className="px-3 py-1 text-sm rounded bg-gray-100 hover:bg-gray-200">
          Export
        </button>
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
      <div className="text-xs text-gray-500 italic">Sub-nav active</div>
    </section>
  );
};

export default Toolbar;
