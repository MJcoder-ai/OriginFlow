/**
 * File: frontend/src/components/Sidebar.tsx
 * Collapsible sidebar navigation used across the engineer UI.
 * Provides basic placeholder navigation and collapse button.
 */
import React from 'react';

/** Props for the Sidebar component. */
interface SidebarProps {
  /** Whether the sidebar is collapsed. */
  isCollapsed: boolean;
  /** Triggered when the collapse button is clicked. */
  toggleCollapse: () => void;
}

/** Sidebar navigation drawer. */
const Sidebar: React.FC<SidebarProps> = ({ isCollapsed, toggleCollapse }) => {
  return (
    <aside className="[grid-area:sidebar] bg-white border-r border-gray-200 p-2 flex flex-col">
      <button onClick={toggleCollapse} className="bg-gray-100 rounded-md h-8 w-full mb-3 text-gray-600">☰</button>
      <div className={`h-10 bg-gray-100 rounded-md mb-4 flex items-center justify-center transition-opacity ${isCollapsed ? 'opacity-0' : 'opacity-100'}`}>Logo_1</div>
      <nav className="flex-grow">
        {Array.from({ length: 7 }).map((_, i) => (
          <div key={i} className={`h-9 bg-gray-100 rounded-md mb-2 flex items-center justify-center transition-opacity ${isCollapsed ? 'opacity-0' : 'opacity-100'}`}>{`NavItem_${i + 1}`}</div>
        ))}
      </nav>
      <div className={`h-9 bg-gray-100 rounded-md flex items-center justify-center transition-opacity ${isCollapsed ? 'opacity-0' : 'opacity-100'}`}>FooterItem_8</div>
    </aside>
  );
};

export default Sidebar;
