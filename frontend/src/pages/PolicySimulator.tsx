/**
 * Policy Simulator — 가상 finding 입력 → 어떤 정책 게이트가 차단되나
 *
 * builtin은 임계치 비교, opa는 Rego 평가. 결과 행에 engine + matched 메시지를
 * expand로 노출 — 보안 담당자가 OPA deny 메시지나 차단된 finding을 즉시 확인.
 */

import {
  DeleteOutlined,
  PlusOutlined,
  RobotOutlined,
  ThunderboltOutlined,
} from "@ant-design/icons";
import { useMutation } from "@tanstack/react-query";
import {
  Alert,
  Button,
  Card,
  Empty,
  Input,
  Select,
  Space,
  Table,
  Tag,
  Typography,
} from "antd";
import { useState } from "react";

import { useI18n } from "@/i18n";
import { api, type Severity } from "@/lib/api";

const { Title, Paragraph, Text } = Typography;

const SEVERITIES: Severity[] = ["critical", "high", "medium", "low", "info"];

const SEVERITY_COLOR: Record<string, string> = {
  critical: "#e8484a",
  high: "#f29142",
  medium: "#eab308",
  low: "#4ad28d",
  info: "#8a8aff",
};

const ENGINE_COLOR: Record<string, string> = {
  builtin: "default",
  opa: "geekblue",
};

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
  engine?: string;
}

interface SimResponse {
  results: SimResultRow[];
  summary: { total_policies: number; blocked: number; passed: number };
}

export default function PolicySimulator() {
  const { t, locale } = useI18n();
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
      <Space size={8} style={{ marginBottom: 8 }}>
        <Title level={2} style={{ margin: 0 }}>
          {t.policySim.title}
        </Title>
        <Tag color="default" style={{ fontSize: 11 }}>
          EXPERIMENTAL
        </Tag>
      </Space>
      <Paragraph type="secondary">{t.policySim.desc}</Paragraph>
      <Alert
        type="info"
        showIcon
        style={{ marginBottom: 12 }}
        message={
          locale === "ko"
            ? "가상 finding을 입력해 현재 정책 게이트가 어떻게 동작할지 미리 봅니다. 실제 자산/발견에 변화는 없습니다."
            : "Simulation only — does not modify real assets or findings."
        }
      />

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
                options={SEVERITIES.map((s) => ({
                  value: s,
                  label: (
                    <Space size={6}>
                      <span
                        style={{
                          display: "inline-block",
                          width: 8,
                          height: 8,
                          borderRadius: "50%",
                          background: SEVERITY_COLOR[s],
                        }}
                      />
                      <span>{s.toUpperCase()}</span>
                    </Space>
                  ),
                }))}
                style={{ width: 160 }}
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
              locale === "ko"
                ? `${result.summary.blocked}건 차단 · ${result.summary.passed}건 통과 · 총 ${result.summary.total_policies}개 정책`
                : `${result.summary.blocked} blocked · ${result.summary.passed} passed · ${result.summary.total_policies} policies total`
            }
          />
          <Table
            dataSource={result.results}
            rowKey="policy_id"
            size="small"
            pagination={false}
            rowClassName={(r) => (r.blocked ? "mond-row-high" : "")}
            locale={{
              emptyText: <Empty description={locale === "ko" ? "정책 없음" : "No policies"} />,
            }}
            expandable={{
              rowExpandable: (r) => r.matched.length > 0 || !r.enabled,
              expandedRowRender: (r) => (
                <Space direction="vertical" size={6} style={{ paddingBlock: 4, width: "100%" }}>
                  {!r.enabled && (
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      {locale === "ko"
                        ? "비활성 정책 — 게이트에 적용되지 않습니다."
                        : "Disabled policy — gate not applied."}
                    </Text>
                  )}
                  {r.matched.length > 0 && (
                    <>
                      <Text strong style={{ fontSize: 12 }}>
                        {r.engine === "opa"
                          ? locale === "ko"
                            ? "OPA deny 메시지"
                            : "OPA deny messages"
                          : locale === "ko"
                            ? "차단된 발견사항"
                            : "Findings that blocked"}
                      </Text>
                      <ul style={{ marginBottom: 0, paddingInlineStart: 18 }}>
                        {r.matched.map((m, i) => (
                          <li key={i}>
                            <Text style={{ fontSize: 12 }}>{m}</Text>
                          </li>
                        ))}
                      </ul>
                    </>
                  )}
                </Space>
              ),
            }}
            columns={[
              { title: locale === "ko" ? "정책" : "Policy", dataIndex: "policy_name" },
              {
                title: locale === "ko" ? "유형" : "Type",
                dataIndex: "policy_type",
                render: (v: string) => <Tag color="purple">{v}</Tag>,
                width: 110,
              },
              {
                title: "engine",
                dataIndex: "engine",
                render: (v: string) =>
                  v === "opa" ? (
                    <Tag color={ENGINE_COLOR.opa} icon={<RobotOutlined />} style={{ marginInlineEnd: 0 }}>
                      opa
                    </Tag>
                  ) : (
                    <Tag color={ENGINE_COLOR.builtin} style={{ marginInlineEnd: 0 }}>
                      builtin
                    </Tag>
                  ),
                width: 110,
              },
              {
                title: locale === "ko" ? "임계치" : "Threshold",
                dataIndex: "threshold",
                render: (v: string) => (
                  <Space size={6}>
                    <span
                      style={{
                        display: "inline-block",
                        width: 8,
                        height: 8,
                        borderRadius: "50%",
                        background: SEVERITY_COLOR[v] ?? "#999",
                      }}
                    />
                    <span>{v}</span>
                  </Space>
                ),
                width: 130,
              },
              {
                title: locale === "ko" ? "결과" : "Verdict",
                dataIndex: "blocked",
                render: (b: boolean, row) => (
                  <Tag color={!row.enabled ? "default" : b ? "red" : "green"} style={{ marginInlineEnd: 0 }}>
                    {!row.enabled
                      ? locale === "ko"
                        ? "비활성"
                        : "disabled"
                      : b
                        ? t.policySim.blocked
                        : t.policySim.passed}
                  </Tag>
                ),
                width: 110,
              },
              {
                title: locale === "ko" ? "사유" : "Reason",
                dataIndex: "reason",
                ellipsis: true,
              },
            ]}
          />
        </Card>
      )}
    </div>
  );
}
