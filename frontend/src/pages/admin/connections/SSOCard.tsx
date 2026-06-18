/**
 * SSO Providers 상태 카드 — 현재 모드 / 활성 IdP / .env 설정 힌트.
 */

import { SafetyOutlined } from "@ant-design/icons";
import { useQuery } from "@tanstack/react-query";
import { Alert, Card, Col, Row, Space, Tag, Typography } from "antd";

import { useI18n } from "@/i18n";
import { authApi } from "@/lib/auth-api";

const { Paragraph, Text } = Typography;

export default function SSOCard() {
  const { t, locale } = useI18n();
  const { data: providers } = useQuery({ queryKey: ["auth-providers"], queryFn: authApi.providers });

  return (
    <Card
      title={
        <Space>
          <SafetyOutlined />
          <span>{t.adminArea.ssoTitle}</span>
        </Space>
      }
      style={{ marginBottom: 16 }}
    >
      <Paragraph type="secondary">{t.adminArea.ssoDesc}</Paragraph>
      <Row gutter={[12, 12]}>
        <Col xs={24} md={12}>
          <Card type="inner" title={t.adminArea.ssoMode}>
            <Tag color={providers?.mode === "sso" ? "green" : "orange"}>
              {providers?.mode ?? "—"}
            </Tag>
            <Text type="secondary" style={{ marginLeft: 8 }}>
              {providers?.dev_login_enabled
                ? locale === "ko"
                  ? "Dev Login 활성"
                  : "Dev login enabled"
                : locale === "ko"
                  ? "Dev Login 비활성"
                  : "Dev login disabled"}
            </Text>
          </Card>
        </Col>
        <Col xs={24} md={12}>
          <Card type="inner" title={t.adminArea.ssoActive}>
            {(providers?.providers ?? []).length === 0 ? (
              <Text type="secondary">
                {locale === "ko"
                  ? "활성 IdP 없음 — .env에 SSO_PROVIDERS와 해당 ENV를 설정하고 백엔드를 재시작하세요."
                  : "No IdP configured — set SSO_PROVIDERS in .env and restart the backend."}
              </Text>
            ) : (
              <Space wrap>
                {providers!.providers.map((p) => (
                  <Tag key={p.name} color="geekblue">
                    {p.display}
                  </Tag>
                ))}
              </Space>
            )}
          </Card>
        </Col>
      </Row>
      <Alert
        style={{ marginTop: 12 }}
        type="info"
        showIcon
        message={t.adminArea.ssoEnvHint}
        description={
          <pre style={{ marginBottom: 0, fontSize: 12 }}>
{`AUTH_MODE=sso
SSO_PROVIDERS=keycloak,okta
SSO_KEYCLOAK_ISSUER=https://kc.example.com/realms/main
SSO_KEYCLOAK_CLIENT_ID=mond
SSO_KEYCLOAK_CLIENT_SECRET=...
SSO_ADMIN_EMAILS=security-lead@example.com`}
          </pre>
        }
      />
    </Card>
  );
}
