import { api } from "./api";

export type SlackPurpose = "default" | "digest" | "finding" | "access_request" | "role_request";

export interface SlackChannelRow {
  id: number;
  purpose: SlackPurpose;
  label: string | null;
  enabled: boolean;
  webhook_masked: string;
}

export interface SlackChannelUpsert {
  purpose: SlackPurpose;
  webhook_url: string;
  label?: string | null;
  enabled: boolean;
}

export const adminSlackApi = {
  list: async (): Promise<SlackChannelRow[]> => (await api.get("/admin/slack")).data,
  upsert: async (body: SlackChannelUpsert): Promise<SlackChannelRow> =>
    (await api.put("/admin/slack", body)).data,
  remove: async (purpose: SlackPurpose): Promise<{ deleted: string }> =>
    (await api.delete(`/admin/slack/${purpose}`)).data,
  test: async (body: { purpose?: SlackPurpose; webhook_url?: string; text?: string }) =>
    (await api.post<{ ok: boolean; error: string | null }>("/admin/slack/test", body)).data,
};
