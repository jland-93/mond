/**
 * 🌒 Dashboard — Moon-phase 보안 점수 + bento 비대칭 그리드
 *
 * AI 디폴트(4-column 균일 카드)를 깨고, 거대 KPI hero + bento 2:1:1:1 비율로
 * 위계를 만든다. 보안 점수는 Moon-phase SVG 시그니처로.
 */

import { useQuery } from "@tanstack/react-query";
import { Empty, Table, Tag, Typography } from "antd";
import {
  Bar,
  BarChart,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
} from "recharts";

import MoonPhase, { phaseForSeverity } from "@/components/MoonPhase";
import { useI18n } from "@/i18n";
import { api, type DashboardOverview, type Severity } from "@/lib/api";

const { Title, Text } = Typography;

const SEVERITY_CSSVAR: Record<Severity, string> = {
  critical: "var(--severity-critical)",
  high: "var(--severity-high)",
  medium: "var(--severity-medium)",
  low: "var(--severity-low)",
  info: "var(--severity-info)",
};

async function fetchOverview(): Promise<DashboardOverview> {
  const { data } = await api.get<DashboardOverview>("/dashboard/overview");
  return data;
}

/** 보안 점수 → 한 줄 카피. AI 도구의 차분한 톤. */
function moodCopy(score: number, locale: "ko" | "en"): string {
  if (locale === "ko") {
    if (score >= 85) return "이번 주는 비교적 안정적입니다";
    if (score >= 65) return "관리 가능한 수준 — 우선순위만 잡으면 됩니다";
    if (score >= 40) return "주의 — 미해결 항목을 살펴봐야 합니다";
    return "위험 — 핵심 통제 점검이 필요합니다";
  }
  if (score >= 85) return "This week looks stable";
  if (score >= 65) return "Manageable — focus on priorities";
  if (score >= 40) return "Attention needed — review open items";
  return "At risk — review core controls";
}

