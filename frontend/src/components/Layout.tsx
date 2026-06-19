/**
 * Mond — 사이드바 + 헤더 레이아웃 + 언어 스위처 + 사용자 메뉴
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
  HomeOutlined,
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

  // 사이드바 정보 위계 — 4그룹으로 미니멀 분할 (OVERVIEW / OPS / KNOWLEDGE / ACCESS).
  // 평탄 14개를 그룹으로 묶어 시각 노이즈를 낮추고 카테고리 navigation 가능.
  const overviewItems = [
    { key: "/me", icon: <HomeOutlined />, label: t.menu.myMond, minRole: "viewer" as const },
    { key: "/", icon: <DashboardOutlined />, label: t.menu.dashboard, minRole: "viewer" as const },
  ].filter((i) => hasRole(user, i.minRole));

  const opsItems = [
    { key: "/assets", icon: <AppstoreOutlined />, label: t.menu.assets, minRole: "viewer" as const },
    { key: "/scans", icon: <ScanOutlined />, label: t.menu.scans, minRole: "employee" as const },
    { key: "/findings", icon: <SafetyOutlined />, label: t.menu.findings, minRole: "viewer" as const },
    { key: "/policies", icon: <ExperimentOutlined />, label: t.menu.policies, minRole: "viewer" as const },
    { key: "/policy-sim", icon: <ThunderboltOutlined />, label: t.menu.policySim, minRole: "employee" as const },
    { key: "/ai-insights", icon: <BulbOutlined />, label: t.menu.aiInsights, minRole: "viewer" as const },
  ].filter((i) => hasRole(user, i.minRole));

  const knowledgeItems = [
    { key: "/knowledge", icon: <BookOutlined />, label: t.menu.knowledge, minRole: "viewer" as const },
    { key: "/regulations", icon: <AuditOutlined />, label: t.menu.regulations, minRole: "viewer" as const },
    { key: "/reports", icon: <FileTextOutlined />, label: t.menu.reports, minRole: "viewer" as const },
  ].filter((i) => hasRole(user, i.minRole));

  const accessItems = [
    { key: "/iam-explorer", icon: <TeamOutlined />, label: t.menu.iamExplorer, minRole: "employee" as const },
    { key: "/access-center", icon: <KeyOutlined />, label: t.menu.accessCenter, minRole: "employee" as const },
    { key: "/security", icon: <SafetyCertificateOutlined />, label: t.menu.security, minRole: "viewer" as const },
    { key: "/settings", icon: <SettingOutlined />, label: t.menu.settings, minRole: "viewer" as const },
  ].filter((i) => hasRole(user, i.minRole));

  // 그룹 정의 — antd Menu의 type:'group' 형식.
  type GroupEntry = {
    type: "group";
    key: string;
    label: string;
    children: { key: string; icon: JSX.Element; label: string }[];
  };
  const userMenu: GroupEntry[] = [
    { type: "group" as const, key: "g-overview", label: t.menuGroups.overview, children: overviewItems },
    { type: "group" as const, key: "g-ops", label: t.menuGroups.operations, children: opsItems },
    { type: "group" as const, key: "g-knowledge", label: t.menuGroups.knowledge, children: knowledgeItems },
    { type: "group" as const, key: "g-access", label: t.menuGroups.access, children: accessItems },
  ].filter((g) => g.children.length > 0);

  const adminFlat = [
    { key: "/admin/access-review", icon: <SolutionOutlined />, label: t.adminArea.menuAccessReview, minRole: "reviewer" as const },
    { key: "/admin/policies", icon: <ExperimentOutlined />, label: t.adminArea.menuPolicies, minRole: "reviewer" as const },
    { key: "/admin/connections", icon: <ApiOutlined />, label: t.adminArea.menuConnections, minRole: "admin" as const },
    { key: "/admin/users", icon: <TeamOutlined />, label: t.adminArea.menuUsers, minRole: "admin" as const },
  ].filter((i) => hasRole(user, i.minRole));

  const items = isAdminRoute ? adminFlat : userMenu;
  // selectedKey 계산용 — 평탄화된 leaf 목록.
  const leafItems = isAdminRoute
    ? adminFlat
    : [...overviewItems, ...opsItems, ...knowledgeItems, ...accessItems];

  // 정확한 일치 우선 — "/"는 모든 경로에 startsWith 매칭되므로 대시보드가 항상 잡히는 버그 방지.
  const selectedKey =
    leafItems.find((i) => location.pathname === i.key)?.key ??
    leafItems.find((i) => i.key !== "/" && location.pathname.startsWith(i.key + "/"))?.key ??
    leafItems.find((i) => i.key !== "/" && location.pathname.startsWith(i.key))?.key ??
    (location.pathname === "/" ? "/" : leafItems[0]?.key ?? "");

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
        breakpoint="lg"
        collapsedWidth={64}
        width={224}
        theme="dark"
        className="mond-sider"
        style={{
          borderRight: "1px solid var(--border)",
          background: "var(--surface-0)",
        }}
      >
        <Logo collapsed={collapsed} />
        {isAdminRoute && !collapsed && (
          <div style={{ padding: "6px 18px" }}>
            <Tag
              style={{
                background: "var(--severity-critical-bg)",
                color: "var(--severity-critical)",
                border: "1px solid var(--severity-critical)",
                borderRadius: 999,
                fontWeight: 500,
                letterSpacing: "0.04em",
              }}
            >
              {t.admin.badge}
            </Tag>
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
          className="mond-header"
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "0 24px",
            background: "var(--surface-0)",
            borderBottom: "1px solid var(--border)",
            height: 56,
          }}
        >
          <Space size={10} align="center">
            <span
              style={{
                fontSize: 11,
                color: "var(--accent)",
                background: "color-mix(in oklch, var(--accent) 10%, transparent)",
                border: "1px solid var(--accent-dim)",
                padding: "3px 10px",
                borderRadius: 999,
                letterSpacing: "0.06em",
                fontWeight: 600,
              }}
            >
              AI · DevSecOps
            </span>
            <span
              className="mond-tagline-long"
              style={{
                color: "var(--fg-tertiary)",
                fontSize: 12,
                letterSpacing: "-0.005em",
              }}
            >
              {t.appTagline}
            </span>
            {isAdminRoute && (
              <Tag
                style={{
                  background: "var(--severity-critical-bg)",
                  color: "var(--severity-critical)",
                  border: "1px solid var(--severity-critical)",
                  borderRadius: 999,
                  marginLeft: 6,
                  fontWeight: 600,
                  letterSpacing: "0.04em",
                }}
              >
                {t.admin.badge}
              </Tag>
            )}
          </Space>
          <Space size={4}>
            {canEnterAdmin && (
              <Button
                type={isAdminRoute ? "primary" : "text"}
                danger={isAdminRoute}
                size="small"
                icon={isAdminRoute ? <RollbackOutlined /> : <SafetyCertificateOutlined />}
                onClick={() => withTransition(() => navigate(isAdminRoute ? "/" : "/admin/access-review"))}
                style={!isAdminRoute ? { color: "var(--fg-tertiary)" } : undefined}
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
                  <span className="mond-user-name">{user.name || user.email}</span>
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
