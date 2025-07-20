/**
 * File: frontend/src/App.tsx
 * Root component for the OriginFlow React application.
 * Renders the main layout container.
 */
import React, { useEffect } from 'react';
import Layout from './components/Layout';
import { BomModal } from './components/BomModal';
import { useAppStore } from './appStore';
import { UIProvider } from './context/UIContext';

/** Main application component wrapping the Layout. */
const App: React.FC = () => {
  const { bomItems, setBom, loadUploads } = useAppStore();

  useEffect(() => {
    loadUploads();
  }, [loadUploads]);


  return (
    <div className="App">
      <UIProvider>
        <Layout />
      </UIProvider>
      {bomItems && <BomModal items={bomItems} onClose={() => setBom(null)} />}
    </div>
  );
};

export default App;
