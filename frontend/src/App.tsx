/**
 * File: frontend/src/App.tsx
 * Root component for the OriginFlow React application.
 * Renders the main layout container.
 */
import React, { useEffect } from 'react';
import Layout from './components/Layout';
import { BomModal } from './components/BomModal';
import { useAppStore } from './appStore';

/** Main application component wrapping the Layout. */
const App: React.FC = () => {
  const { bomItems, setBom, loadUploads } = useAppStore();

  useEffect(() => {
    loadUploads();
  }, [loadUploads]);


  return (
    // Make sure the app container fills the available height so the grid
    // inside Layout can stretch to the full viewport. Without h-full here,
    // the layout can grow taller than the screen and the chat input/status bar
    // may be pushed off-screen.
    <div className="App h-full">
      <Layout />
      {bomItems && <BomModal items={bomItems} onClose={() => setBom(null)} />}
    </div>
  );
};

export default App;
