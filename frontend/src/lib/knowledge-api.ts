/**
 * Knowledge Hub API helpers
 */

import { api } from "@/lib/api";

export type KnowledgeCategory =
  | "devsecops_basics"
  | "owasp"
  | "kr_regulations"
  | "global_regulations"
  | "best_practices"
  | "incident_response";

export type KnowledgeSource = "seed" | "ai" | "manual";

export interface KnowledgeCard {
  id: number;
  slug: string;
  category: KnowledgeCategory;
  title_ko: string;
  title_en: string;
  summary_ko: string;
  summary_en: string;
  ask_ko: string;
  ask_en: string;
  refs: string[];
  source: KnowledgeSource;
  published: boolean;
  model?: string | null;
  created_at: string;
  updated_at: string;
}

export const knowledgeApi = {
  list: (category?: KnowledgeCategory) =>
    api
      .get<KnowledgeCard[]>("/knowledge/cards", { params: { category } })
      .then((r) => r.data),
  create: (body: Omit<KnowledgeCard, "id" | "created_at" | "updated_at">) =>
    api.post<KnowledgeCard>("/knowledge/cards", body).then((r) => r.data),
  remove: (id: number) => api.delete(`/knowledge/cards/${id}`).then((r) => r.data),
  generate: (body: { category: KnowledgeCategory; topic_hint?: string; count?: number }) =>
    api.post<KnowledgeCard[]>("/knowledge/cards/generate", body).then((r) => r.data),
};
