import React from 'react';

const MainPanel = () => (
  <main className="overflow-auto bg-gray-100">
    <div className="border-2 border-dashed border-gray-300 min-w-[2000px] min-h-[1200px] bg-grid-pattern m-6 relative">
      <div className="absolute inset-0 flex justify-center items-center text-gray-400">
        Drag components here to start
      </div>
    </div>
  </main>
);

export default MainPanel;
