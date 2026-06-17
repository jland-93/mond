/**
 * 🌙 Policies — 룰셋 / 컴플라이언스 매핑
 */

import { useQuery } from "@tanstack/react-query";
import { Card, Empty, Switch, Table, Tag, Typography } from "antd";

import { useI18n } from "@/i18n";
import { api, type Policy } from "@/lib/api";

const { Title, Paragraph } = Typography;

async function fetchPolicies(): Promise<Policy[]> {
  const { data } = await api.get<Policy[]>("/policies");
  return data;
}

export default function Policies() {
  const { t } = useI18n();
  const { data, isLoading } = useQuery({ queryKey: ["policies"], queryFn: fetchPolicies });

  return (
    <div>
      <Title level={2} style={{ marginBottom: 16 }}>
        {t.policies.title}
      </Title>
      <Paragraph type="secondary">{t.policies.desc}</Paragraph>

      <Card>
        <Table
          loading={isLoading}
          dataSource={data ?? []}
          rowKey="id"
          locale={{ emptyText: <Empty description="정책이 없습니다" /> }}
          columns={[
            { title: "Name", dataIndex: "name" },
            {
              title: "Type",
              dataIndex: "policy_type",
              render: (t: string) => <Tag color="purple">{t}</Tag>,
              width: 130,
            },
            { title: "Threshold", dataIndex: "severity_threshold", width: 120 },
            {
              title: "Enabled",
              dataIndex: "enabled",
              render: (v: boolean) => <Switch checked={v} disabled />,
              width: 100,
            },
            {
              title: "Compliance",
              dataIndex: "compliance_refs",
              render: (refs: string[]) => (
                <>
                  {(refs ?? []).map((r) => (
                    <Tag key={r}>{r}</Tag>
                  ))}
                </>
              ),
            },
            { title: "Description", dataIndex: "description", ellipsis: true },
          ]}
        />
      </Card>
    </div>
  );
}
