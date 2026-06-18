/**
 * 🌙 Login — 로그인 옵션 + Dev login + SSO 진입
 */

import { LoginOutlined, SafetyOutlined } from "@ant-design/icons";
import { useQuery } from "@tanstack/react-query";
import { Alert, Button, Card, Divider, Form, Input, Space, Typography, message } from "antd";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { useAuth } from "@/auth/AuthContext";
import { useI18n } from "@/i18n";
import { authApi } from "@/lib/auth-api";

const { Title, Paragraph, Text } = Typography;

export default function Login() {
  const { t, locale } = useI18n();
  const { refresh } = useAuth();
  const navigate = useNavigate();
  const [busy, setBusy] = useState(false);

  const { data } = useQuery({ queryKey: ["auth-providers"], queryFn: authApi.providers });

  const onDevLogin = async (values: { email: string; name?: string }) => {
    setBusy(true);
    try {
      const me = await authApi.devLogin(values.email, values.name);
      await refresh();
      message.success(t.auth.welcomeBack);
      // MFA 강제 대상이면 검증 단계로
      if (me.mfa_required && !me.mfa_verified) navigate("/mfa");
      else navigate("/");
    } catch (err) {
      const e = err as Error & { response?: { data?: { detail?: string } } };
      message.error(e.response?.data?.detail ?? e.message);
    } finally {
      setBusy(false);
    }
  };

  const ssoUrl = (name: string) =>
    `${import.meta.env.VITE_API_URL ?? "http://localhost:8000"}/api/v1/auth/login/${name}`;

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: 24,
      }}
    >
      <Card style={{ width: "100%", maxWidth: 480 }} bordered={false}>
        <Space direction="vertical" style={{ width: "100%" }} size="middle">
          <div style={{ textAlign: "center" }}>
            <img
              src="/logo.png"
              alt="Mond"
              width={72}
              height={72}
              style={{
                borderRadius: 16,
                filter: "drop-shadow(0 0 18px rgba(124,140,255,0.6))",
              }}
            />
            <Title level={2} style={{ marginBottom: 4, marginTop: 12 }}>
              Mond
            </Title>
            <Paragraph type="secondary">{t.appTagline}</Paragraph>
          </div>

          {(data?.providers?.length ?? 0) > 0 && (
            <>
              <Title level={5} style={{ marginBottom: 8 }}>
                {t.auth.ssoLogin}
              </Title>
              <Space direction="vertical" style={{ width: "100%" }}>
                {data!.providers.map((p) => (
                  <Button
                    key={p.name}
                    type="primary"
                    size="large"
                    block
                    icon={<SafetyOutlined />}
                    href={ssoUrl(p.name)}
                  >
                    {locale === "ko" ? `${p.display}로 로그인` : `Continue with ${p.display}`}
                  </Button>
                ))}
              </Space>
              {data?.dev_login_enabled && <Divider plain>{t.auth.or}</Divider>}
            </>
          )}

          {data?.dev_login_enabled && (
            <>
              <Alert
                type="warning"
                showIcon
                message={t.auth.devModeTitle}
                description={t.auth.devModeDesc}
              />
              <Form layout="vertical" onFinish={onDevLogin}>
                <Form.Item
                  label={t.auth.email}
                  name="email"
                  rules={[{ required: true, type: "email" }]}
                >
                  <Input placeholder="alice@example.com" autoFocus />
                </Form.Item>
                <Form.Item label={t.auth.displayName} name="name">
                  <Input placeholder={locale === "ko" ? "예: Alice Kim" : "e.g. Alice Kim"} />
                </Form.Item>
                <Button
                  type="primary"
                  htmlType="submit"
                  loading={busy}
                  block
                  icon={<LoginOutlined />}
                >
                  {t.auth.devLoginBtn}
                </Button>
              </Form>
              <Text type="secondary" style={{ fontSize: 12 }}>
                {t.auth.firstUserHint}
              </Text>
            </>
          )}
        </Space>
      </Card>
    </div>
  );
}
