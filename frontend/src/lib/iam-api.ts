/**
 * 🌙 IAM Self-Service API helpers
 */

import { api } from "@/lib/api";

export type IAMSourceKind = "aws" | "gcp" | "azure" | "k8s" | "custom";
export type IdentityType = "user" | "role" | "service_account" | "group";
export type AccessRequestStatus =
  | "pending_ai_review"
  | "ai_auto_approved"
  | "needs_human_review"
  | "human_approved"
  | "human_denied"
  | "granted"
  | "grant_failed"
  | "expired_revoked"
  | "revoke_failed";

export type AuditEvent =
  | "ai_decided"
  | "human_decided"
  | "granted"
  | "grant_failed"
  | "expired_revoked"
  | "revoke_failed"
  | "manual_revoked";

export interface AuditLog {
  id: number;
  request_id: number;
  event: AuditEvent;
  actor: string;
  detail: Record<string, unknown>;
  created_at: string;
}

export interface IAMSource {
  id: number;
  name: string;
  kind: IAMSourceKind;
  config: Record<string, unknown>;
  last_synced_at_str?: string | null;
  created_at: string;
  updated_at: string;
}

export interface IAMIdentity {
  id: number;
  source_id: number;
  identity_type: IdentityType;
  name: string;
  external_id?: string | null;
  attributes: Record<string, unknown>;
}

export interface PermissionRow {
  id: number;
  source_id: number;
  name: string;
  external_id?: string | null;
  description?: string | null;
  risk_hint?: string | null;
  attributes: Record<string, unknown>;
}

export interface AccessRequest {
  id: number;
  requester: string;
  reason: string;
  duration_hours?: number | null;
  target_identity_id: number;
  permission_id: number;
  status: AccessRequestStatus;
  ai_decision: {
    decision?: string;
    risk_level?: string;
    reason?: string;
    model?: string;
    confidence?: number;
  };
  human_decision: {
    approve?: boolean;
    reviewer?: string;
    note?: string;
  };
  grant_result: {
    success?: boolean;
    detail?: Record<string, unknown>;
    granted_at?: string;
  };
  expires_at?: string | null;
  revoked_at?: string | null;
  revoke_result: {
    success?: boolean;
    detail?: Record<string, unknown>;
    revoked_at?: string;
    triggered_by?: string;
  };
  created_at: string;
  updated_at: string;
}

export const iamApi = {
  listSources: () => api.get<IAMSource[]>("/iam/sources").then((r) => r.data),
  createSource: (body: Partial<IAMSource> & { name: string; kind: IAMSourceKind }) =>
    api.post<IAMSource>("/iam/sources", body).then((r) => r.data),
  syncSource: (id: number) => api.post<Record<string, unknown>>(`/iam/sources/${id}/sync`).then((r) => r.data),

  listIdentities: (sourceId?: number) =>
    api
      .get<IAMIdentity[]>("/iam/identities", { params: { source_id: sourceId } })
      .then((r) => r.data),
  listPermissions: (sourceId?: number) =>
    api
      .get<PermissionRow[]>("/iam/permissions", { params: { source_id: sourceId } })
      .then((r) => r.data),

  listRequests: (status?: AccessRequestStatus) =>
    api
      .get<AccessRequest[]>("/iam/access-requests", { params: { status } })
      .then((r) => r.data),
  createRequest: (body: {
    requester: string;
    reason: string;
    target_identity_id: number;
    permission_id: number;
    duration_hours?: number;
  }) => api.post<AccessRequest>("/iam/access-requests", body).then((r) => r.data),
  humanDecision: (id: number, body: { approve: boolean; reviewer: string; note?: string }) =>
    api
      .post<AccessRequest>(`/iam/access-requests/${id}/human-decision`, body)
      .then((r) => r.data),
  revoke: (id: number, actor: string) =>
    api
      .post<AccessRequest>(`/iam/access-requests/${id}/revoke`, { actor })
      .then((r) => r.data),
  sweepExpired: () =>
    api.post<{ revoked: number }>("/iam/access-requests/sweep-expired").then((r) => r.data),
  audit: (id: number) =>
    api.get<AuditLog[]>(`/iam/access-requests/${id}/audit`).then((r) => r.data),
};
