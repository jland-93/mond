/**
 * Users 관리 API (ADMIN 전용)
 */

import { api } from "@/lib/api";
import type { Role } from "@/lib/auth-api";

export interface AdminUser {
  id: number;
  email: string;
  name?: string | null;
  picture_url?: string | null;
  role: Role;
  sso_provider?: string | null;
  last_login_at_iso?: string | null;
  created_at: string;
  updated_at: string;
}

export const usersApi = {
  list: () => api.get<AdminUser[]>("/users").then((r) => r.data),
  updateRole: (id: number, role: Role) =>
    api.patch<AdminUser>(`/users/${id}/role`, { role }).then((r) => r.data),
};
