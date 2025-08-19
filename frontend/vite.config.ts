/**
 * File: frontend/vite.config.ts
 * Configuration for Vite bundler to build OriginFlow's UI.
 * Enables React and Tailwind CSS support.
 */
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    open: true,
  },
  define: {
    global: 'globalThis',
  },
  resolve: {
    alias: {
      'web-worker': 'web-worker',
    },
  },
  optimizeDeps: {
    include: ['web-worker'],
  },
  build: {
    rollupOptions: {
      external: [],
    },
  },
});
