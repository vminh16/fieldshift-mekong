import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
    // MapLibre alone is ~1 MB; it is split out and loaded only by map screens.
    chunkSizeWarningLimit: 1100,
    rollupOptions: {
      output: {
        // Big libraries in their own long-cached chunks, shared by whichever screens need them.
        manualChunks(id) {
          if (id.includes('node_modules/three')) return 'three'
          if (id.includes('node_modules/maplibre-gl')) return 'maplibre'
          if (id.includes('node_modules/react') || id.includes('node_modules/scheduler')) return 'react'
        },
      },
    },
  },
  server: { host: '0.0.0.0', port: 5180, strictPort: true },
})
