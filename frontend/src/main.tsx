/**
 * File: frontend/src/main.tsx
 * Entry point mounting the React application to the DOM.
 * Sets up global styles and renders the App component.
 */
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';
import { pdfjs } from 'react-pdf';

// Import styles for annotations and text layer in React‑PDF
// Using the dist folder ensures compatibility with Vite's production build
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';

// Configure PDF.js worker using a CDN URL for compatibility
pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

const rootEl = document.getElementById('root');
const root = rootEl ? ReactDOM.createRoot(rootEl) : null;
if (root) {
  root.render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  );
}
