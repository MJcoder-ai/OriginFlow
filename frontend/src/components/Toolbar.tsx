import React from 'react';
import { useAppStore } from '../appStore';

const Toolbar: React.FC = () => {
  const analyzeAndExecute = useAppStore((s) => s.analyzeAndExecute);
  return (
    <div className="p-2 space-x-2 bg-gray-50 border-b">
      <button
        onClick={() => analyzeAndExecute('validate my design')}
        className="bg-blue-500 text-white px-2 py-1 rounded"
      >
        Analyze
      </button>
    </div>
  );
};

export default Toolbar;
