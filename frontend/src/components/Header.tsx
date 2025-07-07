/**
 * File: frontend/src/components/Header.tsx
 * Top bar component showing global navigation and agent statuses.
 * Includes button to toggle the action bar visibility.
 */
import React from 'react';

/** Props accepted by the Header component. */
interface HeaderProps {
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
const Header: React.FC<HeaderProps> = ({ toggleActionCollapse }) => {
  return (
    <header className="[grid-area:topbar] bg-white border-b border-gray-200 flex items-center px-4 gap-2">
      <div className="bg-gray-100 rounded-md h-8 px-2 flex items-center">GlobalNav_1</div>
      <div className="bg-gray-100 rounded-md h-8 px-2 flex items-center">GlobalNav_2</div>
      <div className="bg-gray-100 rounded-md h-8 px-2 flex items-center">GlobalNav_3</div>
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
