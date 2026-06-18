/**
 * Role Change Requests API — 셀프서비스 역할 변경 + ADMIN 검토
 */

import { api } from "@/lib/api";
import type { Role } from "@/lib/auth-api";

export type RoleRequestStatus =
  | "pending_ai_review"
  | "ai_auto_approved"
  | "needs_human_review"
  | "approved"
  | "denied";

export interface RoleRequestRow {
  id: number;
  requester_email: string;
  from_role: Role;
  to_role: Role;
  reason: string;
  status: RoleRequestStatus;
  ai_decision: { decision?: string; risk?: string; reason?: string };
  reviewer_email?: string | null;
  review_note?: string | null;
  created_at: string;
  decided_at?: string | null;
}

export const roleRequestsApi = {
  myList: () => api.get<RoleRequestRow[]>("/me/role-request").then((r) => r.data),
  request: (toRole: Role, reason: string) =>
    api
      .post<RoleRequestRow>("/me/role-request", { to_role: toRole, reason })
      .then((r) => r.data),
  adminList: (status?: RoleRequestStatus) =>
    api
      .get<RoleRequestRow[]>("/admin/role-requests", { params: { status } })
      .then((r) => r.data),
  decide: (id: number, approve: boolean, note: string) =>
    api
      .post<RoleRequestRow>(`/admin/role-requests/${id}/decision`, { approve, note })
      .then((r) => r.data),
};
