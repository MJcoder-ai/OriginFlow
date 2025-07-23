import React from 'react';
import { useAppStore } from '../appStore';

const Toolbar: React.FC = () => {
  const analyzeAndExecute = useAppStore((s) => s.analyzeAndExecute);
  return (
    <section
      className="flex items-center justify-between px-4 py-2 border-b bg-gray-50 transition-all duration-300"
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
      </div>
      <div className="text-xs text-gray-500 italic">Sub-nav active</div>
    </section>
  );
};

export default Toolbar;
