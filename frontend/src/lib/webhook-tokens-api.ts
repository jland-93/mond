/**
 * 🌙 Personal Webhook Tokens API
 */

import { api } from "@/lib/api";

export interface WebhookTokenRow {
  id: number;
  name: string;
  token_prefix: string;
  created_at: string;
  last_used_at?: string | null;
  revoked_at?: string | null;
}

export interface WebhookTokenCreated extends WebhookTokenRow {
  raw_token: string;
}

export interface CiSnippet {
  asset_id: number;
  asset_name: string;
  github_actions: string;
  gitlab_ci: string;
  secrets_required: string[];
  note: string;
}

export const webhookTokensApi = {
  list: () => api.get<WebhookTokenRow[]>("/webhook-tokens").then((r) => r.data),
  create: (name: string) =>
    api.post<WebhookTokenCreated>("/webhook-tokens", { name }).then((r) => r.data),
  revoke: (id: number) => api.delete(`/webhook-tokens/${id}`).then((r) => r.data),
  snippet: (assetId: number) =>
    api
      .get<CiSnippet>("/webhook-tokens/ci-snippets/github-actions", {
        params: { asset_id: assetId },
      })
      .then((r) => r.data),
};
