import React from 'react';
import Workspace from './Workspace';
import ComponentCanvas from './ComponentCanvas';
import { useAppStore } from '../appStore';
const MainPanel: React.FC = () => {
  const route = useAppStore((s) => s.route);
  return (
    <main className="flex flex-col bg-gray-50 h-full w-full p-2">
      {route === 'projects' && <Workspace />}
      {route === 'components' && <ComponentCanvas />}
    </main>
  );
};

export default MainPanel;
