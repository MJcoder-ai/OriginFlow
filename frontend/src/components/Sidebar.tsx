import React from 'react';
import { HelpCircle, Box, Book } from 'lucide-react';
import { useAppStore, Route } from '../appStore';
import { FileStagingArea } from './FileStagingArea';

const NAV_ITEMS = [
  { name: 'projects', label: 'Projects', icon: Book },
  { name: 'components', label: 'Components', icon: Box },
];

const Sidebar = ({ isCollapsed }: { isCollapsed: boolean }) => {
  const currentRoute = useAppStore((s) => s.route);
  const setRoute = useAppStore((s) => s.setRoute);

  return (
    <aside className="w-[250px] flex flex-col bg-gray-50 border-r [grid-area:sidebar]">
      {/* App icon only – the title now lives in the header */}
      <div className="h-16 flex items-center justify-center border-b">
        <span className="text-2xl">🌀</span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4 px-2" aria-label="Sidebar navigation">
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
        {!isCollapsed && currentRoute === 'projects' && <FileStagingArea />}
      </nav>

    {/* Help aligned to status height */}
    <div className={`py-[12px] border-t px-4 ${isCollapsed ? 'text-center' : ''}`}>
      <a href="#help" className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700">
        <HelpCircle className="h-4 w-4" />
        {!isCollapsed && 'Help & Support'}
      </a>
    </div>
    </aside>
  );
};

export default Sidebar;
