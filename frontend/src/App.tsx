/**
 * File: frontend/src/App.tsx
 * Root component for the OriginFlow React application.
 * Renders the main layout container.
 */
import React from 'react';
import Layout from './components/Layout';

/** Main application component wrapping the Layout. */
const App: React.FC = () => (
  <div className="App">
    <Layout />
  </div>
);

export default App;
