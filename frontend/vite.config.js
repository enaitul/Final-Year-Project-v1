import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // The Python dashboard server serves the compiled bundle from its root.
  // Absolute asset URLs keep the app working after a refresh on an SPA route.
  base: '/',
  build: {
    outDir: '../dashboard',
    emptyOutDir: false,
  },
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8050',
      '/benchmark_chart.png': 'http://localhost:8050',
      '/reports': 'http://localhost:8050',
    },
  },
})
