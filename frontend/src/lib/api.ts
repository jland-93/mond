/**
 * 🌙 Mond — 백엔드 API 클라이언트
 */

import axios from "axios";

const baseURL = (import.meta.env.VITE_API_URL ?? "http://localhost:8000") + "/api/v1";

export const api = axios.create({
  baseURL,
  timeout: 30_000,
  headers: { "Content-Type": "application/json" },
});

// ── 타입 ───────────────────────────────────────────────
export type AssetType =
  | "repository"
  | "container_image"
  | "host"
  | "url"
  | "cloud_resource"
  | "application";

export type Severity = "critical" | "high" | "medium" | "low" | "info";

export type FindingStatus =
  | "new"
  | "triaged"
  | "in_progress"
  | "resolved"
  | "suppressed"
  | "false_positive";

export type ScanStatus = "pending" | "running" | "completed" | "failed" | "cancelled";

export interface Asset {
  id: number;
  name: string;
  asset_type: AssetType;
  uri: string;
  description?: string | null;
  labels: Record<string, string>;
  owner?: string | null;
  environment?: string | null;
  open_findings_count: number;
  last_scanned_at_str?: string | null;
  created_at: string;
  updated_at: string;
}

export interface Finding {
  id: number;
  asset_id: number;
  scan_id?: number | null;
  rule_id: string;
  title: string;
  description?: string | null;
  severity: Severity;
  status: FindingStatus;
  scanner: string;
  location?: string | null;
  references: string[];
  fingerprint: string;
  extra: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface Scan {
  id: number;
  asset_id: number;
  scanner: string;
  trigger: string;
  status: ScanStatus;
  started_at?: string | null;
  finished_at?: string | null;
  duration_ms?: number | null;
  findings_count: number;
  error_message?: string | null;
  created_at: string;
  updated_at: string;
}

export interface Policy {
  id: number;
  name: string;
  policy_type: string;
  description?: string | null;
  enabled: boolean;
  severity_threshold: string;
  definition: Record<string, unknown>;
  compliance_refs: string[];
  created_at: string;
  updated_at: string;
}

export interface AIInsight {
  id: number;
  finding_id?: number | null;
  kind: "triage" | "remediation" | "summary" | "explain";
  model: string;
  summary: string;
  confidence?: number | null;
  recommended_severity?: string | null;
  remediation: { steps?: string[]; code?: string; references?: string[] };
  input_tokens?: number | null;
  output_tokens?: number | null;
  created_at: string;
  updated_at: string;
}

export interface Page<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export interface DashboardOverview {
  security_score: number;
  asset_total: number;
  open_findings_total: number;
  open_findings_by_severity: Record<Severity, number>;
  scans_last_7d: number;
  recent_scans: Array<{
    id: number;
    asset_id: number;
    scanner: string;
    status: ScanStatus;
    findings_count: number;
    created_at: string;
  }>;
  recent_findings: Array<{
    id: number;
    title: string;
    severity: Severity;
    scanner: string;
    asset_id: number;
    created_at: string;
  }>;
}
