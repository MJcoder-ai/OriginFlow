import React from 'react';
import Workspace from './Workspace';
import ComponentCanvas from './ComponentCanvas';
import { useAppStore } from '../appStore';

const MainPanel: React.FC = () => {
  const route = useAppStore((s) => s.route);
  const activeDatasheet = useAppStore((s) => s.activeDatasheet);
  return (
    <main className="grid-in-main flex flex-col bg-gray-50 text-black h-full w-full p-2 overflow-hidden">
      {route === 'projects' && <Workspace />}
      {route === 'components' &&
        (activeDatasheet ? (
          <ComponentCanvas />
        ) : (
          <div className="flex-1 flex items-center justify-center text-gray-400 border-2 border-dashed rounded-lg">
            Drag or select a datasheet from the library to start parsing.
          </div>
        ))}
    </main>
  );
};

export default MainPanel;
