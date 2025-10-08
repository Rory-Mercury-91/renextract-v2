import { svelte } from '@sveltejs/vite-plugin-svelte';
import tailwindcss from '@tailwindcss/vite';
import path from 'path';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [svelte(), tailwindcss()],
  root: '.',
  publicDir: 'public',
  resolve: {
    extensions: ['.js', '.ts', '.svelte', '.json'],
    mainFields: ['browser', 'module', 'jsnext:main', 'jsnext'],
    alias: {
      $components: path.resolve(__dirname, 'src/components'),
      $routes: path.resolve(__dirname, 'src/routes'),
      $lib: path.resolve(__dirname, 'src/lib'),
      $stores: path.resolve(__dirname, 'src/stores'),
    },
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
  server: {
    port: 3000,
    host: true, // Allow external connections
    strictPort: false, // Use another port if 3000 is occupied
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true,
      },
    },
  },
});
