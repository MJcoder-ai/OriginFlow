import React, { useState } from 'react';
import Header from './Header';
import Toolbar from './Toolbar';
import Sidebar from './Sidebar';
import MainPanel from './MainPanel';
import ChatSidebar from './ChatSidebar';
import StatusBar from './StatusBar';

const Layout: React.FC = () => {
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isSubNavVisible, setIsSubNavVisible] = useState(true);

  return (
    <div className="h-screen flex flex-col">
      <div
        className="grid h-full w-full transition-all duration-300 ease-in-out"
        style={{
          gridTemplateColumns: `${isSidebarCollapsed ? '64px' : '250px'} 1fr 350px`,
          gridTemplateRows: '64px 48px 1fr',
          gridTemplateAreas: `
            "header header header"
            "toolbar toolbar toolbar"
            "sidebar main chat"
          `,
        }}
      >
        <header className="grid-in-header">
          <Header
            toggleSidebar={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
            toggleToolbar={() => setIsSubNavVisible(!isSubNavVisible)}
          />
        </header>

        {isSubNavVisible && (
          <div className="grid-in-toolbar">
            <Toolbar />
          </div>
        )}

        <aside
          className={`grid-in-sidebar transition-all duration-300 ease-in-out ${
            isSidebarCollapsed ? 'w-16' : 'w-64'
          }`}
          aria-label="Main navigation"
        >
          <Sidebar isCollapsed={isSidebarCollapsed} />
        </aside>

        <main className="grid-in-main overflow-hidden">
          <MainPanel />
        </main>

        <div className="grid-in-chat max-md:fixed max-md:right-0 max-md:top-0 max-md:h-full max-md:z-50 max-md:shadow-2xl">
          <ChatSidebar />
        </div>
      </div>

      <StatusBar />
    </div>
  );
};

export default Layout;
