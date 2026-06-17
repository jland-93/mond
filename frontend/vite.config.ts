import react from "@vitejs/plugin-react";
import path from "node:path";
import { defineConfig } from "vite";

// 🌙 Mond Vite 설정
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: { "@": path.resolve(__dirname, "src") },
  },
  server: {
    host: true,
    port: 3000,
    // mac/docker volume mount에서 fs event가 안 와 hot reload가 멈춤 — polling으로 보강
    watch: { usePolling: true, interval: 300 },
  },
});
