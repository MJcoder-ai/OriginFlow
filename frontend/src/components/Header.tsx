import React from 'react';
import { Settings } from 'lucide-react';

const Header = ({ toggleSidebar, toggleToolbar }: { toggleSidebar: () => void; toggleToolbar: () => void }) => (
  <header className="h-16 flex items-center justify-between px-4 bg-white border-b shadow-sm">
    {/* Left: ☰ Toggle only */}
    <div className="flex items-center gap-4">
      <button
        onClick={toggleSidebar}
        className="ml-[4px] p-2 rounded-md hover:bg-gray-100 focus:ring-2 focus:ring-blue-500"
        aria-label="Toggle sidebar"
      >
        ☰
      </button>
    </div>

    {/* Center: Tabs + Gear */}
    <div className="flex items-center gap-4">
      <nav role="tablist" aria-label="Primary navigation" className="flex gap-2">
        {['GlobalNav_1', 'GlobalNav_2', 'GlobalNav_3'].map((tab) => (
          <button
            key={tab}
            role="tab"
            className="px-4 py-2 rounded-md hover:bg-gray-100 aria-selected:bg-blue-100"
            aria-selected={tab === 'GlobalNav_1'}
          >
            {tab}
          </button>
        ))}
      </nav>

      <button
        onClick={toggleToolbar}
        className="p-2 rounded-full hover:bg-gray-100"
        aria-label="Toggle sub-navigation"
        title="Toggle Sub-Nav"
      >
        <Settings className="h-5 w-5" />
      </button>
    </div>

    {/* Right: Avatars */}
    <div className="flex gap-1">
      <span className="h-6 w-6 rounded-full bg-blue-200 text-xs flex items-center justify-center">AI_1</span>
      <span className="h-6 w-6 rounded-full bg-gray-300 text-xs flex items-center justify-center">Eng_1</span>
    </div>
  </header>
);

export default Header;
