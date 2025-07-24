import React, { useState } from 'react';
import Header from './Header';
import Toolbar from './Toolbar';
import Sidebar from './Sidebar';
import ChatPanel from './ChatPanel';
import StatusBar from './StatusBar';
import { ChatInput } from './ChatInput';
import ProjectCanvas from './ProjectCanvas';
import ComponentCanvas from './ComponentCanvas';
import { useAppStore } from '../appStore';

const Layout: React.FC = () => {
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isSubNavVisible, setIsSubNavVisible] = useState(true);
  // Pull the current route from the Zustand store to decide what to render.
  const route = useAppStore((state) => state.route);

  return (
    <div
      // Use h-full so the layout stretches to the height of its parent
      // container. This prevents double scrollbars and keeps the chat input
      // and status bar anchored within the viewport.
      className="grid h-full w-full min-h-0 transition-all duration-300 ease-in-out"
      style={{
        gridTemplateColumns: `${isSidebarCollapsed ? '64px' : '250px'} 1fr 350px`,
        gridTemplateRows: '64px 48px 1fr auto',
        gridTemplateAreas: `
          "sidebar header  chat"
          "sidebar toolbar chat"
          "sidebar main    chat"
          "sidebar status  chatInput"
        `,
      }}
    >
      <Header
        toggleSidebar={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
        toggleToolbar={() => setIsSubNavVisible(!isSubNavVisible)}
      />
      {isSubNavVisible && <Toolbar />}
      <Sidebar isCollapsed={isSidebarCollapsed} />

      {/* Main content: swap between canvases based on the current route */}
      <div className="grid-in-main relative min-h-0 overflow-auto">
        {route === 'components' ? <ComponentCanvas /> : <ProjectCanvas />}
      </div>

      <ChatPanel />
      <ChatInput />
      <StatusBar />
    </div>
  );
};

export default Layout;
