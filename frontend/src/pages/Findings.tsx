/**
 * Findings — 발견된 보안 이슈 + 상태 변경 + AI 분석
 */

import { BulbOutlined } from "@ant-design/icons";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Alert,
  Button,
  Drawer,
  Select,
  Space,
  Table,
  Tag,
  Typography,
  message,
} from "antd";
import { useState } from "react";

import {
  api,
  type AIInsight,
  type Finding,
  type FindingStatus,
  type Page,
  type Severity,
} from "@/lib/api";

import { useI18n } from "@/i18n";

const { Title, Text, Paragraph } = Typography;

const SEVERITY_COLOR: Record<Severity, string> = {
  critical: "#ef4444",
  high: "#f97316",
  medium: "#eab308",
  low: "#22c55e",
  info: "#3b82f6",
};

const STATUS_OPTIONS: FindingStatus[] = [
  "new",
  "triaged",
  "in_progress",
  "resolved",
  "suppressed",
  "false_positive",
];

async function fetchFindings(): Promise<Page<Finding>> {
  const { data } = await api.get<Page<Finding>>("/findings", { params: { limit: 100 } });
  return data;
}

async function fetchInsights(findingId: number): Promise<AIInsight[]> {
  const { data } = await api.get<AIInsight[]>(`/ai/findings/${findingId}/insights`);
  return data;
}

export default function Findings() {
  const { t } = useI18n();
  const qc = useQueryClient();
  const [selected, setSelected] = useState<Finding | null>(null);

  const { data, isLoading } = useQuery({ queryKey: ["findings"], queryFn: fetchFindings });

  const { data: insights, refetch: refetchInsights } = useQuery({
    queryKey: ["finding-insights", selected?.id],
    queryFn: () => fetchInsights(selected!.id),
    enabled: !!selected,
  });

  const triage = useMutation({
    mutationFn: (findingId: number) => api.post<AIInsight>(`/ai/findings/${findingId}/triage`),
    onSuccess: () => {
      message.success("AI 분석 완료");
      refetchInsights();
    },
    onError: (err) => message.error(`분석 실패: ${err.message}`),
  });

  const updateStatus = useMutation({
    mutationFn: ({ id, status }: { id: number; status: FindingStatus }) =>
      api.patch<Finding>(`/findings/${id}`, { status }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["findings"] }),
  });

  return (
    <div>
      <Title level={2} style={{ marginBottom: 16 }}>
        {t.findings.title}
      </Title>

      <Table
        loading={isLoading}
        dataSource={data?.items ?? []}
        rowKey="id"
        onRow={(record) => ({ onClick: () => setSelected(record), style: { cursor: "pointer" } })}
        columns={[
          { title: "ID", dataIndex: "id", width: 70 },
          {
            title: t.common.severity,
            dataIndex: "severity",
            render: (s: Severity) => (
              <Tag color={SEVERITY_COLOR[s]}>{s.toUpperCase()}</Tag>
            ),
            width: 110,
          },
          { title: t.common.title, dataIndex: "title", ellipsis: true },
          { title: t.common.scanner, dataIndex: "scanner", width: 110 },
          { title: "Rule", dataIndex: "rule_id", width: 200, ellipsis: true },
          {
            title: t.common.status,
            dataIndex: "status",
            width: 160,
            render: (s: FindingStatus, record: Finding) => (
              <Select
                size="small"
                value={s}
                style={{ width: "100%" }}
                onClick={(e) => e.stopPropagation()}
                onChange={(val) => updateStatus.mutate({ id: record.id, status: val })}
                options={STATUS_OPTIONS.map((o) => ({ value: o, label: o }))}
              />
            ),
          },
        ]}
      />

      <Drawer
        open={!!selected}
        onClose={() => setSelected(null)}
        width={560}
        title={selected ? `#${selected.id} · ${selected.title}` : ""}
      >
        {selected && (
          <Space direction="vertical" size="middle" style={{ width: "100%" }}>
            <Space>
              <Tag color={SEVERITY_COLOR[selected.severity]}>
                {selected.severity.toUpperCase()}
              </Tag>
              <Tag>{selected.scanner}</Tag>
              <Tag>{selected.rule_id}</Tag>
            </Space>
            {selected.location && <Text type="secondary">📍 {selected.location}</Text>}
            {selected.description && <Paragraph>{selected.description}</Paragraph>}
            {selected.references.length > 0 && (
              <div>
                <Text strong>{t.findings.references}</Text>
                <ul>
                  {selected.references.map((r: string) => (
                    <li key={r}>
                      <a href={r} target="_blank" rel="noreferrer">
                        {r}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <Text strong>{t.menu.aiInsights}</Text>
              <Button
                type="primary"
                size="small"
                icon={<BulbOutlined />}
                loading={triage.isPending}
                onClick={() => triage.mutate(selected.id)}
              >
                {t.common.runTriage}
              </Button>
            </div>

            {(insights ?? []).length === 0 && (
              <Alert type="info" showIcon message={t.findings.drawerNoInsight} />
            )}
            {(insights ?? []).map((i) => (
              <div
                key={i.id}
                style={{
                  border: "1px solid var(--mond-border)",
                  borderRadius: 8,
                  padding: 16,
                  background: "var(--mond-surface)",
                }}
              >
                <Space>
                  <Tag color="purple">{i.kind}</Tag>
                  <Tag>{i.model}</Tag>
                  {i.recommended_severity && (
                    <Tag color={SEVERITY_COLOR[i.recommended_severity as Severity]}>
                      → {i.recommended_severity}
                    </Tag>
                  )}
                  {typeof i.confidence === "number" && (
                    <Tag>confidence {(i.confidence * 100).toFixed(0)}%</Tag>
                  )}
                </Space>
                <Paragraph style={{ marginTop: 12 }}>{i.summary}</Paragraph>
                {i.remediation?.steps && i.remediation.steps.length > 0 && (
                  <>
                    <Text strong>{t.findings.remediation}</Text>
                    <ol>
                      {i.remediation.steps.map((s: string, idx: number) => (
                        <li key={idx}>{s}</li>
                      ))}
                    </ol>
                  </>
                )}
                {i.remediation?.code && (
                  <pre
                    style={{
                      background: "#0d1421",
                      padding: 12,
                      borderRadius: 6,
                      overflowX: "auto",
                    }}
                  >
                    <code>{i.remediation.code}</code>
                  </pre>
                )}
              </div>
            ))}
          </Space>
        )}
      </Drawer>
    </div>
  );
}
