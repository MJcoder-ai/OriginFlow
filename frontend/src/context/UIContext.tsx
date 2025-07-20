import React, { createContext, useState, ReactNode } from 'react';

interface UIState {
  isSidebarCollapsed: boolean;
  isSubNavVisible: boolean;
  toggleSidebar: () => void;
  toggleSubNav: () => void;
}

export const UIContext = createContext<UIState>({
  isSidebarCollapsed: false,
  isSubNavVisible: true,
  toggleSidebar: () => {},
  toggleSubNav: () => {},
});

export const UIProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isSubNavVisible, setIsSubNavVisible] = useState(true);

  const toggleSidebar = () => setIsSidebarCollapsed((v) => !v);
  const toggleSubNav = () => setIsSubNavVisible((v) => !v);

  return (
    <UIContext.Provider
      value={{ isSidebarCollapsed, isSubNavVisible, toggleSidebar, toggleSubNav }}
    >
      {children}
    </UIContext.Provider>
  );
};
