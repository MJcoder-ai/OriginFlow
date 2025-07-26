import React from 'react';
import { useAppStore } from '../appStore';

const Workflow: React.FC = () => {
  const analyzeAndExecute = useAppStore((s) => s.analyzeAndExecute);

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    const data = e.dataTransfer.getData('application/json');
    if (data) {
      const { type, name } = JSON.parse(data);
      if (type === 'file') {
        const dropX = e.clientX;
        const dropY = e.clientY;
        analyzeAndExecute(
          `Parse the file "${name}" and place the components at coordinates (${dropX}, ${dropY}).`,
        );
      }
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
  };

  return (
    <div className="flex-1 bg-white" onDrop={handleDrop} onDragOver={handleDragOver}>
      <div className="p-8 text-center text-gray-400">
        <p>Drop files here to begin parsing</p>
      </div>
    </div>
  );
};

export default Workflow;
