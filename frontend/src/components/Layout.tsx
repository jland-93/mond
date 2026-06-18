/**
 * 🌙 Mond — 사이드바 + 헤더 레이아웃 + 언어 스위처 + 사용자 메뉴
 *
 * 일반 모드와 관리자 모드(/admin/*)에서 사이드바 메뉴가 전환된다.
 */

import {
  AppstoreOutlined,
  ApiOutlined,
  AuditOutlined,
  BookOutlined,
  BulbOutlined,
  DashboardOutlined,
  ExperimentOutlined,
  FileTextOutlined,
  GlobalOutlined,
  KeyOutlined,
  LogoutOutlined,
  RollbackOutlined,
  SafetyCertificateOutlined,
  SafetyOutlined,
  ScanOutlined,
  SettingOutlined,
  SolutionOutlined,
  TeamOutlined,
  ThunderboltOutlined,
  UserOutlined,
} from "@ant-design/icons";
import { Avatar, Button, Dropdown, Layout as AntLayout, Menu, Space, Tag } from "antd";
import { useState } from "react";
import { Outlet, useLocation, useNavigate } from "react-router-dom";

import { useAuth } from "@/auth/AuthContext";
import Logo from "@/components/Logo";
import { useI18n, type Locale } from "@/i18n";
import { hasRole } from "@/lib/auth-api";
import { withTransition } from "@/lib/view-transition";

const { Header, Sider, Content } = AntLayout;

export default function Layout() {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { t, locale, setLocale } = useI18n();
  const { user, logout } = useAuth();

  const isAdminRoute = location.pathname.startsWith("/admin");

  const userItems = [
    { key: "/", icon: <DashboardOutlined />, label: t.menu.dashboard, minRole: "viewer" as const },
    { key: "/assets", icon: <AppstoreOutlined />, label: t.menu.assets, minRole: "viewer" as const },
    { key: "/scans", icon: <ScanOutlined />, label: t.menu.scans, minRole: "employee" as const },
    { key: "/findings", icon: <SafetyOutlined />, label: t.menu.findings, minRole: "viewer" as const },
    { key: "/policies", icon: <ExperimentOutlined />, label: t.menu.policies, minRole: "viewer" as const },
    { key: "/policy-sim", icon: <ThunderboltOutlined />, label: t.menu.policySim, minRole: "employee" as const },
    { key: "/ai-insights", icon: <BulbOutlined />, label: t.menu.aiInsights, minRole: "viewer" as const },
    { key: "/knowledge", icon: <BookOutlined />, label: t.menu.knowledge, minRole: "viewer" as const },
    { key: "/regulations", icon: <AuditOutlined />, label: t.menu.regulations, minRole: "viewer" as const },
    { key: "/reports", icon: <FileTextOutlined />, label: t.menu.reports, minRole: "viewer" as const },
    // Integrations 메타 페이지는 Admin → Connections로 통합되어 일반 메뉴에서 제외.
    // (라우트는 유지되어 기존 링크는 살아 있음)
    { key: "/iam-explorer", icon: <TeamOutlined />, label: t.menu.iamExplorer, minRole: "employee" as const },
    { key: "/access-center", icon: <KeyOutlined />, label: t.menu.accessCenter, minRole: "employee" as const },
    { key: "/settings", icon: <SettingOutlined />, label: t.menu.settings, minRole: "viewer" as const },
  ].filter((i) => hasRole(user, i.minRole));

  const adminItems = [
    { key: "/admin/access-review", icon: <SolutionOutlined />, label: t.adminArea.menuAccessReview, minRole: "reviewer" as const },
    { key: "/admin/policies", icon: <ExperimentOutlined />, label: t.adminArea.menuPolicies, minRole: "reviewer" as const },
    { key: "/admin/connections", icon: <ApiOutlined />, label: t.adminArea.menuConnections, minRole: "admin" as const },
    { key: "/admin/users", icon: <TeamOutlined />, label: t.adminArea.menuUsers, minRole: "admin" as const },
  ].filter((i) => hasRole(user, i.minRole));

  const items = isAdminRoute ? adminItems : userItems;
  const selectedKey =
    items.find((i) => location.pathname.startsWith(i.key))?.key ?? items[0]?.key ?? "";

  const canEnterAdmin = hasRole(user, "reviewer");

  const roleLabel = (() => {
    if (!user) return "";
    return ({
      viewer: t.auth.roleViewer,
      employee: t.auth.roleEmployee,
      reviewer: t.auth.roleReviewer,
      admin: t.auth.roleAdmin,
    })[user.role];
  })();

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
        {isAdminRoute && !collapsed && (
          <div style={{ padding: "6px 18px" }}>
            <Tag color="red">{t.admin.badge}</Tag>
          </div>
        )}
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[selectedKey]}
          items={items}
          onClick={({ key }) => withTransition(() => navigate(key))}
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
          <Space size={8} align="center">
            <img
              src="/logo.png"
              alt="Mond"
              width={20}
              height={20}
              style={{
                borderRadius: 4,
                filter: "drop-shadow(0 0 6px oklch(72% 0.16 285 / 0.5))",
                verticalAlign: "middle",
              }}
            />
            <span style={{ color: "var(--mond-text-dim)" }}>{t.appTagline}</span>
            {isAdminRoute && <Tag color="red">{t.admin.badge}</Tag>}
          </Space>
          <Space>
            {canEnterAdmin && (
              <Button
                type={isAdminRoute ? "primary" : "default"}
                danger={isAdminRoute}
                icon={isAdminRoute ? <RollbackOutlined /> : <SafetyCertificateOutlined />}
                onClick={() => withTransition(() => navigate(isAdminRoute ? "/" : "/admin/access-review"))}
              >
                {isAdminRoute ? t.adminArea.backToApp : t.admin.enter}
              </Button>
            )}
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
            {user && (
              <Dropdown
                trigger={["click"]}
                menu={{
                  items: [
                    {
                      key: "info",
                      label: (
                        <div style={{ padding: "4px 0" }}>
                          <div>{user.name || user.email}</div>
                          <div style={{ color: "var(--mond-text-dim)", fontSize: 12 }}>
                            {user.email}
                          </div>
                          <Tag style={{ marginTop: 4 }}>{roleLabel}</Tag>
                        </div>
                      ),
                      disabled: true,
                    },
                    { type: "divider" },
                    {
                      key: "security",
                      icon: <SafetyOutlined />,
                      label: t.security.menuLabel,
                      onClick: () => navigate("/security"),
                    },
                    { type: "divider" },
                    {
                      key: "logout",
                      icon: <LogoutOutlined />,
                      label: t.auth.logout,
                      onClick: async () => {
                        await logout();
                        navigate("/login");
                      },
                    },
                  ],
                }}
              >
                <Button type="text" style={{ padding: "0 8px" }}>
                  <Avatar
                    size={28}
                    src={user.picture_url ?? undefined}
                    icon={!user.picture_url && <UserOutlined />}
                    style={{ marginRight: 6 }}
                  />
                  <span>{user.name || user.email}</span>
                </Button>
              </Dropdown>
            )}
          </Space>
        </Header>
        <Content style={{ padding: 24 }}>
          <Outlet />
        </Content>
      </AntLayout>
    </AntLayout>
  );
}
