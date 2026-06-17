/**
 * 🌙 Policy Simulator — 가상 finding 입력 → 어떤 정책 게이트가 차단되나
 */

import { DeleteOutlined, PlusOutlined, ThunderboltOutlined } from "@ant-design/icons";
import { useMutation } from "@tanstack/react-query";
import { Alert, Button, Card, Input, Select, Space, Table, Tag, Typography } from "antd";
import { useState } from "react";

import { useI18n } from "@/i18n";
import { api, type Severity } from "@/lib/api";

const { Title, Paragraph } = Typography;

const SEVERITIES: Severity[] = ["critical", "high", "medium", "low", "info"];

interface SimRow {
  rule_id: string;
  severity: Severity;
}

interface SimResultRow {
  policy_id: number;
  policy_name: string;
  policy_type: string;
  enabled: boolean;
  threshold: string;
  blocked: boolean;
  reason: string;
  matched: string[];
}

interface SimResponse {
  results: SimResultRow[];
  summary: { total_policies: number; blocked: number; passed: number };
}

export default function PolicySimulator() {
  const { t } = useI18n();
  const [rows, setRows] = useState<SimRow[]>([
    { rule_id: "CVE-2024-EXAMPLE", severity: "high" },
  ]);
  const [result, setResult] = useState<SimResponse | null>(null);

  const run = useMutation({
    mutationFn: async () => {
      const { data } = await api.post<SimResponse>("/policy/simulate", { findings: rows });
      return data;
    },
    onSuccess: (data) => setResult(data),
  });

  return (
    <div>
      <Title level={2} style={{ marginBottom: 8 }}>
        {t.policySim.title}
      </Title>
      <Paragraph type="secondary">{t.policySim.desc}</Paragraph>

      <Card style={{ marginTop: 12 }}>
        <Space direction="vertical" style={{ width: "100%" }}>
          {rows.map((r, idx) => (
            <Space key={idx} style={{ width: "100%" }}>
              <Input
                placeholder={t.policySim.ruleId}
                value={r.rule_id}
                onChange={(e) =>
                  setRows((rows) =>
                    rows.map((row, i) => (i === idx ? { ...row, rule_id: e.target.value } : row)),
                  )
                }
                style={{ width: 320 }}
              />
              <Select
                value={r.severity}
                onChange={(v) =>
                  setRows((rows) =>
                    rows.map((row, i) => (i === idx ? { ...row, severity: v } : row)),
                  )
                }
                options={SEVERITIES.map((s) => ({ value: s, label: s.toUpperCase() }))}
                style={{ width: 140 }}
              />
              <Button
                icon={<DeleteOutlined />}
                onClick={() => setRows((rows) => rows.filter((_, i) => i !== idx))}
                danger
              />
            </Space>
          ))}
          <Space>
            <Button
              icon={<PlusOutlined />}
              onClick={() => setRows((rows) => [...rows, { rule_id: "", severity: "medium" }])}
            >
              {t.policySim.add}
            </Button>
            <Button
              type="primary"
              icon={<ThunderboltOutlined />}
              loading={run.isPending}
              onClick={() => run.mutate()}
              disabled={rows.length === 0}
            >
              {t.policySim.simulate}
            </Button>
          </Space>
        </Space>
      </Card>

      {result && (
        <Card title={t.policySim.result} style={{ marginTop: 16 }}>
          <Alert
            style={{ marginBottom: 12 }}
            type={result.summary.blocked > 0 ? "error" : "success"}
            showIcon
            message={
              <>
                {result.summary.blocked > 0
                  ? `${result.summary.blocked} ${t.policySim.blocked}`
                  : `${result.summary.passed} ${t.policySim.passed}`}
              </>
            }
          />
          <Table
            dataSource={result.results}
            rowKey="policy_id"
            size="small"
            pagination={false}
            columns={[
              { title: "Policy", dataIndex: "policy_name" },
              {
                title: "Type",
                dataIndex: "policy_type",
                render: (v: string) => <Tag color="purple">{v}</Tag>,
                width: 110,
              },
              {
                title: "Threshold",
                dataIndex: "threshold",
                render: (v: string) => <Tag>{v}</Tag>,
                width: 110,
              },
              {
                title: t.policySim.result,
                dataIndex: "blocked",
                render: (b: boolean, row) => (
                  <Tag color={b ? "red" : "green"}>
                    {b ? t.policySim.blocked : t.policySim.passed}
                    {!row.enabled && " (disabled)"}
                  </Tag>
                ),
                width: 120,
              },
              { title: "Reason", dataIndex: "reason", ellipsis: true },
            ]}
          />
        </Card>
      )}
    </div>
  );
}
