import { useAppStore } from '../appStore';
import ProjectCanvas from './ProjectCanvas';
import ComponentCanvas from './ComponentCanvas';
import PropertiesPanel from './PropertiesPanel';
import { Resizer } from './Workspace';

const MainPanel = () => {
  const route = useAppStore((s) => s.route);
  return (
    <main className="[grid-area:workspace] bg-gray-50 p-4 flex overflow-auto">
      <div className="flex-grow h-full relative">
        {(() => {
          switch (route) {
            case 'projects':
              return <ProjectCanvas />;
            case 'components':
              return <ComponentCanvas />;
          }
        })()}
      </div>
      <Resizer />
      <div className="w-[300px]">
        <PropertiesPanel />
      </div>
    </main>
  );
};

export default MainPanel;
