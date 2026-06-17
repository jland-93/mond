/**
 * 🌙 Mond — 사이드바 + 헤더 레이아웃
 */

import {
  AppstoreOutlined,
  ApiOutlined,
  BulbOutlined,
  DashboardOutlined,
  ExperimentOutlined,
  SafetyOutlined,
  ScanOutlined,
  SettingOutlined,
} from "@ant-design/icons";
import { Layout as AntLayout, Menu } from "antd";
import { useState } from "react";
import { Outlet, useLocation, useNavigate } from "react-router-dom";

import Logo from "@/components/Logo";

const { Header, Sider, Content } = AntLayout;

const items = [
  { key: "/", icon: <DashboardOutlined />, label: "Dashboard" },
  { key: "/assets", icon: <AppstoreOutlined />, label: "Assets" },
  { key: "/scans", icon: <ScanOutlined />, label: "Scans" },
  { key: "/findings", icon: <SafetyOutlined />, label: "Findings" },
  { key: "/policies", icon: <ExperimentOutlined />, label: "Policies" },
  { key: "/ai-insights", icon: <BulbOutlined />, label: "AI Insights" },
  { key: "/integrations", icon: <ApiOutlined />, label: "Integrations" },
  { key: "/settings", icon: <SettingOutlined />, label: "Settings" },
];

export default function Layout() {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

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
            padding: "0 24px",
            borderBottom: "1px solid var(--mond-border)",
          }}
        >
          <span style={{ color: "var(--mond-text-dim)" }}>
            🌙 AI-Powered Open-Source DevSecOps Platform
          </span>
        </Header>
        <Content style={{ padding: 24 }}>
          <Outlet />
        </Content>
      </AntLayout>
    </AntLayout>
  );
}
