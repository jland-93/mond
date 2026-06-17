/**
 * 🌙 Mond — 사이드바 + 헤더 레이아웃 + 언어 스위처
 */

import {
  AppstoreOutlined,
  ApiOutlined,
  AuditOutlined,
  BulbOutlined,
  DashboardOutlined,
  ExperimentOutlined,
  FileTextOutlined,
  GlobalOutlined,
  KeyOutlined,
  SafetyOutlined,
  ScanOutlined,
  SettingOutlined,
  SolutionOutlined,
  TeamOutlined,
  ThunderboltOutlined,
} from "@ant-design/icons";
import { Button, Dropdown, Layout as AntLayout, Menu, Space } from "antd";
import { useState } from "react";
import { Outlet, useLocation, useNavigate } from "react-router-dom";

import Logo from "@/components/Logo";
import { useI18n, type Locale } from "@/i18n";

const { Header, Sider, Content } = AntLayout;

export default function Layout() {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { t, locale, setLocale } = useI18n();

  const items = [
    { key: "/", icon: <DashboardOutlined />, label: t.menu.dashboard },
    { key: "/assets", icon: <AppstoreOutlined />, label: t.menu.assets },
    { key: "/scans", icon: <ScanOutlined />, label: t.menu.scans },
    { key: "/findings", icon: <SafetyOutlined />, label: t.menu.findings },
    { key: "/policies", icon: <ExperimentOutlined />, label: t.menu.policies },
    { key: "/policy-sim", icon: <ThunderboltOutlined />, label: t.menu.policySim },
    { key: "/ai-insights", icon: <BulbOutlined />, label: t.menu.aiInsights },
    { key: "/regulations", icon: <AuditOutlined />, label: t.menu.regulations },
    { key: "/reports", icon: <FileTextOutlined />, label: t.menu.reports },
    { key: "/integrations", icon: <ApiOutlined />, label: t.menu.integrations },
    { key: "/iam-explorer", icon: <TeamOutlined />, label: t.menu.iamExplorer },
    { key: "/access-center", icon: <KeyOutlined />, label: t.menu.accessCenter },
    { key: "/access-review", icon: <SolutionOutlined />, label: t.menu.accessReview },
    { key: "/settings", icon: <SettingOutlined />, label: t.menu.settings },
  ];

  const selectedKey =
    items.find((i) => i.key !== "/" && location.pathname.startsWith(i.key))?.key ?? "/";

  return (
    <AntLayout style={{ minHeight: "100vh" }}>
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        width={232}
        theme="dark"
        style={{ borderRight: "1px solid var(--mond-border)" }}
      >
        <Logo collapsed={collapsed} />
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[selectedKey]}
          items={items}
          onClick={({ key }) => navigate(key)}
          style={{ background: "transparent", borderRight: 0, marginTop: 12 }}
        />
      </Sider>
      <AntLayout>
        <Header
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "0 24px",
            borderBottom: "1px solid var(--mond-border)",
          }}
        >
          <span style={{ color: "var(--mond-text-dim)" }}>🌙 {t.appTagline}</span>
          <Space>
            <Dropdown
              trigger={["click"]}
              menu={{
                items: [
                  { key: "ko", label: t.language.ko },
                  { key: "en", label: t.language.en },
                ],
                selectable: true,
                selectedKeys: [locale],
                onClick: ({ key }) => setLocale(key as Locale),
              }}
            >
              <Button icon={<GlobalOutlined />} type="text">
                {locale.toUpperCase()}
              </Button>
            </Dropdown>
          </Space>
        </Header>
        <Content style={{ padding: 24 }}>
          <Outlet />
        </Content>
      </AntLayout>
    </AntLayout>
  );
}
