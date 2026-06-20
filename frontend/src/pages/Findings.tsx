/**
 * Findings — 발견된 보안 이슈 + 상태 변경 + AI 분석
 */

import {
  ArrowRightOutlined,
  BulbOutlined,
  CheckOutlined,
  EnvironmentOutlined,
  RobotOutlined,
} from "@ant-design/icons";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Button,
  Drawer,
  Empty,
  Popconfirm,
  Progress,
  Select,
  Space,
  Table,
  Tag,
  Tooltip,
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
  const { t, locale } = useI18n();
  const qc = useQueryClient();
  const [selected, setSelected] = useState<Finding | null>(null);
  const [checked, setChecked] = useState<number[]>([]);

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

  const bulkUpdate = useMutation({
    mutationFn: (status: FindingStatus) =>
      api.patch<{ updated: number }>("/findings/bulk/status", {
        finding_ids: checked,
        status,
      }),
    onSuccess: (r) => {
      message.success(
        locale === "ko"
          ? `${r.data.updated}개 발견사항 상태 변경됨`
          : `${r.data.updated} findings updated`,
      );
      setChecked([]);
      qc.invalidateQueries({ queryKey: ["findings"] });
    },
    onError: (err: Error) => message.error(err.message),
  });

  return (
    <div>
      <Title level={2} style={{ marginBottom: 16 }}>
        {t.findings.title}
      </Title>

      {checked.length > 0 && (
        <Space style={{ marginBottom: 12 }} wrap>
          <Tag color="blue" style={{ fontSize: 13, padding: "4px 10px" }}>
            {locale === "ko" ? `${checked.length}개 선택됨` : `${checked.length} selected`}
          </Tag>
          <Popconfirm
            title={locale === "ko" ? "선택한 발견을 해결로 표시할까요?" : "Mark selected as resolved?"}
            onConfirm={() => bulkUpdate.mutate("resolved")}
          >
            <Button size="small" icon={<CheckOutlined />}>
              {locale === "ko" ? "일괄: 해결" : "Bulk: Resolved"}
            </Button>
          </Popconfirm>
          <Popconfirm
            title={locale === "ko" ? "선택한 발견을 억제(무시)할까요?" : "Suppress selected?"}
            onConfirm={() => bulkUpdate.mutate("suppressed")}
          >
            <Button size="small">{locale === "ko" ? "일괄: 억제" : "Bulk: Suppress"}</Button>
          </Popconfirm>
          <Popconfirm
            title={locale === "ko" ? "선택한 발견을 false-positive로 표시할까요?" : "Mark as false-positive?"}
            onConfirm={() => bulkUpdate.mutate("false_positive")}
          >
            <Button size="small">{locale === "ko" ? "일괄: False positive" : "Bulk: FP"}</Button>
          </Popconfirm>
          <Button size="small" type="text" onClick={() => setChecked([])}>
            {locale === "ko" ? "선택 해제" : "Clear"}
          </Button>
        </Space>
      )}

      <Table
        loading={isLoading}
        dataSource={data?.items ?? []}
        rowKey="id"
        rowSelection={{
          selectedRowKeys: checked,
          onChange: (keys) => setChecked(keys as number[]),
        }}
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
        width={620}
        title={selected ? `#${selected.id} · ${selected.title}` : ""}
      >
        {selected && (
          <Space direction="vertical" size="middle" style={{ width: "100%" }}>
            {/* 자산 정보 — 어느 자산의 어느 위치에서 발견됐는지 */}
            {selected.asset_name && (
              <div
                style={{
                  border: "1px solid var(--mond-border)",
                  borderRadius: 8,
                  padding: 12,
                  background: "var(--mond-surface-2, transparent)",
                }}
              >
                <Space size={6} wrap>
                  <Text type="secondary" style={{ fontSize: 11 }}>
                    {locale === "ko" ? "발견된 자산" : "FOUND ON"}
                  </Text>
                  <Text strong>{selected.asset_name}</Text>
                  {selected.asset_type && <Tag style={{ marginInlineEnd: 0 }}>{selected.asset_type}</Tag>}
                  {selected.asset_environment && (
                    <Tag color="blue" style={{ marginInlineEnd: 0 }}>
                      {selected.asset_environment}
                    </Tag>
                  )}
                </Space>
                {selected.location && (
                  <div style={{ marginTop: 6 }}>
                    <EnvironmentOutlined style={{ marginRight: 6, color: "var(--mond-text-dim)" }} />
                    <Text type="secondary" style={{ fontFamily: "var(--mond-font-mono, monospace)", fontSize: 12 }}>
                      {selected.location}
                    </Text>
                  </div>
                )}
              </div>
            )}

            <Space wrap>
              <Tag color={SEVERITY_COLOR[selected.severity]}>
                {selected.severity.toUpperCase()}
              </Tag>
              <Tag>{selected.scanner}</Tag>
              <Tag>{selected.rule_id}</Tag>
            </Space>
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

            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <Space>
                <RobotOutlined style={{ color: "var(--severity-info, #8a8aff)" }} />
                <Text strong>{t.menu.aiInsights}</Text>
              </Space>
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
              <Empty
                description={
                  <Space direction="vertical" align="center" size={4}>
                    <Text strong>
                      {locale === "ko" ? "아직 AI 분석 결과가 없습니다" : "No AI insight yet"}
                    </Text>
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      {locale === "ko"
                        ? "위 'AI 분석 실행' 버튼을 누르면 Claude가 자산 컨텍스트로 severity 재평가 + 수정 가이드를 생성합니다."
                        : "Click 'Run AI triage' to let Claude re-assess severity and propose a remediation."}
                    </Text>
                  </Space>
                }
              />
            )}
            {(insights ?? []).map((i) => {
              const kindKo: Record<string, string> = {
                triage: "분류",
                remediation: "수정 가이드",
                summary: "요약",
                explain: "해설",
              };
              const isAuthored = !i.model.startsWith("rule");
              return (
                <div
                  key={i.id}
                  style={{
                    border: "1px solid var(--mond-border)",
                    borderRadius: 8,
                    padding: 16,
                    background: "var(--mond-surface)",
                  }}
                >
                  <Space size={6} wrap>
                    <Tag color="purple">{kindKo[i.kind] ?? i.kind}</Tag>
                    <Tooltip title={isAuthored ? (locale === "ko" ? "AI provider 응답" : "From AI provider") : (locale === "ko" ? "AI provider 미설정 — 기본 규칙 모드" : "Heuristic (no AI provider)")}>
                      <Tag color={isAuthored ? "geekblue" : "default"}>{i.model}</Tag>
                    </Tooltip>
                    {i.recommended_severity && i.recommended_severity !== selected.severity && (
                      <Tooltip title={locale === "ko" ? "AI 추천 severity로 재평가" : "Severity reassessed by AI"}>
                        <Space size={4}>
                          <Tag color={SEVERITY_COLOR[selected.severity]} style={{ marginInlineEnd: 0 }}>
                            {selected.severity}
                          </Tag>
                          <ArrowRightOutlined style={{ fontSize: 11, color: "var(--mond-text-dim)" }} />
                          <Tag color={SEVERITY_COLOR[i.recommended_severity as Severity]} style={{ marginInlineEnd: 0 }}>
                            {i.recommended_severity}
                          </Tag>
                        </Space>
                      </Tooltip>
                    )}
                    {typeof i.confidence === "number" && (
                      <Tooltip title={locale === "ko" ? `AI 신뢰도 ${(i.confidence * 100).toFixed(0)}%` : `Confidence ${(i.confidence * 100).toFixed(0)}%`}>
                        <div style={{ minWidth: 100, display: "inline-flex", alignItems: "center", gap: 4 }}>
                          <Text type="secondary" style={{ fontSize: 11 }}>
                            {locale === "ko" ? "신뢰도" : "conf."}
                          </Text>
                          <Progress
                            percent={Math.round(i.confidence * 100)}
                            size="small"
                            showInfo={false}
                            strokeColor="var(--severity-info, #8a8aff)"
                            style={{ width: 70, marginBottom: 0 }}
                          />
                          <Text style={{ fontSize: 11 }}>{Math.round(i.confidence * 100)}%</Text>
                        </div>
                      </Tooltip>
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
                  {i.remediation?.references && i.remediation.references.length > 0 && (
                    <div style={{ marginTop: 8 }}>
                      <Text strong style={{ fontSize: 12 }}>
                        {locale === "ko" ? "AI 참고" : "AI references"}
                      </Text>
                      <ul style={{ marginBottom: 0 }}>
                        {i.remediation.references.map((r: string) => (
                          <li key={r}>
                            <a href={r} target="_blank" rel="noreferrer">
                              {r}
                            </a>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              );
            })}
          </Space>
        )}
      </Drawer>
    </div>
  );
}
