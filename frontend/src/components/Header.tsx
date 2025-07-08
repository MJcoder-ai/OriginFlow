/**
 * File: frontend/src/components/Header.tsx
 * Top bar component showing global navigation and agent statuses.
 * Includes buttons to toggle the sidebar and action bar visibility.
 */
import React from 'react';
import { Menu } from 'lucide-react';

/** Props accepted by the Header component. */
interface HeaderProps {
  /** Current collapsed state of the sidebar */
  isNavCollapsed: boolean;
  /** Toggle handler for collapsing the sidebar. */
  toggleNavCollapse: () => void;
  /** Toggle handler for collapsing the action bar. */
  toggleActionCollapse: () => void;
}

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
const Header: React.FC<HeaderProps> = ({
  isNavCollapsed,
  toggleNavCollapse,
  toggleActionCollapse,
}) => {
  return (
    <header className="[grid-area:topbar] bg-white border-b border-gray-200 flex items-center px-4 gap-4">
      <button onClick={toggleNavCollapse} className="text-gray-500 hover:text-gray-800">
        <Menu size={24} />
      </button>
      <div className="bg-gray-100 rounded-md h-8 px-3 flex items-center text-sm">GlobalNav_1</div>
      <div className="bg-gray-100 rounded-md h-8 px-3 flex items-center text-sm">GlobalNav_2</div>
      <div className="bg-gray-100 rounded-md h-8 px-3 flex items-center text-sm">GlobalNav_3</div>
      <div className="flex-grow" />
      <AgentStatus name="Eng_1" />
      <AgentStatus name="Eng_2" isOffline />
      <AgentStatus name="AI_1" />
      <AgentStatus name="AI_2" isOffline />
      <button onClick={toggleActionCollapse} className="bg-gray-100 rounded-md h-8 w-8 flex items-center justify-center text-lg ml-2">⚙︎</button>
    </header>
  );
};

export default Header;
