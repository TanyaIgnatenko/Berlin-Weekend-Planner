import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Dev: the SPA runs on :5173 and proxies /api to the FastAPI backend on :8000.
// Build: emits to web/dist, which src/api/app.py serves in production.
export default defineConfig({
  plugins: [react()],
  server: {
    port: Number(process.env.PORT) || 5173,
    proxy: {
      "/api": {
        // 127.0.0.1 (not "localhost") to force IPv4 and avoid colliding with
        // any other service bound to ::1 on the same port.
        target: process.env.VITE_API_TARGET || "http://127.0.0.1:8765",
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: "dist",
  },
});
