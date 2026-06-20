/**
 * Mond — 라우팅 (인증 가드 + 관리자 영역 포함)
 *
 * 라우트별 코드 스플릿. `Layout`과 인증 가드만 즉시 로드하고, 각 페이지는
 * lazy import로 별도 chunk로 잘라 첫 로드 사이즈를 줄인다. 이미 로그인된
 * 사용자에게 노출되는 첫 화면(Dashboard)은 라우트가 매칭되는 순간 로드.
 */

import { lazy, Suspense } from "react";
import { Navigate, Route, Routes } from "react-router-dom";

import RequireAuth from "@/auth/RequireAuth";
import Layout from "@/components/Layout";

const Login = lazy(() => import("@/pages/Login"));
const MfaChallenge = lazy(() => import("@/pages/MfaChallenge"));
const Dashboard = lazy(() => import("@/pages/Dashboard"));
const MyMond = lazy(() => import("@/pages/MyMond"));
const Assets = lazy(() => import("@/pages/Assets"));
const Scans = lazy(() => import("@/pages/Scans"));
const Findings = lazy(() => import("@/pages/Findings"));
const Policies = lazy(() => import("@/pages/Policies"));
const PolicySimulator = lazy(() => import("@/pages/PolicySimulator"));
const AIInsights = lazy(() => import("@/pages/AIInsights"));
const KnowledgeHub = lazy(() => import("@/pages/KnowledgeHub"));
const Regulations = lazy(() => import("@/pages/Regulations"));
const Reports = lazy(() => import("@/pages/Reports"));
const IAMExplorer = lazy(() => import("@/pages/IAMExplorer"));
const AccessCenter = lazy(() => import("@/pages/AccessCenter"));
const Settings = lazy(() => import("@/pages/Settings"));
const SecuritySettings = lazy(() => import("@/pages/SecuritySettings"));
const AccessReview = lazy(() => import("@/pages/AccessReview"));
const AdminConnections = lazy(() => import("@/pages/admin/AdminConnections"));
const AdminPolicies = lazy(() => import("@/pages/admin/AdminPolicies"));
const AdminSlack = lazy(() => import("@/pages/admin/AdminSlack"));
const AdminUsers = lazy(() => import("@/pages/admin/AdminUsers"));

// 페이지 chunk 로딩 중 빈 화면 대신 옅은 placeholder. 다크 테마 배경에 자연스럽게 녹는다.
function RouteFallback() {
  return <div style={{ minHeight: "60vh" }} aria-hidden />;
}

export default function App() {
  return (
    <Suspense fallback={<RouteFallback />}>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/mfa"
          element={
            <RequireAuth>
              <MfaChallenge />
            </RequireAuth>
          }
        />
        <Route
          element={
            <RequireAuth>
              <Layout />
            </RequireAuth>
          }
        >
          {/* 일반 영역 */}
          <Route index element={<Dashboard />} />
          <Route path="me" element={<MyMond />} />
          <Route path="assets" element={<Assets />} />
          <Route
            path="scans"
            element={
              <RequireAuth minRole="employee">
                <Scans />
              </RequireAuth>
            }
          />
          <Route path="findings" element={<Findings />} />
          <Route path="policies" element={<Policies />} />
          <Route
            path="policy-sim"
            element={
              <RequireAuth minRole="reviewer">
                <PolicySimulator />
              </RequireAuth>
            }
          />
          <Route path="ai-insights" element={<AIInsights />} />
          <Route path="knowledge" element={<KnowledgeHub />} />
          <Route path="regulations" element={<Regulations />} />
          <Route path="reports" element={<Reports />} />
          <Route
            path="iam-explorer"
            element={
              <RequireAuth minRole="employee">
                <IAMExplorer />
              </RequireAuth>
            }
          />
          <Route
            path="access-center"
            element={
              <RequireAuth minRole="employee">
                <AccessCenter />
              </RequireAuth>
            }
          />
          <Route path="settings" element={<Settings />} />
          <Route path="security" element={<SecuritySettings />} />

          {/* 관리자 영역 */}
          <Route path="admin" element={<Navigate to="/admin/access-review" replace />} />
          <Route
            path="admin/access-review"
            element={
              <RequireAuth minRole="reviewer">
                <AccessReview />
              </RequireAuth>
            }
          />
          <Route
            path="admin/policies"
            element={
              <RequireAuth minRole="reviewer">
                <AdminPolicies />
              </RequireAuth>
            }
          />
          <Route
            path="admin/connections"
            element={
              <RequireAuth minRole="admin">
                <AdminConnections />
              </RequireAuth>
            }
          />
          <Route
            path="admin/slack"
            element={
              <RequireAuth minRole="admin">
                <AdminSlack />
              </RequireAuth>
            }
          />
          <Route
            path="admin/users"
            element={
              <RequireAuth minRole="admin">
                <AdminUsers />
              </RequireAuth>
            }
          />

          {/* 구 경로 호환 */}
          <Route path="access-review" element={<Navigate to="/admin/access-review" replace />} />
        </Route>
      </Routes>
    </Suspense>
  );
}
