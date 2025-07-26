/**
 * File: frontend/src/main.tsx
 * Entry point mounting the React application to the DOM.
 * Sets up global styles and renders the App component.
 */
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.tsx';
import './index.css';
import { pdfjs } from 'react-pdf';

// Use the ESM styles for React‑PDF 10.
import 'react-pdf/dist/esm/Page/AnnotationLayer.css';
import 'react-pdf/dist/esm/Page/TextLayer.css';

// Import the PDF.js worker via Vite’s ?url mechanism.  This tells Vite to
// bundle the worker from node_modules and return its URL, ensuring it loads
// correctly in both dev and production.
import pdfWorkerUrl from 'pdfjs-dist/legacy/build/pdf.worker.min.js?url';
pdfjs.GlobalWorkerOptions.workerSrc = pdfWorkerUrl;

const rootEl = document.getElementById('root');
const root = rootEl ? ReactDOM.createRoot(rootEl) : null;
if (root) {
  root.render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  );
}
