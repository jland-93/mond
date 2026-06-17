/**
 * 🌙 Mond — 라우팅 (인증 가드 포함)
 */

import { Route, Routes } from "react-router-dom";

import RequireAuth from "@/auth/RequireAuth";
import Layout from "@/components/Layout";
import AccessCenter from "@/pages/AccessCenter";
import AccessReview from "@/pages/AccessReview";
import AIInsights from "@/pages/AIInsights";
import Assets from "@/pages/Assets";
import Dashboard from "@/pages/Dashboard";
import Findings from "@/pages/Findings";
import IAMExplorer from "@/pages/IAMExplorer";
import Integrations from "@/pages/Integrations";
import KnowledgeHub from "@/pages/KnowledgeHub";
import Login from "@/pages/Login";
import Policies from "@/pages/Policies";
import PolicySimulator from "@/pages/PolicySimulator";
import Regulations from "@/pages/Regulations";
import Reports from "@/pages/Reports";
import Scans from "@/pages/Scans";
import Settings from "@/pages/Settings";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        element={
          <RequireAuth>
            <Layout />
          </RequireAuth>
        }
      >
        <Route index element={<Dashboard />} />
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
            <RequireAuth minRole="employee">
              <PolicySimulator />
            </RequireAuth>
          }
        />
        <Route path="ai-insights" element={<AIInsights />} />
        <Route path="knowledge" element={<KnowledgeHub />} />
        <Route path="regulations" element={<Regulations />} />
        <Route path="reports" element={<Reports />} />
        <Route path="integrations" element={<Integrations />} />
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
        <Route
          path="access-review"
          element={
            <RequireAuth minRole="reviewer">
              <AccessReview />
            </RequireAuth>
          }
        />
        <Route path="settings" element={<Settings />} />
      </Route>
    </Routes>
  );
}
