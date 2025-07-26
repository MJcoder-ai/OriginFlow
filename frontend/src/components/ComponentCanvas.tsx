import React from 'react';

/**
 * The designated workspace for parsing new components.
 * This canvas accepts files dragged from the user's local file system.
 */
const ComponentCanvas = () => {
  // The `analyzeAndExecute` function will be used to trigger parsing
  // but it is not directly available here yet. This setup provides the UI
  // and drop handlers. Integration with the store's action is the next step.

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      // TODO: Call an action to upload and parse the file(s)
      console.log('Files dropped on Component Canvas:', e.dataTransfer.files);
      // Example for later:
      // analyzeAndExecute(`Parse the file: ${e.dataTransfer.files[0].name}`);
      e.dataTransfer.clearData();
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault(); // This is necessary to allow dropping
  };

  return (
    <div
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      className="p-4 bg-gray-100 h-full w-full border-2 border-dashed border-gray-400 rounded-lg flex items-center justify-center"
    >
      <p className="text-gray-500">Drop component datasheets here to parse them.</p>
    </div>
  );
};

export default ComponentCanvas;
