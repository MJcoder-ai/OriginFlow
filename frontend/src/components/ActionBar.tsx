/**
 * File: frontend/src/components/ActionBar.tsx
 * Placeholder action bar housing command buttons and quick tools.
 * Can be collapsed from the header control.
 */
import React from 'react';

/** Props for the ActionBar. */
interface ActionBarProps {
  /** Whether the action bar is collapsed. */
  isCollapsed: boolean;
}

/** Collapsible action bar under the top header. */
const ActionBar: React.FC<ActionBarProps> = ({ isCollapsed }) => {
  return (
    <div className={`[grid-area:action-bar] bg-white border-b border-gray-200 flex items-center px-4 transition-all ${isCollapsed ? 'h-0 overflow-hidden' : 'h-12'}`}>
      {!isCollapsed && (
        <>
          <button className="bg-gray-100 rounded-md h-8 px-2 mr-2">Action_1</button>
          <button className="bg-gray-100 rounded-md h-8 px-2 mr-2">Action_2</button>
          <button className="bg-gray-100 rounded-md h-8 px-2">Action_3</button>
        </>
      )}
    </div>
  );
};

export default ActionBar;
