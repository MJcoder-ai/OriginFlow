import React from 'react';
import { HelpCircle, Box, Book } from 'lucide-react';

const NAV_ITEMS = [
  { name: 'Projects', icon: Book, href: '#projects' },
  { name: 'Components', icon: Box, href: '#components' },
];

const Sidebar = ({ isCollapsed }: { isCollapsed: boolean }) => (
  <aside className="w-[250px] flex flex-col bg-gray-50 border-r">
    {/* Logo + Title */}
    <div className="h-16 flex items-center justify-center border-b text-xl font-bold">
      🌀 {!isCollapsed && <span className="ml-2">OriginFlow</span>}
    </div>

    {/* Navigation */}
    <nav className="flex-1 py-4 px-2" aria-label="Sidebar navigation">
      <ul className="space-y-1">
        {NAV_ITEMS.map((item) => (
          <li key={item.name}>
            <a
              href={item.href}
              className={`flex items-center gap-3 p-3 rounded-r-lg transition-colors ${
                isCollapsed ? 'justify-center' : ''
              } hover:bg-blue-50`}
              aria-current={item.name === 'Projects' ? 'page' : undefined}
              title={isCollapsed ? item.name : undefined}
            >
              <item.icon className="h-5 w-5" />
              {!isCollapsed && <span>{item.name}</span>}
            </a>
          </li>
        ))}
      </ul>
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

export default Sidebar;
