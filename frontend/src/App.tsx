/**
 * File: frontend/src/App.tsx
 * Root component for the OriginFlow React application.
 * Renders the main layout container.
 */
import React from 'react';
import Layout from './components/Layout';
import { BomModal } from './components/BomModal';
import { useAppStore } from './appStore';

/** Main application component wrapping the Layout. */
const App: React.FC = () => {
  const { bomItems, setBom } = useAppStore();
  return (
    <div className="App">
      <Layout />
      {bomItems && <BomModal items={bomItems} onClose={() => setBom(null)} />}
    </div>
  );
};

export default App;
