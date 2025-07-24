import React, { useState } from 'react';
import Header from './Header';
import Toolbar from './Toolbar';
import Sidebar from './Sidebar';
import ChatSidebar from './ChatSidebar';
import StatusBar from './StatusBar';
import MainPanel from './MainPanel';
import { ChatInput } from './ChatInput';

const Layout: React.FC = () => {
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isSubNavVisible, setIsSubNavVisible] = useState(true);

  return (
    <div
      className="grid h-screen w-screen transition-all duration-300 ease-in-out"
      style={{
        gridTemplateColumns: `${isSidebarCollapsed ? '64px' : '250px'} 1fr 350px`,
        gridTemplateRows: '64px 48px 1fr auto',
        gridTemplateAreas: `
          "header header header"
          "toolbar toolbar toolbar"
          "sidebar main chat"
          "status status chatInput"
        `,
      }}
    >
      <Header
        toggleSidebar={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
        toggleToolbar={() => setIsSubNavVisible(!isSubNavVisible)}
      />
      {isSubNavVisible && <Toolbar />}
      <Sidebar isCollapsed={isSidebarCollapsed} />
      <MainPanel />
      <ChatSidebar />
      <StatusBar />
      <ChatInput />
    </div>
  );
};

export default Layout;
