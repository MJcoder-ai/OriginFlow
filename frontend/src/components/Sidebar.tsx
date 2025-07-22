import React, { useContext } from 'react';
import { FolderKanban, Box, LifeBuoy } from 'lucide-react';
import clsx from 'clsx';
import { useAppStore, Route } from '../appStore';
import { FileStagingArea } from './FileStagingArea';
import { UIContext } from '../context/UIContext';

const SidebarItem = ({ label, route, Icon, collapsed }: { label: string; route: Route; Icon?: React.ComponentType<{ size?: number }>; collapsed: boolean }) => {
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

const Sidebar: React.FC = () => {
  const { isSidebarCollapsed } = useContext(UIContext);

  return (
    <aside
      className={`h-full border-r bg-white transition-all duration-300 ease-in-out flex flex-col ${isSidebarCollapsed ? 'w-[64px]' : 'w-[250px]'}`}
      aria-label="Main navigation"
    >
      <div className="flex items-center justify-center h-[64px] font-bold text-lg border-b">
        {isSidebarCollapsed ? '🌀' : 'OriginFlow'}
      </div>

      <nav className="flex flex-col gap-2 px-2 py-4 text-sm">
        <SidebarItem Icon={FolderKanban} label="Projects" route="projects" collapsed={isSidebarCollapsed} />
        <SidebarItem Icon={Box} label="Components" route="components" collapsed={isSidebarCollapsed} />
        <FileStagingArea />
      </nav>

      <div className="mt-auto px-2 py-4">
        <SidebarItem Icon={LifeBuoy} label="Help" route="projects" collapsed={isSidebarCollapsed} />
      </div>
    </aside>
  );
};

export default Sidebar;
