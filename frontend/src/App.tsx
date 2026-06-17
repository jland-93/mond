/**
 * 🌙 Mond — 라우팅
 */

import { Route, Routes } from "react-router-dom";

import Layout from "@/components/Layout";
import AIInsights from "@/pages/AIInsights";
import Assets from "@/pages/Assets";
import Dashboard from "@/pages/Dashboard";
import Findings from "@/pages/Findings";
import Integrations from "@/pages/Integrations";
import Policies from "@/pages/Policies";
import Scans from "@/pages/Scans";
import Settings from "@/pages/Settings";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="assets" element={<Assets />} />
        <Route path="scans" element={<Scans />} />
        <Route path="findings" element={<Findings />} />
        <Route path="policies" element={<Policies />} />
        <Route path="ai-insights" element={<AIInsights />} />
        <Route path="integrations" element={<Integrations />} />
        <Route path="settings" element={<Settings />} />
      </Route>
    </Routes>
  );
}
