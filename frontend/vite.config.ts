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
  },
});
