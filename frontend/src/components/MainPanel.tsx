import React from 'react';

const MainPanel: React.FC = () => (
  <main className="overflow-auto bg-gray-100 [grid-area:main]">
    {/* Placeholder for other routes: allow the panel to grow naturally without forcing a huge scrollable area */}
    <div className="border-2 border-dashed w-full h-full bg-white rounded-lg m-6 relative">
      <div className="absolute inset-0 flex justify-center items-center text-gray-400">
        Drag components here to start
      </div>
    </div>
  </main>
);

export default MainPanel;
