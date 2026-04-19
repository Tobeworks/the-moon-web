import { defineConfig } from 'astro/config';
import node from '@astrojs/node';
import tailwindcss from '@tailwindcss/vite';
import vue from '@astrojs/vue';

export default defineConfig({
  site: 'https://the-moon-records.de',
  output: 'static',
  integrations: [vue()],
  adapter: node({ mode: 'standalone' }),
  security: {
    checkOrigin: false,
  },
  vite: {
    plugins: [tailwindcss()],
  },
});
