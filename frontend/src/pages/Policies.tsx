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
  const { t, locale } = useI18n();
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
          locale={{
            emptyText: <Empty description={locale === "ko" ? "정책이 없습니다" : "No policies"} />,
          }}
          columns={[
            { title: t.common.name, dataIndex: "name" },
            {
              title: t.common.type,
              dataIndex: "policy_type",
              render: (v: string) => <Tag color="purple">{v}</Tag>,
              width: 130,
            },
            { title: t.policies.threshold, dataIndex: "severity_threshold", width: 120 },
            {
              title: t.common.enabled,
              dataIndex: "enabled",
              render: (v: boolean) => <Switch checked={v} disabled />,
              width: 100,
            },
            {
              title: t.policies.compliance,
              dataIndex: "compliance_refs",
              render: (refs: string[]) => (
                <>
                  {(refs ?? []).map((r) => (
                    <Tag key={r}>{r}</Tag>
                  ))}
                </>
              ),
            },
            { title: t.common.description, dataIndex: "description", ellipsis: true },
          ]}
        />
      </Card>
    </div>
  );
}
