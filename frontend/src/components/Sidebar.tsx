import React from 'react';
import { Box, Book, Settings as SettingsIcon, Bot } from 'lucide-react';
import { useAppStore, Route } from '../appStore';
import { FileStagingArea } from './FileStagingArea';

// Extended navigation to include a Settings view. Each name maps to a route.
const NAV_ITEMS = [
  { name: 'projects', label: 'Projects', icon: Book },
  { name: 'components', label: 'Components', icon: Box },
  { name: 'agents', label: 'Agents', icon: Bot },
  { name: 'settings', label: 'Settings', icon: SettingsIcon },
];

interface Props {
  isCollapsed: boolean;
}

const Sidebar = ({ isCollapsed }: Props) => {
  const currentRoute = useAppStore((s) => s.route);
  const setRoute = useAppStore((s) => s.setRoute);

  return (
    <div className="grid-in-sidebar flex flex-col bg-white text-black border-r border-gray-200">
      <nav className="flex-1 py-4 px-2 mt-2" aria-label="Sidebar navigation">
        <ul className="space-y-1">
          {NAV_ITEMS.map((item) => (
            <li key={item.name}>
              <button
                onClick={() => setRoute(item.name as Route)}
                className={`flex w-full items-center gap-3 p-3 rounded-r-lg transition-colors ${
                  isCollapsed ? 'justify-center' : ''
                } ${currentRoute === item.name ? 'bg-blue-100 text-blue-600' : 'hover:bg-blue-50'}`}
                aria-current={currentRoute === item.name ? 'page' : undefined}
                title={isCollapsed ? item.label : undefined}
              >
                <item.icon className="h-5 w-5" />
                {!isCollapsed && <span>{item.label}</span>}
              </button>
            </li>
          ))}
        </ul>
        {!isCollapsed && <FileStagingArea />}
      </nav>
    </div>
  );
};

export default Sidebar;
