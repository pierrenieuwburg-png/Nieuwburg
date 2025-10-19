import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path'; // Import the 'path' module

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  base: '/static/admin-assets/', // Ensures assets are loaded relative to this path
  build: {
    // Output directory relative to the project root (admin-frontend)
    outDir: path.resolve(__dirname, '../static/admin-assets'),
    assetsDir: '', // Assets will be directly in outDir
    emptyOutDir: true, // Clears the directory before building
    manifest: true, // Optional: useful for more advanced integrations
    rollupOptions: {
      input: path.resolve(__dirname, 'src/main.jsx'), // Ensure this points to your entry file
      output: {
          entryFileNames: 'index.js', // Consistent JS filename
          chunkFileNames: 'index.js', // Or configure chunking if needed
          assetFileNames: 'index.css', // Consistent CSS filename
      }
    },
  },
  server: {
    // Optional: Configure dev server proxy if needed later to talk to Flask API
    // proxy: {
    //   '/api': 'http://127.0.0.1:5000' // Your Flask backend URL
    // }
  }
});