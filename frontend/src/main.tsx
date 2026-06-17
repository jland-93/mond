/**
 * 🌙 Mond — 앱 엔트리포인트
 */

import { ConfigProvider, theme } from "antd";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";

import App from "@/App";
import { AuthProvider } from "@/auth/AuthContext";
import { I18nProvider, useI18n } from "@/i18n";
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

const mondTheme = {
  algorithm: theme.darkAlgorithm,
  token: {
    colorPrimary: "#7c8cff",
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
    Layout: { bodyBg: "#0d1421", headerBg: "#141c2f", siderBg: "#0f1626" },
    Card: { colorBgContainer: "#141c2f" },
    Menu: { darkItemBg: "#0f1626" },
  },
};

// antd locale은 i18n 컨텍스트에 따라 변경된다.
function ThemedApp() {
  const { antdLocale } = useI18n();
  return (
    <ConfigProvider theme={mondTheme} locale={antdLocale}>
      <BrowserRouter>
        <AuthProvider>
          <App />
        </AuthProvider>
      </BrowserRouter>
    </ConfigProvider>
  );
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <I18nProvider>
        <ThemedApp />
      </I18nProvider>
    </QueryClientProvider>
  </React.StrictMode>,
);
