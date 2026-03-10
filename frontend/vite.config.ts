import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'
import { FRONTEND_DEV_HOST, FRONTEND_DEV_PORT } from './config/ports.mjs'

export default defineConfig({
  plugins: [vue(), tailwindcss()],
  server: {
    host: FRONTEND_DEV_HOST,
    port: FRONTEND_DEV_PORT,
    strictPort: true,
  },
  preview: {
    host: FRONTEND_DEV_HOST,
    port: FRONTEND_DEV_PORT,
    strictPort: true,
  },
})
