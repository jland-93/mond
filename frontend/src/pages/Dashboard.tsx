/**
 * 🌙 Dashboard — 보안 점수, 자산/발견 현황, 최근 스캔
 */

import { useQuery } from "@tanstack/react-query";
import { Card, Col, Progress, Row, Statistic, Table, Tag, Typography } from "antd";
import {
  Cell,
  PieChart,
  Pie,
  ResponsiveContainer,
  Tooltip,
} from "recharts";

import { useI18n } from "@/i18n";
import { api, type DashboardOverview, type Severity } from "@/lib/api";

const { Title, Text } = Typography;

const SEVERITY_COLOR: Record<Severity, string> = {
  critical: "#ef4444",
  high: "#f97316",
  medium: "#eab308",
  low: "#22c55e",
  info: "#3b82f6",
};

async function fetchOverview(): Promise<DashboardOverview> {
  const { data } = await api.get<DashboardOverview>("/dashboard/overview");
  return data;
}

export default function Dashboard() {
  const { t } = useI18n();
  const { data, isLoading } = useQuery({
    queryKey: ["dashboard-overview"],
    queryFn: fetchOverview,
    refetchInterval: 15_000,
  });

  const severityData: { name: string; value: number; color: string }[] | undefined =
    data &&
    (Object.entries(data.open_findings_by_severity) as [Severity, number][])
      .filter(([, v]) => v > 0)
      .map(([k, v]) => ({
        name: k.toUpperCase(),
        value: v,
        color: SEVERITY_COLOR[k],
      }));

  return (
    <div>
      <Title level={2} style={{ color: "var(--mond-text)", marginBottom: 24 }}>
        🌙 {t.dashboard.title}
      </Title>

      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card loading={isLoading}>
            <Statistic
              title={t.dashboard.securityScore}
              value={data?.security_score ?? 0}
              suffix="/100"
              valueStyle={{ color: "#22c55e" }}
            />
            <Progress
              percent={data?.security_score ?? 0}
              showInfo={false}
              strokeColor="#22c55e"
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card loading={isLoading}>
            <Statistic title={t.dashboard.assets} value={data?.asset_total ?? 0} />
            <Text type="secondary">{t.dashboard.assetsHint}</Text>
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card loading={isLoading}>
            <Statistic
              title={t.dashboard.openFindings}
              value={data?.open_findings_total ?? 0}
              valueStyle={{ color: "#f97316" }}
            />
            <Text type="secondary">{t.dashboard.openFindingsHint}</Text>
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card loading={isLoading}>
            <Statistic title={t.dashboard.scans7d} value={data?.scans_last_7d ?? 0} />
            <Text type="secondary">{t.dashboard.scans7dHint}</Text>
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={12}>
          <Card title={t.dashboard.severityChart} loading={isLoading}>
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie
                  data={severityData ?? []}
                  dataKey="value"
                  nameKey="name"
                  innerRadius={70}
                  outerRadius={110}
                  paddingAngle={4}
                >
                  {(severityData ?? []).map((d) => (
                    <Cell key={d.name} fill={d.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    background: "var(--mond-surface)",
                    border: "1px solid var(--mond-border)",
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title={t.dashboard.recentFindings} loading={isLoading}>
            <Table
              dataSource={data?.recent_findings ?? []}
              rowKey="id"
              size="small"
              pagination={false}
              columns={[
                {
                  title: "Severity",
                  dataIndex: "severity",
                  render: (s: Severity) => (
                    <Tag color={SEVERITY_COLOR[s]}>{s.toUpperCase()}</Tag>
                  ),
                  width: 110,
                },
                { title: "Title", dataIndex: "title", ellipsis: true },
                { title: "Scanner", dataIndex: "scanner", width: 100 },
              ]}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col span={24}>
          <Card title={t.dashboard.recentScans} loading={isLoading}>
            <Table
              dataSource={data?.recent_scans ?? []}
              rowKey="id"
              size="small"
              pagination={false}
              columns={[
                { title: "Scan #", dataIndex: "id", width: 90 },
                { title: "Asset", dataIndex: "asset_id", width: 110 },
                { title: "Scanner", dataIndex: "scanner" },
                {
                  title: "Status",
                  dataIndex: "status",
                  render: (s: string) => (
                    <Tag
                      color={
                        s === "completed"
                          ? "green"
                          : s === "failed"
                            ? "red"
                            : "blue"
                      }
                    >
                      {s}
                    </Tag>
                  ),
                  width: 120,
                },
                { title: "Findings", dataIndex: "findings_count", width: 100 },
                {
                  title: "When",
                  dataIndex: "created_at",
                  render: (v: string) => new Date(v).toLocaleString(),
                },
              ]}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
}
