/**
 * File: frontend/src/components/ActionBar.tsx
 * Placeholder action bar housing command buttons and quick tools.
 * Can be collapsed from the header control.
 */
import React, { useContext } from 'react';
import Toolbar from './Toolbar';
import { UIContext } from '../context/UIContext';

/** Props for the ActionBar. */
/** Collapsible action bar under the top header. */
const ActionBar: React.FC = () => {
  const { isSubNavVisible } = useContext(UIContext);
  return (
    <div
      className={`[grid-area:action-bar] bg-white border-b border-gray-200 flex items-center px-4 transition-all ${isSubNavVisible ? 'h-12' : 'h-0 overflow-hidden'}`}
    >
      {isSubNavVisible && <Toolbar />}
    </div>
  );
};

export default ActionBar;
