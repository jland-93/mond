/**
 * 🌙 Auth API helpers
 */

import { api } from "@/lib/api";

export type Role = "viewer" | "employee" | "reviewer" | "admin";

export interface Me {
  id: number;
  email: string;
  name?: string | null;
  picture_url?: string | null;
  role: Role;
  mfa_required?: boolean;
  mfa_verified?: boolean;
  mfa_enrolled?: boolean;
}

export interface AuthProviderInfo {
  name: string;
  display: string;
}

export interface ProvidersResponse {
  mode: string;
  dev_login_enabled: boolean;
  providers: AuthProviderInfo[];
}

export const authApi = {
  providers: () => api.get<ProvidersResponse>("/auth/providers").then((r) => r.data),
  me: () => api.get<Me>("/auth/me").then((r) => r.data),
  devLogin: (email: string, name?: string) =>
    api.post<Me>("/auth/dev-login", { email, name }).then((r) => r.data),
  logout: () => api.post("/auth/logout").then((r) => r.data),
};

// Role 계층: viewer < employee < reviewer < admin
const RANK: Record<Role, number> = { viewer: 1, employee: 2, reviewer: 3, admin: 4 };

export function hasRole(user: Me | null, min: Role): boolean {
  if (!user) return false;
  return RANK[user.role] >= RANK[min];
}
