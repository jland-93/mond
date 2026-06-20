/**
 * 🌒 Dashboard v3 — 3D 입체 카드 · Donut · Area · Activity 타임라인
 *
 * 차별점:
 *  · 3D perspective + multi-layer shadow + hover tilt
 *  · Donut chart (radial gradient + drop shadow) — severity 분포
 *  · 7일 area chart (finding + scan) — gradient fill
 *  · Activity 타임라인 — 스캔/finding/access 통합 피드
 *  · Top Assets — 미해결 개수 기준
 */

import { useQuery } from "@tanstack/react-query";
import { Empty, Typography } from "antd";
import {
  Area,
  AreaChart,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import MoonPhase, { phaseForSeverity } from "@/components/MoonPhase";
import { useI18n } from "@/i18n";
import { api, type DashboardOverview, type Severity } from "@/lib/api";
import NextSteps from "@/pages/dashboard/NextSteps";

const { Text } = Typography;

const SEVERITY_CSSVAR: Record<Severity, string> = {
  critical: "var(--severity-critical)",
  high: "var(--severity-high)",
  medium: "var(--severity-medium)",
  low: "var(--severity-low)",
  info: "var(--severity-info)",
};

const KIND_LABEL_KO: Record<string, string> = { scan: "스캔", finding: "발견", access: "권한" };
const KIND_LABEL_EN: Record<string, string> = { scan: "SCAN", finding: "FIND", access: "ACCESS" };

async function fetchOverview(): Promise<DashboardOverview> {
  const { data } = await api.get<DashboardOverview>("/dashboard/overview");
  return data;
}

function moodCopy(score: number, locale: "ko" | "en"): string {
  if (locale === "ko") {
    if (score >= 85) return "이번 주는 비교적 안정적입니다";
    if (score >= 65) return "관리 가능한 수준 — 우선순위만 잡으면 됩니다";
    if (score >= 40) return "주의 — 미해결 항목을 살펴봐야 합니다";
    return "위험 — 핵심 통제 점검이 필요합니다";
  }
  if (score >= 85) return "This week looks stable";
  if (score >= 65) return "Manageable — focus on priorities";
  if (score >= 40) return "Attention needed";
  return "At risk — review core controls";
}

function timeAgo(iso: string, locale: "ko" | "en"): string {
  const ms = Date.now() - new Date(iso).getTime();
  const m = Math.floor(ms / 60_000);
  if (m < 1) return locale === "ko" ? "방금" : "now";
  if (m < 60) return locale === "ko" ? `${m}분 전` : `${m}m`;
  const h = Math.floor(m / 60);
  if (h < 24) return locale === "ko" ? `${h}시간 전` : `${h}h`;
  const d = Math.floor(h / 24);
  return locale === "ko" ? `${d}일 전` : `${d}d`;
}

export default function Dashboard() {
  const { locale } = useI18n();
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
      .map(([k, v]) => ({ name: k.toUpperCase(), key: k, value: v, color: SEVERITY_CSSVAR[k] }));

  const trend = data?.trend_7d ?? [];
  const trendMax = Math.max(1, ...trend.map((d) => Math.max(d.findings, d.scans)));

  return (
    <div className="mond-dashboard">
      <Text style={{ color: "var(--fg-tertiary)", fontSize: 12, letterSpacing: "0.08em" }}>
        DASHBOARD
      </Text>

      <NextSteps overview={data} />

      {/* Hero — Moon score + 7일 area chart */}
      <section className="mond-tile mond-hero3d">
        <div className="mond-hero3d-left">
          <div className="mond-hero3d-moon">
            <MoonPhase phase={phase} size={150} color="var(--accent)" shadowColor="var(--surface-1)" />
          </div>
          <div>
            <Text style={{ color: "var(--fg-tertiary)", fontSize: 11, letterSpacing: "0.1em" }}>
              {locale === "ko" ? "오늘의 보안 점수" : "TODAY'S SECURITY SCORE"}
            </Text>
            <div className="mond-hero-score">
              <span className="mond-hero-num">{score}</span>
              <span className="mond-hero-denom">/100</span>
            </div>
            <Text style={{ color: "var(--fg-primary)", fontSize: 16, fontWeight: 500, lineHeight: 1.4 }}>
              {moodCopy(score, locale)}
            </Text>
          </div>
        </div>

        <div className="mond-hero3d-right">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
            <Text style={{ color: "var(--fg-tertiary)", fontSize: 11, letterSpacing: "0.1em" }}>
              {locale === "ko" ? "최근 7일 흐름" : "LAST 7 DAYS"}
            </Text>
            <Text style={{ color: "var(--fg-secondary)", fontSize: 12 }}>
              {locale === "ko"
                ? `발견 ${trend.reduce((s, d) => s + d.findings, 0)} · 스캔 ${trend.reduce((s, d) => s + d.scans, 0)}`
                : `${trend.reduce((s, d) => s + d.findings, 0)} found · ${trend.reduce((s, d) => s + d.scans, 0)} scans`}
            </Text>
          </div>
          <ResponsiveContainer width="100%" height={120}>
            <AreaChart data={trend} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="findGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="oklch(82% 0.08 180)" stopOpacity={0.6} />
                  <stop offset="100%" stopColor="oklch(82% 0.08 180)" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="scanGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="oklch(70% 0.14 285)" stopOpacity={0.4} />
                  <stop offset="100%" stopColor="oklch(70% 0.14 285)" stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis dataKey="date" tick={{ fill: "var(--fg-tertiary)", fontSize: 10 }} axisLine={false} tickLine={false} />
              <YAxis domain={[0, trendMax * 1.2]} hide />
              <Tooltip
                contentStyle={{ background: "var(--surface-2)", border: "1px solid var(--border)", borderRadius: 8, fontSize: 12 }}
                cursor={{ stroke: "var(--accent)", strokeOpacity: 0.3 }}
              />
              <Area type="monotone" dataKey="findings" stroke="oklch(82% 0.08 180)" strokeWidth={2} fill="url(#findGrad)" />
              <Area type="monotone" dataKey="scans" stroke="oklch(70% 0.14 285)" strokeWidth={1.5} fill="url(#scanGrad)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </section>

      {/* Bento: Donut + small KPIs */}
      <section className="mond-bento">
        <div className="mond-tile mond-tile-wide">
          <div className="mond-tile-head">
            <span className="mond-tile-label">{locale === "ko" ? "심각도 분포" : "BY SEVERITY"}</span>
            <span className="mond-tile-meta">
              {locale === "ko" ? "총 미해결" : "open"} {data?.open_findings_total ?? 0}
            </span>
          </div>
          <div className="mond-donut-wrap">
            {severityChart && severityChart.length > 0 ? (
              <>
                <div style={{ position: "relative", width: 200, height: 200 }}>
                  <ResponsiveContainer width={200} height={200}>
                    <PieChart>
                      <defs>
                        {severityChart.map((d) => (
                          <radialGradient key={`g-${d.key}`} id={`donut-${d.key}`}>
                            <stop offset="0%" stopColor={d.color} stopOpacity={1} />
                            <stop offset="100%" stopColor={d.color} stopOpacity={0.5} />
                          </radialGradient>
                        ))}
                      </defs>
                      <Pie data={severityChart} dataKey="value" nameKey="name" innerRadius={62} outerRadius={92} paddingAngle={3} stroke="var(--surface-1)" strokeWidth={2}>
                        {severityChart.map((d) => (
                          <Cell key={d.key} fill={`url(#donut-${d.key})`} style={{ filter: `drop-shadow(0 4px 12px ${d.color})` }} />
                        ))}
                      </Pie>
                      <Tooltip contentStyle={{ background: "var(--surface-2)", border: "1px solid var(--border)", borderRadius: 8, fontSize: 12 }} />
                    </PieChart>
                  </ResponsiveContainer>
                  <div className="mond-donut-center">
                    <div style={{ fontSize: 32, fontWeight: 700, lineHeight: 1, color: "var(--fg-primary)", fontVariantNumeric: "tabular-nums" }}>
                      {data?.open_findings_total ?? 0}
                    </div>
                    <Text style={{ fontSize: 10, color: "var(--fg-tertiary)", letterSpacing: "0.08em" }}>
                      {locale === "ko" ? "미해결" : "OPEN"}
                    </Text>
                  </div>
                </div>
                <div className="mond-donut-legend">
                  {severityChart.map((d) => (
                    <div key={d.key} className="mond-legend-item">
                      <MoonPhase phase={phaseForSeverity(d.key)} size={12} color={d.color} />
                      <span style={{ fontSize: 11, color: "var(--fg-secondary)", flex: 1 }}>{d.name}</span>
                      <span className="mond-numeric" style={{ fontSize: 13, color: d.color, fontWeight: 600 }}>
                        {d.value}
                      </span>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <Empty
                imageStyle={{ opacity: 0.4 }}
                description={<span style={{ color: "var(--fg-tertiary)", fontSize: 13 }}>{locale === "ko" ? "오늘은 미해결 항목이 없습니다" : "No open findings"}</span>}
              />
            )}
          </div>
        </div>

        <KpiTile3D label={locale === "ko" ? "자산" : "ASSETS"} value={data?.asset_total ?? 0} icon="cube" loading={isLoading} />
        <KpiTile3D label={locale === "ko" ? "주간 스캔" : "SCANS · 7D"} value={data?.scans_last_7d ?? 0} icon="scan" loading={isLoading} />
        <KpiTile3D label={locale === "ko" ? "미해결" : "OPEN"} value={data?.open_findings_total ?? 0} icon="alert" loading={isLoading} tone={(data?.open_findings_total ?? 0) > 0 ? "warn" : "ok"} />
      </section>

      {/* Activity + Top Assets */}
      <section className="mond-rows">
        <div className="mond-tile">
          <div className="mond-tile-head">
            <span className="mond-tile-label">{locale === "ko" ? "활동 피드" : "ACTIVITY"}</span>
            <span className="mond-tile-meta">{data?.activity?.length ?? 0}</span>
          </div>
          {(data?.activity?.length ?? 0) === 0 ? (
            <Empty imageStyle={{ opacity: 0.4 }} description={<span style={{ color: "var(--fg-tertiary)", fontSize: 13 }}>{locale === "ko" ? "활동 없음" : "No activity"}</span>} />
          ) : (
            <ul className="mond-activity">
              {(data?.activity ?? []).map((a) => {
                const sev = a.severity as Severity;
                const color = SEVERITY_CSSVAR[sev] ?? "var(--fg-tertiary)";
                return (
                  <li key={`${a.kind}-${a.id}`} className="mond-activity-item">
                    <span className="mond-activity-dot" style={{ background: `radial-gradient(circle at 30% 30%, ${color}, color-mix(in oklch, ${color} 40%, transparent))`, boxShadow: `0 0 12px ${color}` }} />
                    <span className="mond-activity-kind">{locale === "ko" ? KIND_LABEL_KO[a.kind] : KIND_LABEL_EN[a.kind]}</span>
                    <span className="mond-activity-label">{a.label}</span>
                    <span className="mond-activity-meta">{a.meta}</span>
                    <span className="mond-activity-time">{timeAgo(a.at, locale)}</span>
                  </li>
                );
              })}
            </ul>
          )}
        </div>

        <div className="mond-tile">
          <div className="mond-tile-head">
            <span className="mond-tile-label">{locale === "ko" ? "주의 자산 Top 5" : "TOP RISKY ASSETS"}</span>
            <span className="mond-tile-meta">{data?.top_assets?.length ?? 0}</span>
          </div>
          {(data?.top_assets?.length ?? 0) === 0 ? (
            <Empty imageStyle={{ opacity: 0.4 }} description={<span style={{ color: "var(--fg-tertiary)", fontSize: 13 }}>{locale === "ko" ? "데이터 없음" : "No data"}</span>} />
          ) : (
            <ul className="mond-asset-list">
              {(data?.top_assets ?? []).map((a, i) => {
                const max = data?.top_assets?.[0]?.open_findings ?? 1;
                const pct = Math.round((a.open_findings / Math.max(1, max)) * 100);
                return (
                  <li key={a.id} className="mond-asset-row">
                    <span className="mond-asset-rank">{String(i + 1).padStart(2, "0")}</span>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ display: "flex", alignItems: "baseline", gap: 8 }}>
                        <span style={{ color: "var(--fg-primary)", fontSize: 13, fontWeight: 500, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{a.name}</span>
                        <span className="mond-mono" style={{ color: "var(--fg-tertiary)", fontSize: 10 }}>{a.asset_type}</span>
                      </div>
                      <div className="mond-asset-bar">
                        <div className="mond-asset-bar-fill" style={{ width: `${pct}%`, background: `linear-gradient(90deg, var(--severity-high), var(--severity-critical))` }} />
                      </div>
                    </div>
                    <span className="mond-numeric" style={{ color: "var(--severity-high)", fontSize: 16, fontWeight: 700, minWidth: 30, textAlign: "right" }}>{a.open_findings}</span>
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      </section>

      <style>{`
        .mond-dashboard { padding-bottom: 32px; }
        .mond-tile {
          padding: 20px 22px;
          background: linear-gradient(180deg, color-mix(in oklch, var(--surface-1) 96%, var(--accent) 4%) 0%, var(--surface-1) 100%);
          border: 1px solid var(--border);
          border-radius: var(--radius-lg);
          position: relative; overflow: hidden;
          box-shadow:
            0 1px 0 oklch(96% 0.005 60 / 0.04) inset,
            0 1px 2px oklch(0% 0 0 / 0.25),
            0 8px 24px oklch(0% 0 0 / 0.20);
          transition: transform var(--motion-normal) var(--motion-ease),
                      box-shadow var(--motion-normal) var(--motion-ease),
                      border-color var(--motion-fast) var(--motion-ease);
        }
        .mond-tile::after {
          content: ""; position: absolute; inset: 0;
          background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='200' height='200'><filter id='n'><feTurbulence baseFrequency='0.9' numOctaves='2'/></filter><rect width='100%25' height='100%25' filter='url(%23n)' opacity='0.018'/></svg>");
          pointer-events: none;
        }
        .mond-tile:hover {
          transform: translateY(-2px);
          border-color: var(--border-strong);
          box-shadow:
            0 1px 0 oklch(96% 0.005 60 / 0.06) inset,
            0 4px 8px oklch(0% 0 0 / 0.30),
            0 18px 42px oklch(0% 0 0 / 0.32),
            0 0 0 1px color-mix(in oklch, var(--accent) 18%, transparent);
        }
        .mond-tile-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; position: relative; z-index: 1; }
        .mond-tile-label { font-size: 11px; letter-spacing: 0.1em; font-weight: 600; color: var(--fg-tertiary); }
        .mond-tile-meta { font-size: 12px; color: var(--fg-secondary); font-variant-numeric: tabular-nums; }

        .mond-hero3d {
          display: grid; grid-template-columns: 1.1fr 1fr; gap: 32px;
          align-items: center; margin: 16px 0 16px; padding: 28px 32px; min-height: 200px;
        }
        @media (max-width: 900px) { .mond-hero3d { grid-template-columns: 1fr; } }
        @media (max-width: 560px) {
          .mond-hero3d { padding: 20px; gap: 20px; }
          .mond-hero3d-moon { width: 110px !important; height: 110px !important; }
          .mond-hero-num { font-size: 48px !important; }
        }
        .mond-hero3d-left {
          display: flex; align-items: center; gap: 28px;
          position: relative; z-index: 1; min-width: 0;
        }
        .mond-hero3d-left > div:last-child { min-width: 0; flex: 1; }
        .mond-hero3d-moon {
          position: relative; width: 150px; height: 150px;
          display: flex; align-items: center; justify-content: center;
          filter: drop-shadow(0 8px 32px oklch(82% 0.08 180 / 0.35));
          flex-shrink: 0;
        }
        .mond-hero3d-moon::before {
          content: ""; position: absolute; inset: -30px;
          background: radial-gradient(circle at center, oklch(82% 0.08 180 / 0.22) 0%, transparent 65%);
          z-index: -1;
        }
        .mond-hero-score { display: flex; align-items: baseline; gap: 6px; margin: 6px 0 4px; }
        .mond-hero-num {
          font-size: 64px; font-weight: 700; letter-spacing: -0.04em; line-height: 1;
          font-variant-numeric: tabular-nums;
          background: linear-gradient(180deg, var(--fg-primary) 0%, color-mix(in oklch, var(--fg-primary) 60%, var(--accent)) 100%);
          -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
        }
        .mond-hero-denom { font-size: 18px; color: var(--fg-tertiary); font-variant-numeric: tabular-nums; }
        .mond-hero3d-right { position: relative; z-index: 1; display: flex; flex-direction: column; gap: 8px; }

        .mond-bento {
          display: grid; grid-template-columns: 1.6fr 1fr 1fr 1fr; gap: 14px; margin-bottom: 16px;
        }
        @media (max-width: 1100px) {
          .mond-bento { grid-template-columns: 1fr 1fr; }
          .mond-tile-wide { grid-column: span 2; }
        }
        @media (max-width: 640px) {
          .mond-bento { grid-template-columns: 1fr; }
          .mond-tile-wide { grid-column: span 1; }
        }
        .mond-tile-wide { min-height: 260px; }

        .mond-donut-wrap {
          display: grid; grid-template-columns: auto 1fr; gap: 24px;
          align-items: center; position: relative; z-index: 1;
        }
        .mond-donut-center {
          position: absolute; left: 50%; top: 50%;
          transform: translate(-50%, -50%);
          text-align: center; pointer-events: none;
        }
        .mond-donut-legend { display: flex; flex-direction: column; gap: 10px; min-width: 0; }
        .mond-legend-item {
          display: flex; align-items: center; gap: 10px; padding: 6px 10px;
          background: color-mix(in oklch, var(--surface-2) 60%, transparent);
          border-radius: 8px;
        }

        .mond-kpi { display: flex; flex-direction: column; padding: 20px 22px; position: relative; }
        .mond-kpi-icon {
          width: 36px; height: 36px;
          display: flex; align-items: center; justify-content: center;
          border-radius: 10px;
          background: linear-gradient(140deg,
            color-mix(in oklch, var(--accent) 25%, var(--surface-2)) 0%,
            color-mix(in oklch, var(--accent) 10%, var(--surface-1)) 100%);
          border: 1px solid color-mix(in oklch, var(--accent) 30%, transparent);
          box-shadow: 0 4px 12px color-mix(in oklch, var(--accent) 20%, transparent);
          font-size: 18px; margin-bottom: 16px;
        }
        .mond-kpi-num {
          font-size: 42px; font-weight: 700; letter-spacing: -0.03em; line-height: 1;
          font-variant-numeric: tabular-nums; margin-top: auto;
        }
        .mond-kpi-hint { font-size: 11px; color: var(--fg-tertiary); margin-top: 6px; letter-spacing: 0.04em; }

        .mond-rows { display: grid; grid-template-columns: 1.2fr 1fr; gap: 14px; }
        @media (max-width: 1100px) { .mond-rows { grid-template-columns: 1fr; } }

        .mond-activity { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; position: relative; z-index: 1; }
        .mond-activity-item {
          display: grid;
          grid-template-columns: 14px 48px 1fr auto auto;
          gap: 10px; align-items: center; padding: 8px 4px;
          border-bottom: 1px solid color-mix(in oklch, var(--border) 60%, transparent);
        }
        .mond-activity-item:last-child { border-bottom: none; }
        .mond-activity-dot { width: 10px; height: 10px; border-radius: 50%; }
        .mond-activity-kind { font-size: 10px; letter-spacing: 0.08em; font-weight: 600; color: var(--fg-tertiary); }
        .mond-activity-label { font-size: 13px; color: var(--fg-primary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        .mond-activity-meta { font-size: 11px; color: var(--fg-tertiary); font-family: var(--font-mono); }
        .mond-activity-time { font-size: 11px; color: var(--fg-tertiary); font-variant-numeric: tabular-nums; }

        .mond-asset-list { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 12px; position: relative; z-index: 1; }
        .mond-asset-row { display: flex; align-items: center; gap: 12px; }
        .mond-asset-rank { font-family: var(--font-mono); font-size: 11px; color: var(--fg-tertiary); width: 24px; }
        .mond-asset-bar { margin-top: 6px; height: 4px; border-radius: 2px; background: color-mix(in oklch, var(--surface-2) 80%, transparent); overflow: hidden; }
        .mond-asset-bar-fill {
          height: 100%;
          box-shadow: 0 0 12px oklch(74% 0.18 60 / 0.5);
          transition: width var(--motion-slow) var(--motion-ease);
        }
      `}</style>
    </div>
  );
}

function KpiTile3D({
  label, value, hint, loading, tone = "default", icon = "cube",
}: {
  label: string;
  value: number;
  hint?: string;
  loading?: boolean;
  tone?: "default" | "ok" | "warn";
  icon?: "cube" | "scan" | "alert";
}) {
  const valueColor =
    tone === "warn" ? "var(--severity-high)" :
    tone === "ok" ? "var(--severity-low)" :
    "var(--fg-primary)";
  const iconEmoji = icon === "scan" ? "◐" : icon === "alert" ? "▲" : "▣";
  return (
    <div className="mond-tile mond-kpi">
      <div className="mond-kpi-icon" style={{ color: tone === "warn" ? "var(--severity-high)" : "var(--accent)" }}>
        {iconEmoji}
      </div>
      <span className="mond-tile-label" style={{ marginBottom: 4 }}>{label}</span>
      <div className="mond-kpi-num" style={{ color: valueColor }}>{loading ? "—" : value}</div>
      {hint && <span className="mond-kpi-hint">{hint}</span>}
    </div>
  );
}
