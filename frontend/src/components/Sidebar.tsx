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
    // Remove the fixed width on the sidebar. The width is controlled by the grid
    // in Layout.tsx (64px when collapsed or 250px when expanded). Using h-full
    // allows the sidebar to stretch the full height of its grid row.
    <aside className="grid-in-sidebar flex flex-col bg-white text-black border-r border-gray-200">
      <div
        className={`flex items-center p-4 h-16 border-b border-gray-200 ${isCollapsed ? 'justify-center' : 'justify-start'}`}
      >
        <a href="/" className="flex items-center gap-2">
          <span className="text-2xl">🌀</span>
          {!isCollapsed && <h1 className="text-xl font-bold">OriginFlow</h1>}
        </a>
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
