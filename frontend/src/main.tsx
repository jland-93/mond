/**
 * Mond — 앱 엔트리포인트
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

// CSS variables가 단일 진실 원천. antd token은 그걸 참조.
// cssVar:true → antd 토큰도 CSS variable로 출력, hashed:false → 클래스 해시 제거.
const mondTheme = {
  algorithm: theme.darkAlgorithm,
  cssVar: true,
  hashed: false,
  token: {
    colorPrimary: "var(--mond-primary)",
    colorBgBase: "var(--mond-surface-0)",
    colorBgContainer: "var(--mond-surface-1)",
    colorBgElevated: "var(--mond-surface-2)",
    colorBorder: "var(--mond-border)",
    colorBorderSecondary: "var(--mond-border)",
    colorText: "var(--mond-text)",
    colorTextSecondary: "var(--mond-text-dim)",
    colorTextTertiary: "var(--mond-text-muted)",
    colorSuccess: "var(--severity-low)",
    colorWarning: "var(--severity-high)",
    colorError: "var(--severity-critical)",
    colorInfo: "var(--severity-info)",
    borderRadius: 12,         // 한국 트렌드 — 더 친근하게 둥글게
    borderRadiusSM: 6,
    borderRadiusLG: 16,
    fontFamily:
      '"Pretendard Variable", Pretendard, "Inter Tight", -apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo", "Segoe UI", Roboto, "Malgun Gothic", sans-serif',
    fontSize: 14,
    motionDurationFast: "120ms",
    motionDurationMid: "220ms",
    motionDurationSlow: "360ms",
    motionEaseInOut: "cubic-bezier(0.32, 0.72, 0, 1)",
  },
  components: {
    Layout: {
      bodyBg: "var(--mond-surface-0)",
      headerBg: "var(--mond-surface-1)",
      siderBg: "var(--mond-surface-0)",
    },
    Card: {
      colorBgContainer: "var(--mond-surface-1)",
      paddingLG: 20,          // 24 → 20 — 정보 밀도
    },
    Menu: {
      darkItemBg: "transparent",
      darkItemColor: "var(--fg-secondary)",
      darkItemHoverBg: "color-mix(in oklch, var(--accent) 8%, transparent)",
      darkItemHoverColor: "var(--fg-primary)",
      darkItemSelectedBg: "color-mix(in oklch, var(--accent) 14%, transparent)",
      darkItemSelectedColor: "var(--accent)",
      darkSubMenuItemBg: "transparent",
      darkGroupTitleColor: "var(--fg-tertiary)",
      itemSelectedBg: "color-mix(in oklch, var(--accent) 14%, transparent)",
      itemSelectedColor: "var(--accent)",
      itemHoverBg: "color-mix(in oklch, var(--accent) 8%, transparent)",
      groupTitleColor: "var(--fg-tertiary)",
      groupTitleFontSize: 10,
      itemHeight: 38,
      iconSize: 15,
    },
    Table: {
      cellPaddingBlock: 10,   // 16 → 10 — 행 높이 ↓
      headerBg: "transparent",
    },
    Statistic: {
      contentFontSize: 32,    // 24 → 32 — KPI 강조
      titleFontSize: 13,
    },
    Drawer: {
      colorBgElevated: "var(--mond-surface-2)",
    },
    Modal: {
      contentBg: "var(--mond-surface-2)",
    },
    Tag: {
      defaultBg: "var(--mond-surface-2)",
      defaultColor: "var(--mond-text-dim)",
    },
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
