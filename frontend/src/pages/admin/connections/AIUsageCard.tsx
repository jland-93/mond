/**
 * AI 토큰 사용량 — 최근 N일 호출수 + 입출력 토큰 + provider/tier/intent 분포.
 *
 * 외부 LLM 비용 가시화와 사내 vLLM 게이트웨이의 호출량 검증이 목적.
 * complete_json이 호출될 때마다 ai_usage_logs 테이블에 행 1건 기록되고,
 * 이 카드는 그 집계를 admin이 보도록 노출한다.
 */

import { BarChartOutlined } from "@ant-design/icons";
import { useQuery } from "@tanstack/react-query";
import { Card, Empty, Select, Space, Statistic, Table, Tag, Typography } from "antd";
import { useState } from "react";

import { useI18n } from "@/i18n";
import { api } from "@/lib/api";

const { Paragraph, Text } = Typography;

interface UsageSummary {
  days: number;
  since: string;
  total: { calls: number; input_tokens: number; output_tokens: number; failed: number };
  by_provider: { provider: string; calls: number; input_tokens: number; output_tokens: number }[];
  by_tier: { tier: string; calls: number; input_tokens: number; output_tokens: number }[];
  by_intent: { intent: string; calls: number; input_tokens: number; output_tokens: number }[];
  by_day: { day: string; calls: number; input_tokens: number; output_tokens: number }[];
}

const PROVIDER_COLOR: Record<string, string> = {
  anthropic: "purple",
  openai: "green",
  bedrock: "orange",
  ollama: "geekblue",
  vllm: "magenta",
};

function fmt(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}k`;
  return n.toLocaleString();
}

export default function AIUsageCard() {
  const { locale } = useI18n();
  const [days, setDays] = useState(7);

  const { data, isLoading } = useQuery({
    queryKey: ["ai-usage", days],
    queryFn: async () =>
      (await api.get<UsageSummary>("/admin/ai-providers/usage", { params: { days } })).data,
  });

  const total = data?.total ?? { calls: 0, input_tokens: 0, output_tokens: 0, failed: 0 };
  const empty = total.calls === 0;

  return (
    <Card
      title={
        <Space>
          <BarChartOutlined />
          <span>{locale === "ko" ? "AI 토큰 사용량" : "AI Token Usage"}</span>
        </Space>
      }
      extra={
        <Select
          value={days}
          onChange={setDays}
          style={{ width: 120 }}
          options={[
            { value: 1, label: locale === "ko" ? "오늘" : "Today" },
            { value: 7, label: locale === "ko" ? "최근 7일" : "Last 7d" },
            { value: 30, label: locale === "ko" ? "최근 30일" : "Last 30d" },
            { value: 90, label: locale === "ko" ? "최근 90일" : "Last 90d" },
          ]}
        />
      }
      style={{ marginBottom: 16 }}
    >
      <Paragraph type="secondary" style={{ marginBottom: 12 }}>
        {locale === "ko"
          ? "complete_json 호출 단위로 provider · 모델 tier · intent · 입출력 토큰을 기록합니다. 사내 vLLM/Ollama 게이트웨이 사용량과 외부 LLM 비용을 한 화면에."
          : "Every complete_json call records provider · model tier · intent · token counts. Track both on-prem (vLLM/Ollama) and external LLM cost in one view."}
      </Paragraph>

      {empty && !isLoading ? (
        <Empty
          description={
            locale === "ko"
              ? "기록된 호출이 없습니다. AI Insights / 권한 평가 / RAG 검색을 한 번 실행하면 여기에 누적됩니다."
              : "No recorded calls yet. Trigger AI Insights / access review / RAG to populate."
          }
        />
      ) : (
        <>
          <Space size={32} wrap style={{ marginBottom: 16 }}>
            <Statistic
              title={locale === "ko" ? "호출수" : "Calls"}
              value={total.calls}
              loading={isLoading}
            />
            <Statistic
              title={locale === "ko" ? "입력 토큰" : "Input tokens"}
              value={fmt(total.input_tokens)}
              loading={isLoading}
            />
            <Statistic
              title={locale === "ko" ? "출력 토큰" : "Output tokens"}
              value={fmt(total.output_tokens)}
              loading={isLoading}
            />
            <Statistic
              title={locale === "ko" ? "실패" : "Failed"}
              value={total.failed}
              valueStyle={{ color: total.failed > 0 ? "#cf1322" : undefined }}
              loading={isLoading}
            />
          </Space>

          <Space direction="vertical" size={12} style={{ width: "100%" }}>
            <div>
              <Text strong>{locale === "ko" ? "Provider별" : "By provider"}</Text>
              <Table
                size="small"
                rowKey="provider"
                pagination={false}
                dataSource={data?.by_provider ?? []}
                columns={[
                  {
                    title: locale === "ko" ? "Provider" : "Provider",
                    dataIndex: "provider",
                    render: (p: string) => (
                      <Tag color={PROVIDER_COLOR[p] ?? "default"} style={{ marginInlineEnd: 0 }}>
                        {p}
                      </Tag>
                    ),
                  },
                  { title: locale === "ko" ? "호출" : "Calls", dataIndex: "calls", width: 90 },
                  {
                    title: locale === "ko" ? "입력" : "In",
                    dataIndex: "input_tokens",
                    width: 100,
                    render: (n: number) => fmt(n),
                  },
                  {
                    title: locale === "ko" ? "출력" : "Out",
                    dataIndex: "output_tokens",
                    width: 100,
                    render: (n: number) => fmt(n),
                  },
                ]}
                style={{ marginTop: 6 }}
              />
            </div>

            <Space size={32} wrap>
              <div style={{ minWidth: 220 }}>
                <Text strong>{locale === "ko" ? "Tier별" : "By tier"}</Text>
                <Table
                  size="small"
                  rowKey="tier"
                  pagination={false}
                  dataSource={data?.by_tier ?? []}
                  columns={[
                    {
                      title: "Tier",
                      dataIndex: "tier",
                      render: (t: string) => (
                        <Tag color={t === "deep" ? "volcano" : "blue"} style={{ marginInlineEnd: 0 }}>
                          {t}
                        </Tag>
                      ),
                    },
                    { title: locale === "ko" ? "호출" : "Calls", dataIndex: "calls", width: 80 },
                    {
                      title: locale === "ko" ? "입+출" : "I+O",
                      key: "io",
                      width: 110,
                      render: (_: unknown, r) => fmt((r.input_tokens || 0) + (r.output_tokens || 0)),
                    },
                  ]}
                  style={{ marginTop: 6 }}
                />
              </div>

              <div style={{ flex: 1, minWidth: 280 }}>
                <Text strong>{locale === "ko" ? "Intent별 (상위 20)" : "By intent (top 20)"}</Text>
                <Table
                  size="small"
                  rowKey="intent"
                  pagination={false}
                  dataSource={data?.by_intent ?? []}
                  columns={[
                    { title: "Intent", dataIndex: "intent" },
                    { title: locale === "ko" ? "호출" : "Calls", dataIndex: "calls", width: 80 },
                    {
                      title: locale === "ko" ? "입+출" : "I+O",
                      key: "io",
                      width: 110,
                      render: (_: unknown, r) => fmt((r.input_tokens || 0) + (r.output_tokens || 0)),
                    },
                  ]}
                  style={{ marginTop: 6 }}
                />
              </div>
            </Space>
          </Space>
        </>
      )}
    </Card>
  );
}
