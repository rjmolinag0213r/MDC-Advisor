import path from 'path';
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

// API keys stay on the Flask backend. The dev server proxies /api and /health to it,
// so the browser never sees a key and no CORS setup is needed locally.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 3000,
    host: '127.0.0.1',
    proxy: {
      '/api': 'http://127.0.0.1:5000',
      '/health': 'http://127.0.0.1:5000',
    },
  },
  resolve: { alias: { '@': path.resolve(__dirname, '.') } },
});
