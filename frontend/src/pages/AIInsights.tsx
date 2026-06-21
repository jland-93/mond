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
  redactions?: Record<string, number>;
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
                {Object.entries(analyze.data.redactions ?? {}).map(([kind, n]) => (
                  <Tooltip
                    key={kind}
                    title={
                      locale === "ko"
                        ? `외부 LLM 호출 전 ${kind} ${n}건을 자동 마스킹 처리했습니다.`
                        : `Masked ${n} ${kind} before sending to external LLM.`
                    }
                  >
                    <Tag color="gold">
                      redacted {kind}:{n}
                    </Tag>
                  </Tooltip>
                ))}
              </Space>
              <Paragraph style={{ whiteSpace: "pre-wrap" }}>
                {renderSummaryWithCitations(
                  analyze.data.summary,
                  analyze.data.citations ?? [],
                  jumpTo,
                )}
              </Paragraph>

              <FollowUps
                intent={analyze.data.intent}
                suggested={analyze.data.suggested_actions ?? []}
                onAsk={(q) => {
                  setQuery(q);
                  analyze.mutate(q);
                }}
                locale={locale}
              />

              {analyze.data.suggested_actions.length > 0 && (
                <div>
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    {locale === "ko" ? "Claude 제안 endpoint" : "Claude suggested endpoints"}
                  </Text>
                  <ul style={{ marginBottom: 0, fontSize: 12 }}>
                    {analyze.data.suggested_actions
                      .filter((a) => a.endpoint)
                      .map((a, i) => (
                        <li key={i}>
                          <Text code>{a.endpoint}</Text> — {a.label}
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

/** intent별 표준 follow-up + Claude suggested_actions의 label을 chip으로 노출. */
function FollowUps({
  intent,
  suggested,
  onAsk,
  locale,
}: {
  intent: string;
  suggested: Array<{ label: string; endpoint?: string }>;
  onAsk: (q: string) => void;
  locale: "ko" | "en";
}) {
  // 1) AI가 제안한 label에서 자연어 후보를 모음
  const fromAi = suggested
    .map((a) => a.label?.trim())
    .filter((l): l is string => !!l)
    .slice(0, 3);

  // 2) intent별 표준 follow-up (외부 LLM 없어도 흐름이 끊기지 않도록)
  const intentFallbacks: Record<string, { ko: string[]; en: string[] }> = {
    scan: {
      ko: ["방금 스캔 결과 요약해줘", "이 자산에 자동 스캔 일정을 잡으려면?"],
      en: ["Summarize the latest scan", "How do I auto-schedule scans?"],
    },
    list_findings: {
      ko: ["critical만 보여줘", "이번 주 새로 발견된 것만", "open 상태만 알려줘"],
      en: ["Show critical only", "New this week", "Open only"],
    },
    explain: {
      ko: ["수정 가이드(remediation)도 보여줘", "관련 정책이 있어?"],
      en: ["Show remediation", "Any related policy?"],
    },
    unknown: {
      ko: ["우리 critical 자산 알려줘", "ISMS-P 매핑 정책 보여줘", "최근 만료된 권한 회수 내역"],
      en: ["Top critical assets", "ISMS-P mapped policies", "Recent expired permissions"],
    },
  };

  const fallbacks = (intentFallbacks[intent] ?? intentFallbacks.unknown)[locale];
  const items = Array.from(new Set([...fromAi, ...fallbacks])).slice(0, 6);

  if (items.length === 0) return null;

  return (
    <div>
      <Text type="secondary" style={{ fontSize: 12, display: "block", marginBottom: 6 }}>
        {locale === "ko" ? "이어서 묻기" : "Follow-up"}
      </Text>
      <Space size={[6, 6]} wrap>
        {items.map((q, i) => (
          <Tag
            key={i}
            color="default"
            style={{ cursor: "pointer", padding: "4px 10px", fontSize: 12 }}
            onClick={() => onAsk(q)}
          >
            {q}
          </Tag>
        ))}
      </Space>
    </div>
  );
}
