/**
 * 🌙 Settings — 헬스/버전 정보
 */

import { useQuery } from "@tanstack/react-query";
import { Card, Descriptions, Tag, Typography } from "antd";

import { useI18n } from "@/i18n";
import { api } from "@/lib/api";

const { Title, Paragraph } = Typography;

interface Health {
  status: string;
  db: boolean;
  version: string;
  environment: string;
  ai_enabled: boolean;
}

async function fetchHealth(): Promise<Health> {
  const { data } = await api.get<Health>("/health");
  return data;
}

export default function Settings() {
  const { t, locale } = useI18n();
  const { data } = useQuery({ queryKey: ["health"], queryFn: fetchHealth });

  return (
    <div>
      <Title level={2} style={{ marginBottom: 16 }}>
        {t.settings.title}
      </Title>

      <Card title={t.settings.serviceStatus}>
        <Descriptions column={1}>
          <Descriptions.Item label={t.common.status}>
            <Tag color={data?.status === "ok" ? "green" : "orange"}>{data?.status ?? "—"}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label={t.settings.db}>
            <Tag color={data?.db ? "green" : "red"}>
              {data?.db ? t.common.yes : t.common.no}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label={t.settings.version}>{data?.version ?? "—"}</Descriptions.Item>
          <Descriptions.Item label={t.settings.environment}>{data?.environment ?? "—"}</Descriptions.Item>
          <Descriptions.Item label={t.settings.ai}>
            {data?.ai_enabled ? (
              <Tag color="green">{t.ai.enabled}</Tag>
            ) : (
              <Tag color="orange">{t.ai.disabled}</Tag>
            )}
          </Descriptions.Item>
          <Descriptions.Item label={t.settings.locale}>
            <Tag>{locale.toUpperCase()}</Tag>
          </Descriptions.Item>
        </Descriptions>
      </Card>

      <Paragraph type="secondary" style={{ marginTop: 24 }}>
        {t.settings.note}
      </Paragraph>
    </div>
  );
}
