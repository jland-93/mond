/**
 * 🌙 Policies — 룰셋 / 컴플라이언스 매핑
 */

import { useQuery } from "@tanstack/react-query";
import { Card, Empty, Switch, Table, Tag, Typography } from "antd";

import { api, type Policy } from "@/lib/api";

const { Title, Paragraph } = Typography;

async function fetchPolicies(): Promise<Policy[]> {
  const { data } = await api.get<Policy[]>("/policies");
  return data;
}

export default function Policies() {
  const { data, isLoading } = useQuery({ queryKey: ["policies"], queryFn: fetchPolicies });

  return (
    <div>
      <Title level={2} style={{ marginBottom: 16 }}>
        Policies
      </Title>
      <Paragraph type="secondary">
        스캐너 결과에 적용되는 정책입니다. 각 정책은 SAST / SCA / IaC / DAST / Container /
        Secrets / Compliance 유형 중 하나에 속하며, 임계치를 넘기는 발견사항은 파이프라인 게이트를 차단합니다.
      </Paragraph>

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
