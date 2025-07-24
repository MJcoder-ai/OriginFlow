import React from 'react';
import { Settings, PanelLeftClose } from 'lucide-react';

const Header = ({ toggleSidebar, toggleToolbar }: { toggleSidebar: () => void; toggleToolbar: () => void }) => (
  <header className="grid-in-header h-16 flex items-center justify-between px-4 bg-white text-black border-b border-gray-200">
    {/* Left: ☰ Toggle and App name */}
    <div className="flex items-center gap-2">
      <button
        onClick={toggleSidebar}
        className="p-2 rounded-md hover:bg-gray-100 focus:ring-2 focus:ring-blue-500"
        aria-label="Toggle sidebar"
      >
        <PanelLeftClose size={24} />
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
