/**
 * AI Providers (Admin) API helpers
 */

import { api } from "@/lib/api";

export type AIProviderName = "anthropic" | "openai" | "bedrock" | "ollama" | "vllm";

export interface AIProviderRow {
  id: number;
  provider: AIProviderName;
  enabled: boolean;
  is_default: boolean;
  has_api_key: boolean;
  api_key_masked: string;
  base_url?: string | null;
  region?: string | null;
  model_default?: string | null;
  model_deep?: string | null;
}

export interface AIProviderUpsert {
  provider: AIProviderName;
  enabled?: boolean;
  is_default?: boolean;
  api_key?: string;
  base_url?: string;
  region?: string;
  model_default?: string;
  model_deep?: string;
}

export interface TestResult {
  ok: boolean;
  provider: string;
  model: string;
  detail: string;
}

export const aiProvidersApi = {
  list: () => api.get<AIProviderRow[]>("/admin/ai-providers").then((r) => r.data),
  upsert: (body: AIProviderUpsert) =>
    api.put<AIProviderRow>("/admin/ai-providers", body).then((r) => r.data),
  activate: (id: number) =>
    api.post<AIProviderRow>(`/admin/ai-providers/${id}/activate`).then((r) => r.data),
  remove: (id: number) => api.delete(`/admin/ai-providers/${id}`).then((r) => r.data),
  test: (body: AIProviderUpsert) =>
    api.post<TestResult>("/admin/ai-providers/test", body).then((r) => r.data),
};
