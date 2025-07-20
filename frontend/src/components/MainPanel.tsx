import React from 'react';
import { useAppStore } from '../appStore';
import ProjectCanvas from './ProjectCanvas';
import ComponentCanvas from './ComponentCanvas';

const MainPanel: React.FC = () => {
  const route = useAppStore((s) => s.route);

  return (
    <div className="[grid-area:workspace] bg-gray-100">
      {route === 'projects' && <ProjectCanvas />}
      {route === 'components' && <ComponentCanvas />}
    </div>
  );
};

export default MainPanel;
