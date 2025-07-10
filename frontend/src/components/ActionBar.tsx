/**
 * File: frontend/src/components/ActionBar.tsx
 * Placeholder action bar housing command buttons and quick tools.
 * Can be collapsed from the header control.
 */
import React from 'react';
import Toolbar from './Toolbar';

/** Props for the ActionBar. */
interface ActionBarProps {
  /** Whether the action bar is collapsed. */
  isCollapsed: boolean;
}

/** Collapsible action bar under the top header. */
const ActionBar: React.FC<ActionBarProps> = ({ isCollapsed }) => {
  return (
    <div className={`[grid-area:action-bar] bg-white border-b border-gray-200 flex items-center px-4 transition-all ${isCollapsed ? 'h-0 overflow-hidden' : 'h-12'}`}>
      {!isCollapsed && <Toolbar />}
    </div>
  );
};

export default ActionBar;
