import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/auth': 'http://localhost:8000',
      '/server': 'http://localhost:8000',
      '/users': 'http://localhost:8000',
      '/minecraft': 'http://localhost:8000',
      '/backups': 'http://localhost:8000',
      '/metrics': 'http://localhost:8000',
      '/health': 'http://localhost:8000',
    },
  },
})

