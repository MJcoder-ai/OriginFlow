/**
 * File: frontend/src/main.tsx
 * Entry point mounting the React application to the DOM.
 * Sets up global styles and renders the App component.
 */
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

const rootEl = document.getElementById('root');
const root = rootEl ? ReactDOM.createRoot(rootEl) : null;
if (root) {
  root.render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  );
}
