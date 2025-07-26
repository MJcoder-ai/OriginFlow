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

// Import styles for annotations and text layer in React‑PDF
// Using the dist folder ensures compatibility with Vite's production build
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';

// Import the PDF.js worker via Vite’s ?url mechanism.  This tells Vite to
// bundle the worker from node_modules and return its URL, ensuring it loads
// correctly in both dev and production.
import pdfWorkerUrl from 'pdfjs-dist/legacy/build/pdf.worker.min.mjs?url';
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