export default function Dashboard() {
  const { t, locale } = useI18n();
  const { data, isLoading } = useQuery({
    queryKey: ["dashboard-overview"],
    queryFn: fetchOverview,
    refetchInterval: 15_000,
  });

  const score = data?.security_score ?? 0;
  const phase = Math.max(0.04, Math.min(1, score / 100));

  const severityChart =
    data &&
    (Object.entries(data.open_findings_by_severity) as [Severity, number][])
      .filter(([, v]) => v > 0)
      .map(([k, v]) => ({ name: k.toUpperCase(), key: k, value: v }));

  return (
    <div className="mond-dashboard">
      <Title level={2} style={{ margin: 0, color: "var(--fg-secondary)", fontSize: 14, fontWeight: 500, letterSpacing: "0.04em" }}>
        DASHBOARD
      </Title>

      {/* ── Hero — Moon-phase 보안 점수 + 거대 카피 ─────────────── */}
      <section className="mond-hero">
        <div className="mond-hero-moon">
          <MoonPhase
            phase={phase}
            size={180}
            color="var(--accent)"
            shadowColor="var(--surface-1)"
          />
          <div
            aria-hidden
            style={{
              position: "absolute",
              inset: -40,
              background:
                "radial-gradient(circle at 40% 45%, oklch(82% 0.08 180 / 0.22) 0%, transparent 65%)",
              pointerEvents: "none",
              zIndex: -1,
            }}
          />
        </div>
        <div className="mond-hero-text">
          <Text style={{ color: "var(--fg-tertiary)", fontSize: 12, letterSpacing: "0.08em" }}>
            {locale === "ko" ? "오늘의 보안 점수" : "TODAY'S SECURITY SCORE"}
          </Text>
          <div className="mond-hero-score">
            <span className="mond-hero-num">{score}</span>
            <span className="mond-hero-denom">/100</span>
          </div>
          <Text style={{ color: "var(--fg-primary)", fontSize: 18, fontWeight: 500, lineHeight: 1.4 }}>
            {moodCopy(score, locale)}
          </Text>
        </div>
      </section>

      {/* ── Bento — 2:1:1:1 비대칭. AI 디폴트 4-column grid 깨기 ───── */}
      <section className="mond-bento">
        {/* 좌측 큰 카드 — Severity 분포 */}
        <div className="mond-tile mond-tile-wide">
          <div className="mond-tile-head">
            <span className="mond-tile-label">{locale === "ko" ? "심각도 분포" : "BY SEVERITY"}</span>
            <span className="mond-tile-meta">
              {locale === "ko" ? "미해결" : "open"} {data?.open_findings_total ?? 0}
            </span>
          </div>
          {severityChart && severityChart.length > 0 ? (
            <div style={{ flex: 1, minHeight: 180, display: "flex", flexDirection: "column", gap: 12 }}>
              <ResponsiveContainer width="100%" height={140}>
                <BarChart
                  data={severityChart}
                  layout="vertical"
                  margin={{ top: 4, right: 24, left: 0, bottom: 0 }}
                >
                  <XAxis type="number" hide />
                  <Tooltip
                    cursor={{ fill: "oklch(82% 0.06 180 / 0.06)" }}
                    contentStyle={{
                      background: "var(--surface-2)",
                      border: "1px solid var(--border)",
                      borderRadius: 8,
                      fontSize: 12,
                    }}
                  />
                  <Bar dataKey="value" radius={[0, 6, 6, 0]}>
                    {severityChart.map((d) => (
                      <Cell key={d.key} fill={SEVERITY_CSSVAR[d.key]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
              <div style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
                {severityChart.map((d) => (
                  <div key={d.key} style={{ display: "flex", alignItems: "center", gap: 6 }}>
                    <MoonPhase phase={phaseForSeverity(d.key)} size={14} color={SEVERITY_CSSVAR[d.key]} />
                    <span style={{ fontSize: 12, color: "var(--fg-secondary)" }}>{d.name}</span>
                    <span className="mond-numeric" style={{ fontSize: 13, color: "var(--fg-primary)", fontWeight: 600 }}>
                      {d.value}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <Empty
              imageStyle={{ opacity: 0.4 }}
              description={
                <span style={{ color: "var(--fg-tertiary)", fontSize: 13 }}>
                  {locale === "ko" ? "오늘은 미해결 항목이 없습니다" : "No open findings"}
                </span>
              }
            />
          )}
        </div>

        {/* 우측 3개 — small KPI tiles */}
        <KpiTile
          label={locale === "ko" ? "자산" : "ASSETS"}
          value={data?.asset_total ?? 0}
          hint={t.dashboard.assetsHint}
          loading={isLoading}
        />
        <KpiTile
          label={locale === "ko" ? "주간 스캔" : "SCANS · 7D"}
          value={data?.scans_last_7d ?? 0}
          hint={t.dashboard.scans7dHint}
          loading={isLoading}
        />
        <KpiTile
          label={locale === "ko" ? "미해결" : "OPEN"}
          value={data?.open_findings_total ?? 0}
          hint={t.dashboard.openFindingsHint}
          loading={isLoading}
          tone={(data?.open_findings_total ?? 0) > 0 ? "warn" : "ok"}
        />
      </section>

      {/* ── 최근 발견사항 + 스캔 — 일반 row, 시그니처 spacing ───── */}
      <section className="mond-rows">
        <div className="mond-tile">
          <div className="mond-tile-head">
            <span className="mond-tile-label">
              {locale === "ko" ? "최근 발견사항" : "RECENT FINDINGS"}
            </span>
            <span className="mond-tile-meta">{data?.recent_findings?.length ?? 0}</span>
          </div>
          <Table
            dataSource={data?.recent_findings ?? []}
            rowKey="id"
            size="small"
            pagination={false}
            showHeader={false}
            locale={{ emptyText: <Empty description={locale === "ko" ? "기록 없음" : "No data"} /> }}
            columns={[
              {
                title: "",
                dataIndex: "severity",
                width: 40,
                render: (s: Severity) => (
                  <MoonPhase phase={phaseForSeverity(s)} size={16} color={SEVERITY_CSSVAR[s]} />
                ),
              },
              {
                title: "",
                dataIndex: "title",
                ellipsis: true,
                render: (txt: string) => (
                  <span style={{ color: "var(--fg-primary)", fontSize: 13 }}>{txt}</span>
                ),
              },
              {
                title: "",
                dataIndex: "scanner",
                width: 90,
                render: (s: string) => (
                  <span className="mond-mono" style={{ color: "var(--fg-tertiary)" }}>
                    {s}
                  </span>
                ),
              },
            ]}
          />
        </div>

        <div className="mond-tile">
          <div className="mond-tile-head">
            <span className="mond-tile-label">
              {locale === "ko" ? "최근 스캔" : "RECENT SCANS"}
            </span>
            <span className="mond-tile-meta">{data?.recent_scans?.length ?? 0}</span>
          </div>
          <Table
            dataSource={data?.recent_scans ?? []}
            rowKey="id"
            size="small"
            pagination={false}
            showHeader={false}
            locale={{ emptyText: <Empty description={locale === "ko" ? "기록 없음" : "No data"} /> }}
            columns={[
              {
                title: "",
                dataIndex: "scanner",
                width: 90,
                render: (s: string) => (
                  <span className="mond-mono" style={{ color: "var(--fg-tertiary)" }}>
                    {s}
                  </span>
                ),
              },
              {
                title: "",
                dataIndex: "status",
                width: 100,
                render: (s: string) => (
                  <Tag
                    style={{
                      background:
                        s === "completed" ? "var(--severity-low-bg)" :
                        s === "failed" ? "var(--severity-critical-bg)" :
                        "var(--severity-info-bg)",
                      color:
                        s === "completed" ? "var(--severity-low)" :
                        s === "failed" ? "var(--severity-critical)" :
                        "var(--severity-info)",
                      border: "none",
                      borderRadius: 999,
                      fontSize: 11,
                    }}
                  >
                    {s}
                  </Tag>
                ),
              },
              {
                title: "",
                dataIndex: "findings_count",
                width: 60,
                render: (v: number) => (
                  <span className="mond-numeric" style={{ color: "var(--fg-secondary)" }}>{v}</span>
                ),
              },
              {
                title: "",
                dataIndex: "created_at",
                render: (v: string) => (
                  <span style={{ color: "var(--fg-tertiary)", fontSize: 12 }}>
                    {new Date(v).toLocaleString(locale === "ko" ? "ko-KR" : "en-US", {
                      month: "short", day: "numeric", hour: "2-digit", minute: "2-digit",
                    })}
                  </span>
                ),
              },
            ]}
          />
        </div>
      </section>

      <style>{`
        .mond-dashboard {
          padding-bottom: 32px;
        }
        .mond-hero {
          display: grid;
          grid-template-columns: auto 1fr;
          align-items: center;
          gap: 32px;
          padding: 28px 32px;
          margin: 16px 0 28px;
          background:
            radial-gradient(ellipse at 0% 50%, oklch(82% 0.08 180 / 0.06), transparent 60%),
            var(--surface-1);
          border: 1px solid var(--border);
          border-radius: var(--radius-lg);
          position: relative;
          overflow: hidden;
        }
        .mond-hero::after {
          content: "";
          position: absolute;
          inset: 0;
          background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='200' height='200'><filter id='n'><feTurbulence baseFrequency='0.9' numOctaves='2'/></filter><rect width='100%' height='100%' filter='url(%23n)' opacity='0.02'/></svg>");
          pointer-events: none;
        }
        .mond-hero-moon {
          position: relative;
          display: flex;
          align-items: center;
          justify-content: center;
          width: 180px;
          height: 180px;
        }
        .mond-hero-text {
          display: flex;
          flex-direction: column;
          gap: 6px;
        }
        .mond-hero-score {
          display: flex;
          align-items: baseline;
          gap: 6px;
        }
        .mond-hero-num {
          font-size: 80px;
          font-weight: 700;
          letter-spacing: -0.04em;
          line-height: 1;
          color: var(--fg-primary);
          font-variant-numeric: tabular-nums;
          background: linear-gradient(180deg, var(--fg-primary) 0%, color-mix(in oklch, var(--fg-primary) 70%, var(--accent)) 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
        }
        .mond-hero-denom {
          font-size: 22px;
          color: var(--fg-tertiary);
          font-variant-numeric: tabular-nums;
        }

        .mond-bento {
          display: grid;
          grid-template-columns: 2fr 1fr 1fr 1fr;
          gap: 12px;
          margin-bottom: 16px;
        }
        @media (max-width: 1100px) {
          .mond-bento { grid-template-columns: 1fr 1fr; }
          .mond-tile-wide { grid-column: span 2; }
        }
        @media (max-width: 640px) {
          .mond-bento { grid-template-columns: 1fr; }
          .mond-tile-wide { grid-column: span 1; }
        }

        .mond-rows {
          display: grid;
          grid-template-columns: 1.1fr 1fr;
          gap: 12px;
        }
        @media (max-width: 1100px) {
          .mond-rows { grid-template-columns: 1fr; }
        }

        .mond-tile {
          padding: 18px 20px;
          background: var(--surface-1);
          border: 1px solid var(--border);
          border-radius: var(--radius-md);
          display: flex;
          flex-direction: column;
          min-height: 168px;
          transition: border-color var(--motion-fast) var(--motion-ease);
        }
        .mond-tile:hover {
          border-color: var(--border-strong);
        }
        .mond-tile-wide {
          min-height: 240px;
        }
        .mond-tile-head {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 12px;
        }
        .mond-tile-label {
          font-size: 11px;
          color: var(--fg-tertiary);
          letter-spacing: 0.08em;
          font-weight: 600;
        }
        .mond-tile-meta {
          font-size: 12px;
          color: var(--fg-secondary);
          font-variant-numeric: tabular-nums;
        }
      `}</style>
    </div>
  );
}

function KpiTile({
  label, value, hint, loading, tone = "default",
}: {
  label: string;
  value: number;
  hint?: string;
  loading?: boolean;
  tone?: "default" | "ok" | "warn";
}) {
  const valueColor =
    tone === "warn" ? "var(--severity-high)" :
    tone === "ok" ? "var(--severity-low)" :
    "var(--fg-primary)";
  return (
    <div className="mond-tile">
      <div className="mond-tile-head">
        <span className="mond-tile-label">{label}</span>
      </div>
      <div
        className="mond-numeric"
        style={{
          fontSize: 44,
          fontWeight: 700,
          letterSpacing: "-0.03em",
          lineHeight: 1,
          color: valueColor,
          marginTop: "auto",
          marginBottom: 6,
        }}
      >
        {loading ? "—" : value}
      </div>
      {hint && (
        <span style={{ fontSize: 12, color: "var(--fg-tertiary)", lineHeight: 1.4 }}>
          {hint}
        </span>
      )}
    </div>
  );
}
