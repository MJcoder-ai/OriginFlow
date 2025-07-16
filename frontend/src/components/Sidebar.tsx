import React from 'react';
import { FolderKanban, Box, LifeBuoy } from 'lucide-react';
import clsx from 'clsx';
import { useAppStore, Route } from '../appStore';
import { FileStagingArea } from './FileStagingArea';

const Item = ({ label, route, Icon, collapsed }: { label: string; route: Route; Icon?: React.ComponentType<{size?:number}>; collapsed: boolean }) => {
  const setRoute = useAppStore((s) => s.setRoute);
  const active = useAppStore((s) => s.route) === route;
  return (
    <li
      className={clsx('flex items-center p-2 rounded-lg cursor-pointer', active && 'bg-blue-100')}
      onClick={() => setRoute(route)}
    >
      {Icon && <Icon size={20} className="flex-shrink-0" />}
      <span className={clsx('ml-3 transition-opacity duration-200', { 'opacity-0': collapsed })}>{label}</span>
    </li>
  );
};

interface SidebarProps {
  isCollapsed: boolean;
}

const Sidebar: React.FC<SidebarProps> = ({ isCollapsed }) => (
  <aside className="[grid-area:sidebar] bg-white border-r border-gray-200 p-4 flex flex-col">
    <div className="h-14 flex items-center justify-center mb-4">
      <div className="h-10 w-32 bg-gray-100 rounded-md flex items-center justify-center font-bold">Logo_1</div>
    </div>
    <nav className="flex-grow space-y-1">
      <Item label="Projects" route="projects" Icon={FolderKanban} collapsed={isCollapsed} />
      <Item label="Components" route="components" Icon={Box} collapsed={isCollapsed} />
      <FileStagingArea />
    </nav>
    <div className="flex-shrink-0">
      <Item label="Help & Support" route="projects" Icon={LifeBuoy} collapsed={isCollapsed} />
    </div>
  </aside>
);

export default Sidebar;
