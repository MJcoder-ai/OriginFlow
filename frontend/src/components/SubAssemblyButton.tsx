import React from 'react';
import { useAppStore } from '../appStore';

const SubAssemblyButton: React.FC = () => {
  const analyzeAndExecute = useAppStore((s) => s.analyzeAndExecute);
  const selectedId = useAppStore((s) => s.selectedComponentId);
  const components = useAppStore((s) => s.canvasComponents);

  const handleClick = () => {
    const comp = components.find((c) => c.id === selectedId);
    if (comp) {
      analyzeAndExecute(`generate sub assembly for ${comp.name}`);
    }
  };

  return (
    <button
      onClick={handleClick}
      disabled={!selectedId}
      className="px-2 py-1 text-sm rounded bg-gray-100 hover:bg-gray-200 disabled:opacity-50"
    >
      Generate Sub-Assembly
    </button>
  );
};

export default SubAssemblyButton;
