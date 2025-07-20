import React from 'react';
import { useAppStore } from '../appStore';
import ProjectCanvas from './ProjectCanvas';
import ComponentCanvas from './ComponentCanvas';
import { Resizer } from './Workspace';

const MainPanel: React.FC = () => {
  const route = useAppStore((s) => s.route);

  // Only responsible for rendering the workspace panes. Datasheet overlays
  // are handled at the App level via a portal.
  return (
    <main className="[grid-area:workspace] bg-gray-50 p-4 flex overflow-hidden">
      <div
        id="canvas-area"
        className="flex-grow min-h-0 overflow-auto"
        onClick={() => useAppStore.getState().selectComponent(null)}
      >
        {(() => {
          switch (route) {
            case 'projects':
              return <ProjectCanvas />;
            case 'components':
              return <ComponentCanvas />;
            default:
              return <div className="p-4 text-gray-500">No view selected.</div>;
          }
        })()}
      </div>
      <Resizer />
    </main>
  );
};

export default MainPanel;
