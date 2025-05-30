import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";

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
    watch: {
      usePolling: true, // Enable polling for Docker volume mounts
    },
    proxy: {
      "/api": {
        target: process.env.DOCKER_ENV
          ? "http://backend:8000"
          : "http://localhost:8000",
        changeOrigin: true,
        secure: false,
        // rewrite: (path) => path.replace(/^\/api/, ''),
      },
      "/auth": {
        target: process.env.DOCKER_ENV
          ? "http://backend:8000"
          : "http://localhost:8000",
        changeOrigin: true,
        secure: false,
      },
      "/nlp": {
        target: process.env.DOCKER_ENV
          ? "http://backend:8000"
          : "http://localhost:8000",
        changeOrigin: true,
        secure: false,
      },
      "/ws": {
        target: process.env.DOCKER_ENV
          ? "ws://backend:8000"
          : "ws://localhost:8000",
        ws: true,
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: "dist",
    sourcemap: true,
  },
});
