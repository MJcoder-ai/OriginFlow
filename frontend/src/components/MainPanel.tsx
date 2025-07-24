import React from 'react';

// The parent wrapper in Layout handles the grid area and scrolling behavior.
const MainPanel: React.FC = () => (
  <main className="flex flex-col bg-gray-900 text-white h-full w-full">
    {/* Placeholder for other routes */}
    <div className="border-2 border-dashed w-full h-full bg-gray-800 rounded-lg m-6 relative">
      <div className="absolute inset-0 flex justify-center items-center text-gray-400">
        Drag components here to start
      </div>
    </div>
  </main>
);

export default MainPanel;
