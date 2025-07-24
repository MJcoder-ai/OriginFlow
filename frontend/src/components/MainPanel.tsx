import React from 'react';
import Workspace from './Workspace';

const MainPanel: React.FC = () => (
  <main className="flex flex-col bg-gray-50 text-black h-full w-full p-2">
    <Workspace />
  </main>
);

export default MainPanel;
