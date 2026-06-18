/**
 * Policy Templates API
 */

import { api } from "@/lib/api";

export interface PolicyTemplate {
  name: string;
  policy_type: string;
  description: string;
  severity_threshold: string;
  definition: Record<string, unknown>;
  compliance_refs: string[];
  frameworks: string[];
}

export interface FrameworkInfo {
  id: string;
  short_name: string;
  name_ko: string;
  name_en: string;
}

export const policyTemplatesApi = {
  list: (framework?: string) =>
    api
      .get<PolicyTemplate[]>("/policy/templates", { params: { framework } })
      .then((r) => r.data),
  frameworks: () =>
    api.get<FrameworkInfo[]>("/policy/templates/frameworks").then((r) => r.data),
  install: (names: string[]) =>
    api
      .post<{ installed: number; skipped_existing: number; names: string[] }>(
        "/policy/templates/install",
        { names },
      )
      .then((r) => r.data),
};
