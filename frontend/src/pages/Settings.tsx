/**
 * 🌙 Settings — 헬스/버전 정보
 */

import { useQuery } from "@tanstack/react-query";
import { Card, Descriptions, Tag, Typography } from "antd";

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
  const { data } = useQuery({ queryKey: ["health"], queryFn: fetchHealth });

  return (
    <div>
      <Title level={2} style={{ marginBottom: 16 }}>
        Settings
      </Title>

      <Card title="Service Status">
        <Descriptions column={1}>
          <Descriptions.Item label="Status">
            <Tag color={data?.status === "ok" ? "green" : "orange"}>{data?.status ?? "—"}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Database">
            <Tag color={data?.db ? "green" : "red"}>{data?.db ? "connected" : "down"}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Version">{data?.version ?? "—"}</Descriptions.Item>
          <Descriptions.Item label="Environment">{data?.environment ?? "—"}</Descriptions.Item>
          <Descriptions.Item label="AI">
            {data?.ai_enabled ? (
              <Tag color="green">enabled</Tag>
            ) : (
              <Tag color="orange">disabled (heuristic mode)</Tag>
            )}
          </Descriptions.Item>
        </Descriptions>
      </Card>

      <Paragraph type="secondary" style={{ marginTop: 24 }}>
        Mond OSS는 자율 호스팅을 전제로 합니다. 환경 변수는 <code>.env</code>에서 관리하고, 운영
        설정은 <code>docker-compose.yml</code>을 참조하세요.
      </Paragraph>
    </div>
  );
}
