import React from 'react';
import { useAppStore } from '../appStore';
import { exportAttributesToCsv } from '../utils/exportCsv';
import { reanalyze } from '../services/attributesApi';

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

  const handleAnalyzeClick = async () => {
    // If a datasheet is currently open, trigger re-analysis of that datasheet
    if (activeDatasheet) {
      const confirm = window.confirm(
        'Re-analysing will discard extracted images and metadata. Continue?'
      );
      if (!confirm) return;
      try {
        // Show an info status message
        addStatusMessage('Re-analysing datasheet...', 'info');
        await reanalyze(activeDatasheet.id);
        // Close the datasheet view; it will reopen once parsing completes via polling
        setActiveDatasheet(null);
        setRoute('components');
      } catch (err: any) {
        console.error('Failed to reanalyze datasheet', err);
        addStatusMessage('Re-Analyze failed', 'error');
      }
    } else {
      // Otherwise run the AI design validation
      analyzeAndExecute('validate my design');
    }
  };
  return (
    <section
      className="grid-in-toolbar h-12 flex items-center justify-between px-6 border-b bg-white shadow-sm"
      role="region"
      aria-label="Sub Navigation"
    >
      <div className="flex items-center gap-3">
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
