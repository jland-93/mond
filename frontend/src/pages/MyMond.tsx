/**
 * My Mond — 임직원이 매일 처음 보는 본인 화면.
 *
 * 보안 담당자가 한 화면에서 조직 전체를 본다면,
 * 임직원은 한 화면에서 본인 자산·발견·권한·만료 임박을 본다.
 */

import { useQuery } from "@tanstack/react-query";
import { Card, Col, Empty, List, Row, Space, Tag, Typography } from "antd";
import { Link } from "react-router-dom";

import { useAuth } from "@/auth/AuthContext";
import { useI18n } from "@/i18n";
import { api, type MeOverview, type Severity } from "@/lib/api";

const { Title, Paragraph, Text } = Typography;

const SEVERITY_COLOR: Record<Severity, string> = {
  critical: "red",
  high: "volcano",
  medium: "orange",
  low: "gold",
  info: "default",
};

async function fetchMe(): Promise<MeOverview> {
  const { data } = await api.get<MeOverview>("/me/overview");
  return data;
}

export default function MyMond() {
  const { locale } = useI18n();
  const { user } = useAuth();
  const { data, isLoading } = useQuery({
    queryKey: ["me-overview"],
    queryFn: fetchMe,
    refetchInterval: 30_000,
  });

  const summary = data?.summary;
  const greeting = locale === "ko"
    ? `안녕하세요, ${user?.name || user?.email}님`
    : `Hello, ${user?.name || user?.email}`;

  return (
    <div>
      <Title level={2} style={{ marginBottom: 4 }}>
        {greeting}
      </Title>
      <Paragraph type="secondary">
        {locale === "ko"
          ? "내가 등록한 자산 · 받은 발견사항 · 권한 요청 · 만료 임박을 한눈에."
          : "Your assets, findings, requests, and expiring permissions at a glance."}
      </Paragraph>

      <Row gutter={[12, 12]} style={{ marginBottom: 16 }}>
        <Col xs={12} md={6}>
          <Card size="small" loading={isLoading}>
            <Text type="secondary" style={{ fontSize: 11, letterSpacing: "0.08em" }}>
              {locale === "ko" ? "내 자산" : "MY ASSETS"}
            </Text>
            <div style={{ fontSize: 32, fontWeight: 700, fontVariantNumeric: "tabular-nums" }}>
              {summary?.my_assets_total ?? 0}
            </div>
          </Card>
        </Col>
        <Col xs={12} md={6}>
          <Card size="small" loading={isLoading}>
            <Text type="secondary" style={{ fontSize: 11, letterSpacing: "0.08em" }}>
              {locale === "ko" ? "미해결 발견" : "OPEN FINDINGS"}
            </Text>
            <div
              style={{
                fontSize: 32,
                fontWeight: 700,
                fontVariantNumeric: "tabular-nums",
                color: (summary?.open_findings_total ?? 0) > 0 ? "var(--severity-high)" : undefined,
              }}
            >
              {summary?.open_findings_total ?? 0}
            </div>
          </Card>
        </Col>
        <Col xs={12} md={6}>
          <Card size="small" loading={isLoading}>
            <Text type="secondary" style={{ fontSize: 11, letterSpacing: "0.08em" }}>
              {locale === "ko" ? "진행중 권한 요청" : "ACTIVE REQUESTS"}
            </Text>
            <div style={{ fontSize: 32, fontWeight: 700, fontVariantNumeric: "tabular-nums" }}>
              {summary?.active_requests ?? 0}
            </div>
          </Card>
        </Col>
        <Col xs={12} md={6}>
          <Card size="small" loading={isLoading}>
            <Text type="secondary" style={{ fontSize: 11, letterSpacing: "0.08em" }}>
              {locale === "ko" ? "만료 임박 (7일)" : "EXPIRING (7d)"}
            </Text>
            <div
              style={{
                fontSize: 32,
                fontWeight: 700,
                fontVariantNumeric: "tabular-nums",
                color: (summary?.expiring_soon ?? 0) > 0 ? "var(--severity-high)" : undefined,
              }}
            >
              {summary?.expiring_soon ?? 0}
            </div>
          </Card>
        </Col>
      </Row>

      <Row gutter={[12, 12]}>
        <Col xs={24} md={12}>
          <Card
            title={locale === "ko" ? "내 자산" : "My Assets"}
            extra={<Link to="/assets">{locale === "ko" ? "전체" : "All"}</Link>}
            style={{ marginBottom: 12 }}
          >
            {(data?.my_assets?.length ?? 0) === 0 ? (
              <Empty
                description={
                  locale === "ko" ? "owner=내 이메일인 자산이 없습니다" : "No assets owned by you"
                }
              />
            ) : (
              <List
                size="small"
                dataSource={data?.my_assets ?? []}
                renderItem={(a) => (
                  <List.Item>
                    <Space style={{ width: "100%", justifyContent: "space-between" }}>
                      <Space>
                        <Text strong>{a.name}</Text>
                        <Tag>{a.asset_type}</Tag>
                        {a.environment && <Tag color="blue">{a.environment}</Tag>}
                      </Space>
                      {a.open_findings_count > 0 && (
                        <Tag color="orange">
                          {a.open_findings_count} {locale === "ko" ? "미해결" : "open"}
                        </Tag>
                      )}
                    </Space>
                  </List.Item>
                )}
              />
            )}
          </Card>
        </Col>

        <Col xs={24} md={12}>
          <Card
            title={locale === "ko" ? "최근 발견사항" : "Recent Findings"}
            extra={<Link to="/findings">{locale === "ko" ? "전체" : "All"}</Link>}
            style={{ marginBottom: 12 }}
          >
            {(data?.recent_findings?.length ?? 0) === 0 ? (
              <Empty description={locale === "ko" ? "조용한 하루입니다" : "Quiet day"} />
            ) : (
              <List
                size="small"
                dataSource={data?.recent_findings ?? []}
                renderItem={(f) => (
                  <List.Item>
                    <Space>
                      <Tag color={SEVERITY_COLOR[f.severity]}>{f.severity}</Tag>
                      <Text ellipsis style={{ maxWidth: 300 }}>
                        {f.title}
                      </Text>
                    </Space>
                  </List.Item>
                )}
              />
            )}
          </Card>
        </Col>

        <Col xs={24} md={12}>
          <Card
            title={locale === "ko" ? "만료 임박 권한" : "Expiring Permissions"}
            extra={<Link to="/access-center">{locale === "ko" ? "갱신 요청" : "Renew"}</Link>}
          >
            {(data?.expiring_soon?.length ?? 0) === 0 ? (
              <Empty description={locale === "ko" ? "임박한 만료 없음" : "Nothing expiring soon"} />
            ) : (
              <List
                size="small"
                dataSource={data?.expiring_soon ?? []}
                renderItem={(p) => (
                  <List.Item>
                    <Space style={{ width: "100%", justifyContent: "space-between" }}>
                      <Text>{p.permission_name}</Text>
                      <Tag color={p.days_left !== null && p.days_left <= 2 ? "red" : "orange"}>
                        {p.days_left !== null
                          ? `${p.days_left}${locale === "ko" ? "일 남음" : "d left"}`
                          : "—"}
                      </Tag>
                    </Space>
                  </List.Item>
                )}
              />
            )}
          </Card>
        </Col>

        <Col xs={24} md={12}>
          <Card
            title={locale === "ko" ? "내 권한 요청" : "My Access Requests"}
            extra={<Link to="/access-center">{locale === "ko" ? "센터" : "Center"}</Link>}
          >
            {(data?.my_requests?.length ?? 0) === 0 ? (
              <Empty description={locale === "ko" ? "권한 요청 없음" : "No requests"} />
            ) : (
              <List
                size="small"
                dataSource={data?.my_requests?.slice(0, 5) ?? []}
                renderItem={(r) => (
                  <List.Item>
                    <Space>
                      <Tag
                        color={
                          r.status === "approved" || r.status === "granted"
                            ? "green"
                            : r.status === "denied"
                              ? "red"
                              : r.status === "pending"
                                ? "blue"
                                : "default"
                        }
                      >
                        {r.status}
                      </Tag>
                      <Text>{r.permission_name}</Text>
                    </Space>
                  </List.Item>
                )}
              />
            )}
          </Card>
        </Col>
      </Row>
    </div>
  );
}
