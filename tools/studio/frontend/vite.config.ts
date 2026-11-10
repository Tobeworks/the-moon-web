import vue from '@vitejs/plugin-vue';
import { fileURLToPath, URL } from 'node:url';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [vue()],
  resolve: { alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) } },
  // Entwicklung: `pnpm dev` (5173); die API kommt vom laufenden `tmr studio` (Standard 8777).
  // Das Cookie von 127.0.0.1:8777 gilt auch für :5173, einmal die Studio-Adresse mit ?key= öffnen.
  server: { proxy: { '/api': 'http://127.0.0.1:8777' } },
  build: { outDir: '../dist', emptyOutDir: true },
});
