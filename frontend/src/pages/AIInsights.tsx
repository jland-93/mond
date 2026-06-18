/**
 * 🌙 AI Insights — 자연어로 묻고 의도 분류 결과 받기
 */

import { SendOutlined } from "@ant-design/icons";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Alert, Button, Card, Input, Space, Tag, Typography } from "antd";
import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";

import { useI18n } from "@/i18n";
import { api } from "@/lib/api";

const { Title, Paragraph } = Typography;
const { TextArea } = Input;

interface AnalyzeResponse {
  intent: string;
  summary: string;
  suggested_actions: Array<{ label: string; endpoint?: string }>;
  model: string;
}

async function fetchStatus(): Promise<{ enabled: boolean }> {
  const { data } = await api.get<{ enabled: boolean }>("/ai/status");
  return data;
}

export default function AIInsights() {
  const { t } = useI18n();
  const [params, setParams] = useSearchParams();
  const [query, setQuery] = useState(params.get("q") ?? "");
  const { data: status } = useQuery({ queryKey: ["ai-status"], queryFn: fetchStatus });

  const analyze = useMutation<AnalyzeResponse, Error, string>({
    mutationFn: async (q: string) => {
      const { data } = await api.post<AnalyzeResponse>("/ai/analyze", { query: q });
      return data;
    },
  });

  // Knowledge Hub 등 외부에서 ?q=...로 진입했을 때 자동 분석 + 쿼리스트링 정리
  useEffect(() => {
    const seed = params.get("q");
    if (seed && seed.trim()) {
      analyze.mutate(seed);
      setParams({}, { replace: true });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div>
      <Title
        level={2}
        style={{ marginBottom: 16, display: "flex", alignItems: "center", gap: 10 }}
      >
        <img
          src="/logo.png"
          alt=""
          width={28}
          height={28}
          style={{
            borderRadius: 6,
            filter: "drop-shadow(0 0 8px oklch(72% 0.16 285 / 0.5))",
          }}
        />
        {t.ai.title}
      </Title>

      {!status?.enabled && (
        <Alert
          type="warning"
          showIcon
          style={{ marginBottom: 16 }}
          message={t.ai.disabled}
          description={t.ai.disabledHint}
        />
      )}

      <Card title={t.ai.title}>
        <Paragraph type="secondary">{t.ai.askExample}</Paragraph>
        <Space.Compact style={{ width: "100%" }}>
          <TextArea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={t.ai.askPlaceholder}
            autoSize={{ minRows: 2, maxRows: 6 }}
          />
          <Button
            type="primary"
            icon={<SendOutlined />}
            onClick={() => analyze.mutate(query)}
            loading={analyze.isPending}
            disabled={!query.trim()}
            style={{ height: "auto" }}
          >
            {t.ai.analyze}
          </Button>
        </Space.Compact>

        {analyze.data && (
          <Card style={{ marginTop: 16 }} type="inner">
            <Space direction="vertical" style={{ width: "100%" }}>
              <Space>
                <Tag color="purple">intent: {analyze.data.intent}</Tag>
                <Tag>{analyze.data.model}</Tag>
              </Space>
              <Paragraph>{analyze.data.summary}</Paragraph>
              {analyze.data.suggested_actions.length > 0 && (
                <div>
                  <strong>Suggested actions</strong>
                  <ul>
                    {analyze.data.suggested_actions.map((a, i) => (
                      <li key={i}>
                        {a.label}
                        {a.endpoint ? ` — ${a.endpoint}` : ""}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </Space>
          </Card>
        )}
      </Card>
    </div>
  );
}
