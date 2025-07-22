import React from 'react';
import { useAppStore } from '../appStore';
import ProjectCanvas from './ProjectCanvas';
import ComponentCanvas from './ComponentCanvas';

const MainPanel: React.FC = () => {
  const route = useAppStore((s) => s.route);

  // Only responsible for rendering the workspace panes. Datasheet overlays
  // are handled at the App level via a portal.
  return (
    <main
      id="canvas-area"
      className="[grid-area:workspace] flex flex-col min-h-0 w-full overflow-hidden bg-gray-50 p-4"
      onClick={() => useAppStore.getState().selectComponent(null)}
    >
      <div className="flex-grow overflow-auto">
        {route === 'projects' ? <ProjectCanvas /> : <ComponentCanvas />}
      </div>
    </main>
  );
};

export default MainPanel;
