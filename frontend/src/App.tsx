/**
 * Mond — 라우팅 (인증 가드 + 관리자 영역 포함)
 */

import { Navigate, Route, Routes } from "react-router-dom";

import RequireAuth from "@/auth/RequireAuth";
import Layout from "@/components/Layout";
import AccessCenter from "@/pages/AccessCenter";
import AccessReview from "@/pages/AccessReview";
import AIInsights from "@/pages/AIInsights";
import Assets from "@/pages/Assets";
import Dashboard from "@/pages/Dashboard";
import Findings from "@/pages/Findings";
import IAMExplorer from "@/pages/IAMExplorer";
import KnowledgeHub from "@/pages/KnowledgeHub";
import Login from "@/pages/Login";
import MyMond from "@/pages/MyMond";
import MfaChallenge from "@/pages/MfaChallenge";
import Policies from "@/pages/Policies";
import SecuritySettings from "@/pages/SecuritySettings";
import PolicySimulator from "@/pages/PolicySimulator";
import Regulations from "@/pages/Regulations";
import Reports from "@/pages/Reports";
import Scans from "@/pages/Scans";
import Settings from "@/pages/Settings";
import AdminConnections from "@/pages/admin/AdminConnections";
import AdminPolicies from "@/pages/admin/AdminPolicies";
import AdminUsers from "@/pages/admin/AdminUsers";

export default function App() {
  return (
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
  );
}
