/**
 * File: frontend/src/components/Header.tsx
 * Top bar component showing global navigation and agent statuses.
 * Includes buttons to toggle the sidebar and action bar visibility.
 */
import React, { useContext } from 'react';
import { Menu, Settings } from 'lucide-react';
import { UIContext } from '../context/UIContext';

/** Props accepted by the Header component. */
/** Props for the AgentStatus subcomponent. */
interface AgentStatusProps {
  /** Display name abbreviation. */
  name: string;
  /** Optional flag to mark the agent offline. */
  isOffline?: boolean;
}

/** Display a round badge representing agent status. */
const AgentStatus: React.FC<AgentStatusProps> = ({ name, isOffline }) => (
  <div className={`w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center text-xs font-semibold ${isOffline ? 'opacity-30' : ''}`}>{name}</div>
);

/** Header containing global navigation and agent indicators. */
const Header: React.FC = () => {
  const { toggleSidebar, isSubNavVisible, toggleSubNav } = useContext(UIContext);
  return (
    <header className="[grid-area:topbar] bg-white border-b shadow-sm flex items-center justify-between h-[64px] px-4">
      <div className="flex items-center gap-6">
        <button onClick={toggleSidebar} aria-label="Toggle Sidebar" className="text-gray-500 hover:text-gray-800">
          <Menu size={24} />
        </button>
        <nav role="tablist" className="flex items-center gap-4">
          <button role="tab" className="text-sm font-medium text-gray-700 hover:text-black">GlobalNav_1</button>
          <button role="tab" className="text-sm font-medium text-gray-700 hover:text-black">GlobalNav_2</button>
          <button role="tab" className="text-sm font-medium text-gray-700 hover:text-black">GlobalNav_3</button>
        </nav>
      </div>

      <div className="flex items-center gap-4">
        <button
          onClick={toggleSubNav}
          aria-label="Toggle Sub Navigation"
          aria-pressed={isSubNavVisible}
          title="Toggle Sub-Nav"
          className={`transition-transform hover:rotate-90 ${isSubNavVisible ? 'text-blue-600' : 'text-gray-600'}`}
        >
          <Settings size={20} />
        </button>
      </div>
    </header>
  );
};

export default Header;
