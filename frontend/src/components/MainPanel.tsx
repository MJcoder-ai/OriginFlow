import React from 'react';
import Workspace from './Workspace';
import ComponentCanvas from './ComponentCanvas';
import SettingsPanel from './SettingsPanel';
import { useAppStore } from '../appStore';

const MainPanel: React.FC = () => {
  const route = useAppStore((s) => s.route);
  const activeDatasheet = useAppStore((s) => s.activeDatasheet);
  return (
    <main className="grid-in-main flex flex-col bg-gray-50 text-black h-full w-full p-2 overflow-hidden">
      {route === 'projects' && <Workspace />}
      {route === 'components' && (
        /* Always render the ComponentCanvas so the droppable area is available. */
        <ComponentCanvas />
      )}
      {route === 'settings' && <SettingsPanel />}
    </main>
  );
};

export default MainPanel;
