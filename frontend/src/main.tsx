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
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';

// Configure the PDF.js worker to load from the local pdfjs-dist package. Vite
// bundles this worker file so the version always matches react-pdf and avoids
// any external CDN requests that could trigger CORS errors during development.
pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  'pdfjs-dist/legacy/build/pdf.worker.min.js',
  import.meta.url,
).toString();

const rootEl = document.getElementById('root');
const root = rootEl ? ReactDOM.createRoot(rootEl) : null;
if (root) {
  root.render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  );
}
