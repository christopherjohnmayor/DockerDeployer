import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@components": path.resolve(__dirname, "src/components"),
      "@pages": path.resolve(__dirname, "src/pages"),
      "@api": path.resolve(__dirname, "src/api"),
      "@store": path.resolve(__dirname, "src/store"),
    },
  },
  server: {
    host: "0.0.0.0",
    port: 3000,
    open: false, // Disable auto-open in Docker
    proxy: {
      "/api": {
        target: "http://backend:8000",
        changeOrigin: true,
        // rewrite: (path) => path.replace(/^\/api/, ''),
      },
      "/auth": {
        target: "http://backend:8000",
        changeOrigin: true,
      },
      "/nlp": {
        target: "http://backend:8000",
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: "dist",
    sourcemap: true,
  },
});
