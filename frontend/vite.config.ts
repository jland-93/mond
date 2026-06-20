import react from "@vitejs/plugin-react";
import path from "node:path";
import { defineConfig } from "vite";

// Mond Vite 설정
//
// 라우트 단위 split은 App.tsx의 lazy import로 처리.
// 여기서는 큰 vendor 묶음을 manualChunks로 분리 — 페이지를 옮겨도 vendor 캐시 재사용.
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
  build: {
    // 1MB까지는 경고 안 받기 — three.js Moon3D chunk가 866KB로 큼.
    chunkSizeWarningLimit: 1024,
    rollupOptions: {
      output: {
        // three.js만 별도 chunk로 분리 — Moon3D는 로그인 화면 + 일부에서만 사용.
        // 다른 vendor는 circular dep 회피 위해 단일 vendor chunk로 묶음 — rollup이
        // 자동으로 잘라낸 페이지별 chunk가 작아서 분리 효과는 미미.
        manualChunks: (id) => {
          if (!id.includes("node_modules")) return undefined;
          if (/[/\\](three|@react-three)[/\\]/.test(id)) return "vendor-three";
          return undefined;
        },
      },
    },
  },
});
