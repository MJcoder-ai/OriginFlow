/**
 * File: frontend/src/components/Layout.tsx
 * Provides the application layout using CSS Grid with collapsible sidebar
 * and action bar sections for responsive engineer UI.
 */
import React, { useState } from 'react';
import Sidebar from './Sidebar';
import Header from './Header';
import ActionBar from './ActionBar';
import Workspace from './Workspace';
import StatusBar from './StatusBar';

/**
 * Main layout component orchestrating structural UI elements.
 */
const Layout: React.FC = () => {
  const [isNavCollapsed, setIsNavCollapsed] = useState<boolean>(false);
  const [isActionCollapsed, setIsActionCollapsed] = useState<boolean>(false);

  return (
    <div
      className={`grid h-screen transition-all duration-200 \
        ${isNavCollapsed ? 'grid-cols-[60px_1fr]' : 'grid-cols-[180px_1fr]'} \
        ${isActionCollapsed ? 'grid-rows-[48px_0_1fr_40px]' : 'grid-rows-[48px_48px_1fr_40px]'}
        grid-areas-layout-desktop`}
    >
      <Sidebar isCollapsed={isNavCollapsed} toggleCollapse={() => setIsNavCollapsed(!isNavCollapsed)} />
      <Header toggleActionCollapse={() => setIsActionCollapsed(!isActionCollapsed)} />
      <ActionBar isCollapsed={isActionCollapsed} />
      <Workspace />
      <StatusBar />
    </div>
  );
};

export default Layout;
