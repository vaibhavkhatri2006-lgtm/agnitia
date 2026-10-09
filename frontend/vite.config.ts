import react from '@vitejs/plugin-react'
import path from 'path'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(import.meta.dirname, './src'),
    },
  },
  server: {
    port: 5173,
    host: '127.0.0.1',
    proxy: {
      '/auth': 'http://127.0.0.1:8000',
      '/areas': 'http://127.0.0.1:8000',
      '/services': 'http://127.0.0.1:8000',
      '/analytics': 'http://127.0.0.1:8000',
      '/decision': 'http://127.0.0.1:8000',
      '/recommendations': 'http://127.0.0.1:8000',
      '/simulations': 'http://127.0.0.1:8000',
      '/reports': 'http://127.0.0.1:8000',
      '/planner': 'http://127.0.0.1:8000',
      '/mode': 'http://127.0.0.1:8000',
      '/osm': 'http://127.0.0.1:8000',
      '/health': 'http://127.0.0.1:8000',
    },
  },
})
