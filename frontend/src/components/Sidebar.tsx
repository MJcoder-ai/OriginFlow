import React, { useContext } from 'react';
import { FolderKanban, Box, LifeBuoy, ChevronLeft, ChevronRight } from 'lucide-react';
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
  const { isSidebarCollapsed, toggleSidebar } = useContext(UIContext);

  return (
    <aside
      className={`h-full border-r bg-white transition-all duration-300 ease-in-out flex flex-col ${isSidebarCollapsed ? 'w-[64px]' : 'w-[250px]'}`}
      aria-label="Main navigation"
    >
      <div className="flex items-center justify-end p-2">
        <button
          onClick={toggleSidebar}
          className="p-2 rounded hover:bg-gray-200 focus:outline-none focus-visible:ring"
          aria-label="Toggle Sidebar"
          aria-expanded={!isSidebarCollapsed}
        >
          {isSidebarCollapsed ? <ChevronRight size={20} /> : <ChevronLeft size={20} />}
        </button>
      </div>

      <nav className="flex flex-col gap-2 px-2 py-4 text-sm">
        <SidebarItem icon="📁" label="Projects" route="projects" collapsed={isSidebarCollapsed} />
        <SidebarItem icon="🧩" label="Components" route="components" collapsed={isSidebarCollapsed} />
        <FileStagingArea />
      </nav>

      <div className="mt-auto px-2 py-4">
        <SidebarItem icon="❓" label="Help" route="projects" collapsed={isSidebarCollapsed} />
      </div>
    </aside>
  );
};

export default Sidebar;
