/**
 * 🌙 AI Insights — 자연어로 묻고 의도 분류 결과 받기
 */

import { SendOutlined } from "@ant-design/icons";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Alert, Button, Card, Input, Space, Tag, Typography } from "antd";
import { useState } from "react";

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
  const [query, setQuery] = useState("");
  const { data: status } = useQuery({ queryKey: ["ai-status"], queryFn: fetchStatus });

  const analyze = useMutation({
    mutationFn: (q: string) =>
      api.post<AnalyzeResponse>("/ai/analyze", { query: q }).then((r) => r.data),
  });

  return (
    <div>
      <Title level={2} style={{ marginBottom: 16 }}>
        🌙 AI Insights
      </Title>

      {!status?.enabled && (
        <Alert
          type="warning"
          showIcon
          style={{ marginBottom: 16 }}
          message="ANTHROPIC_API_KEY가 설정되지 않았습니다 — 휴리스틱 모드"
          description="실제 Claude 분석을 사용하려면 .env에 ANTHROPIC_API_KEY를 설정하고 백엔드를 재시작하세요."
        />
      )}

      <Card title="자연어로 묻기">
        <Paragraph type="secondary">
          예시: <em>"우리 nginx 이미지 스캔해줘"</em>, <em>"이번 주 critical 이슈 뭐 있어?"</em>,{" "}
          <em>"이 SSRF 취약점 왜 위험한지 설명해"</em>
        </Paragraph>
        <Space.Compact style={{ width: "100%" }}>
          <TextArea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Mond에게 무엇이든 물어보세요"
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
            분석
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
