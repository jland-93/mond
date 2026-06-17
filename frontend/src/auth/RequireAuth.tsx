/**
 * 🌙 RequireAuth — 미인증 시 /login으로 리다이렉트하는 라우트 가드
 */

import { Spin } from "antd";
import type { ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";

import { useAuth } from "@/auth/AuthContext";
import { hasRole, type Role } from "@/lib/auth-api";

export default function RequireAuth({
  children,
  minRole = "viewer",
}: {
  children: ReactNode;
  minRole?: Role;
}) {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div style={{ minHeight: "100vh", display: "grid", placeItems: "center" }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" state={{ from: location.pathname }} replace />;
  }

  if (!hasRole(user, minRole)) {
    return (
      <div style={{ padding: 24 }}>
        <h2>403 — 권한 부족 / Forbidden</h2>
        <p>요청한 페이지에는 {minRole} 이상의 권한이 필요합니다.</p>
      </div>
    );
  }

  return <>{children}</>;
}
