import { useAppStore } from '../appStore';
import ProjectCanvas from './ProjectCanvas';
import ComponentCanvas from './ComponentCanvas';

const MainPanel = () => {
  const route = useAppStore((s) => s.route);
  switch (route) {
    case 'projects':
      return <ProjectCanvas />;
    case 'components':
      return <ComponentCanvas />;
    default:
      return null;
  }
};

export default MainPanel;
