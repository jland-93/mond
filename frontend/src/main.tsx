/**
 * 🌙 Mond — 앱 엔트리포인트
 */

import { ConfigProvider, theme } from "antd";
import koKR from "antd/locale/ko_KR";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";

import App from "@/App";
import "@/styles/global.css";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 30_000,
    },
  },
});

// Mond 브랜드 컬러 — docs/assets/brand-guidelines.md 기준
const mondTheme = {
  algorithm: theme.darkAlgorithm,
  token: {
    colorPrimary: "#7c8cff", // 달빛 보라
    colorBgBase: "#0d1421",
    colorBgContainer: "#141c2f",
    colorBgElevated: "#1e293b",
    colorBorder: "#293346",
    colorText: "#f1f5f9",
    colorTextSecondary: "#94a3b8",
    borderRadius: 10,
    fontFamily:
      "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
  },
  components: {
    Layout: {
      bodyBg: "#0d1421",
      headerBg: "#141c2f",
      siderBg: "#0f1626",
    },
    Card: { colorBgContainer: "#141c2f" },
    Menu: { darkItemBg: "#0f1626" },
  },
};

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <ConfigProvider theme={mondTheme} locale={koKR}>
        <BrowserRouter>
          <App />
        </BrowserRouter>
      </ConfigProvider>
    </QueryClientProvider>
  </React.StrictMode>,
);
