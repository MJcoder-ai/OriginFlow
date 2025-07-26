import React from 'react';
import { useAppStore } from '../appStore';
import { File as FileIcon } from 'lucide-react';

const StagedFiles: React.FC = () => {
  const { stagedFiles } = useAppStore();

  const handleDragStart = (e: React.DragEvent<HTMLDivElement>, file: File) => {
    e.dataTransfer.setData(
      'application/json',
      JSON.stringify({ type: 'file', name: file.name }),
    );
  };

  if (stagedFiles.length === 0) {
    return null;
  }

  return (
    <div className="p-4 border-t border-gray-200">
      <h3 className="text-md font-semibold mb-2">Staged Files</h3>
      <div className="space-y-2">
        {stagedFiles.map((file, index) => (
          <div
            key={index}
            className="flex items-center p-2 bg-white rounded-md shadow-sm cursor-grab"
            draggable="true"
            onDragStart={(e) => handleDragStart(e, file)}
          >
            <FileIcon className="h-5 w-5 mr-2 text-gray-500" />
            <span className="text-sm truncate">{file.name}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default StagedFiles;
