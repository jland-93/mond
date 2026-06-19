/**
 * AI Insights — 자연어로 묻고 의도 분류 결과 받기
 */

import { LinkOutlined, SendOutlined } from "@ant-design/icons";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Alert, Button, Card, Input, Space, Tag, Tooltip, Typography } from "antd";
import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";

import { useI18n } from "@/i18n";
import { api } from "@/lib/api";

const { Title, Paragraph, Text } = Typography;
const { TextArea } = Input;

interface Citation {
  n: number;
  kind: "asset" | "finding" | "policy" | "knowledge" | string;
  title: string;
  snippet: string;
  url?: string | null;
}

interface AnalyzeResponse {
  intent: string;
  summary: string;
  suggested_actions: Array<{ label: string; endpoint?: string }>;
  model: string;
  citations?: Citation[];
}

const KIND_COLOR: Record<string, string> = {
  asset: "green",
  finding: "red",
  policy: "purple",
  knowledge: "blue",
};

/** "...[1] 또는 [2]..." 같은 텍스트를 inline citation chip 으로 렌더. */
function renderSummaryWithCitations(
  summary: string,
  citations: Citation[],
  onJump: (c: Citation) => void,
): React.ReactNode[] {
  if (!summary) return [];
  const map = new Map(citations.map((c) => [c.n, c]));
  const parts: React.ReactNode[] = [];
  const re = /\[(\d+)\]/g;
  let last = 0;
  let m: RegExpExecArray | null;
  while ((m = re.exec(summary))) {
    if (m.index > last) parts.push(summary.slice(last, m.index));
    const n = Number(m[1]);
    const c = map.get(n);
    if (c) {
      parts.push(
        <Tooltip key={`c-${n}-${m.index}`} title={`${c.title} — ${c.snippet}`}>
          <Tag
            color={KIND_COLOR[c.kind] || "default"}
            style={{ cursor: "pointer", margin: "0 2px", fontWeight: 500 }}
            onClick={() => onJump(c)}
          >
            [{n}]
          </Tag>
        </Tooltip>,
      );
    } else {
      parts.push(m[0]);
    }
    last = m.index + m[0].length;
  }
  if (last < summary.length) parts.push(summary.slice(last));
  return parts;
}

async function fetchStatus(): Promise<{ enabled: boolean }> {
  const { data } = await api.get<{ enabled: boolean }>("/ai/status");
  return data;
}

export default function AIInsights() {
  const { t, locale } = useI18n();
  const navigate = useNavigate();
  const [params, setParams] = useSearchParams();
  const [query, setQuery] = useState(params.get("q") ?? "");

  const jumpTo = (c: Citation) => {
    if (!c.url) return;
    if (c.url.startsWith("http")) {
      window.open(c.url, "_blank", "noopener,noreferrer");
    } else {
      navigate(c.url);
    }
  };
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
              <Space wrap>
                <Tag color="purple">intent: {analyze.data.intent}</Tag>
                <Tag>{analyze.data.model}</Tag>
                {(analyze.data.citations?.length ?? 0) > 0 && (
                  <Tag color="cyan">
                    {locale === "ko" ? "출처" : "Sources"} {analyze.data.citations!.length}
                  </Tag>
                )}
              </Space>
              <Paragraph style={{ whiteSpace: "pre-wrap" }}>
                {renderSummaryWithCitations(
                  analyze.data.summary,
                  analyze.data.citations ?? [],
                  jumpTo,
                )}
              </Paragraph>

              {analyze.data.suggested_actions.length > 0 && (
                <div>
                  <Text strong>{locale === "ko" ? "제안된 행동" : "Suggested actions"}</Text>
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

              {(analyze.data.citations?.length ?? 0) > 0 && (
                <Card
                  type="inner"
                  size="small"
                  title={
                    <Space>
                      <LinkOutlined />
                      <span>{locale === "ko" ? "출처" : "Sources"}</span>
                    </Space>
                  }
                  style={{ background: "var(--mond-surface-2)" }}
                >
                  <Space direction="vertical" style={{ width: "100%" }}>
                    {analyze.data.citations!.map((c) => (
                      <div
                        key={c.n}
                        style={{
                          cursor: c.url ? "pointer" : "default",
                          padding: "6px 0",
                          borderBottom: "1px solid var(--mond-border)",
                        }}
                        onClick={() => jumpTo(c)}
                      >
                        <Space wrap>
                          <Tag color={KIND_COLOR[c.kind] || "default"}>[{c.n}]</Tag>
                          <Tag>{c.kind}</Tag>
                          <Text strong>{c.title}</Text>
                        </Space>
                        <Text type="secondary" style={{ display: "block", marginTop: 4 }}>
                          {c.snippet}
                        </Text>
                      </div>
                    ))}
                  </Space>
                </Card>
              )}
            </Space>
          </Card>
        )}
      </Card>
    </div>
  );
}
