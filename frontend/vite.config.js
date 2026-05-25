import { defineConfig } from 'vite'
import vue        from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [
    vue(),
    tailwindcss(),   // Tailwind v4 — no tailwind.config.js needed
  ],
})
