// @ts-check
import { defineConfig } from 'astro/config';
import node from '@astrojs/node';
import tailwindcss from '@tailwindcss/vite';

// SSR con servidor Node standalone (lo ejecuta PM2 detrás de NGINX).
// Las páginas de contenido se prerenderizan con `export const prerender = true`.
export default defineConfig({
  site: 'https://amurb.com.mx',
  output: 'server',
  adapter: node({ mode: 'standalone' }),
  vite: {
    plugins: [tailwindcss()],
  },
});
