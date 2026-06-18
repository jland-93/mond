/**
 * 🌙 MFA Challenge — 1차 인증 직후 강제되는 2차 인증 단계.
 *
 * 가능한 옵션:
 *   1) 패스키(WebAuthn) — 등록된 키가 있으면 1순위
 *   2) TOTP 코드
 *   3) 백업 코드
 *
 * MFA 미등록 사용자가 강제 대상이면, 첫 등록 안내(SecuritySettings로 이동).
 */

import { KeyOutlined, MobileOutlined, SafetyOutlined } from "@ant-design/icons";
import { startAuthentication, startRegistration } from "@simplewebauthn/browser";
import { useQuery } from "@tanstack/react-query";
import { Alert, Button, Card, Divider, Input, Space, Tabs, Typography, message } from "antd";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { useAuth } from "@/auth/AuthContext";
import { useI18n } from "@/i18n";
import { mfaApi } from "@/lib/mfa-api";

const { Title, Paragraph, Text } = Typography;

export default function MfaChallenge() {
  const { t, locale } = useI18n();
  const { user, refresh, logout } = useAuth();
  const navigate = useNavigate();
  const [busy, setBusy] = useState(false);
  const [totp, setTotp] = useState("");
  const [backup, setBackup] = useState("");

  const { data: status } = useQuery({ queryKey: ["mfa-status"], queryFn: mfaApi.status });

  const enrolled = !!status?.enrolled;

  const after = async () => {
    await refresh();
    navigate("/");
  };

  const onPasskey = async () => {
    setBusy(true);
    try {
      const options = await mfaApi.passkeyLoginBegin();
      const credential = await startAuthentication({ optionsJSON: options as never });
      await mfaApi.passkeyLoginComplete(credential as unknown as Record<string, unknown>);
      message.success(t.security.mfaPassed);
      await after();
    } catch (e) {
      const err = e as Error & { response?: { data?: { detail?: string } } };
      message.error(err.response?.data?.detail ?? err.message);
    } finally {
      setBusy(false);
    }
  };

  const onTotp = async () => {
    setBusy(true);
    try {
      await mfaApi.totpChallenge(totp);
      message.success(t.security.mfaPassed);
      await after();
    } catch (e) {
      const err = e as Error & { response?: { data?: { detail?: string } } };
      message.error(err.response?.data?.detail ?? err.message);
    } finally {
      setBusy(false);
    }
  };

  const onBackup = async () => {
    setBusy(true);
    try {
      await mfaApi.backupCodeChallenge(backup);
      message.success(t.security.mfaPassed);
      await after();
    } catch (e) {
      const err = e as Error & { response?: { data?: { detail?: string } } };
      message.error(err.response?.data?.detail ?? err.message);
    } finally {
      setBusy(false);
    }
  };

  // 강제 대상이지만 미등록 → 첫 등록 안내
  const enrollPasskey = async () => {
    setBusy(true);
    try {
      const options = await mfaApi.passkeyRegisterBegin();
      const credential = await startRegistration({ optionsJSON: options as never });
      await mfaApi.passkeyRegisterComplete(
        locale === "ko" ? "내 패스키" : "My Passkey",
        credential as unknown as Record<string, unknown>,
      );
      message.success(locale === "ko" ? "패스키 등록 완료 — 이제 로그인하세요" : "Passkey enrolled — sign in now");
      // 등록 후 즉시 로그인 챌린지로 연결
      const auth = await mfaApi.passkeyLoginBegin();
      const cred2 = await startAuthentication({ optionsJSON: auth as never });
      await mfaApi.passkeyLoginComplete(cred2 as unknown as Record<string, unknown>);
      await after();
    } catch (e) {
      const err = e as Error & { response?: { data?: { detail?: string } } };
      message.error(err.response?.data?.detail ?? err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", padding: 24 }}>
      <Card style={{ width: "100%", maxWidth: 480 }} bordered={false}>
        <Space direction="vertical" style={{ width: "100%" }} size="middle">
          <div style={{ textAlign: "center" }}>
            <SafetyOutlined style={{ fontSize: 42, color: "var(--mond-primary)" }} />
            <Title level={3} style={{ marginTop: 8 }}>
              {t.security.mfaTitle}
            </Title>
            <Paragraph type="secondary">
              {user?.email} — {t.security.mfaDesc}
            </Paragraph>
          </div>

          {!enrolled ? (
            <>
              <Alert
                type="warning"
                showIcon
                message={t.security.notEnrolled}
                description={t.security.notEnrolledDesc}
              />
              <Button
                type="primary"
                icon={<KeyOutlined />}
                block
                size="large"
                loading={busy}
                onClick={enrollPasskey}
              >
                {t.security.enrollPasskeyNow}
              </Button>
              <Text type="secondary" style={{ fontSize: 12 }}>
                {t.security.orVisitSettings}
              </Text>
              <Button block onClick={() => navigate("/security")}>{t.security.openSettings}</Button>
            </>
          ) : (
            <Tabs
              defaultActiveKey={(status?.passkeys.length ?? 0) > 0 ? "passkey" : "totp"}
              items={[
                {
                  key: "passkey",
                  label: (
                    <Space>
                      <KeyOutlined />
                      {t.security.passkey}
                    </Space>
                  ),
                  disabled: (status?.passkeys.length ?? 0) === 0,
                  children: (
                    <Space direction="vertical" style={{ width: "100%" }}>
                      <Paragraph type="secondary">{t.security.passkeyTabDesc}</Paragraph>
                      <Button
                        type="primary"
                        icon={<KeyOutlined />}
                        size="large"
                        block
                        loading={busy}
                        onClick={onPasskey}
                      >
                        {t.security.signInWithPasskey}
                      </Button>
                    </Space>
                  ),
                },
                {
                  key: "totp",
                  label: (
                    <Space>
                      <MobileOutlined />
                      {t.security.totp}
                    </Space>
                  ),
                  disabled: !status?.totp_confirmed,
                  children: (
                    <Space direction="vertical" style={{ width: "100%" }}>
                      <Input
                        size="large"
                        placeholder="123 456"
                        value={totp}
                        onChange={(e) => setTotp(e.target.value.replace(/\D/g, ""))}
                        maxLength={8}
                        autoFocus
                      />
                      <Button
                        type="primary"
                        block
                        size="large"
                        loading={busy}
                        disabled={!/^\d{6,8}$/.test(totp)}
                        onClick={onTotp}
                      >
                        {t.security.verify}
                      </Button>
                    </Space>
                  ),
                },
                {
                  key: "backup",
                  label: t.security.backupCodeTab,
                  disabled: (status?.backup_codes_remaining ?? 0) === 0,
                  children: (
                    <Space direction="vertical" style={{ width: "100%" }}>
                      <Input
                        size="large"
                        placeholder="XXXXXXXX-XXXXXXXX"
                        value={backup}
                        onChange={(e) => setBackup(e.target.value.toUpperCase())}
                      />
                      <Button type="primary" block size="large" loading={busy} onClick={onBackup}>
                        {t.security.verify}
                      </Button>
                    </Space>
                  ),
                },
              ]}
            />
          )}

          <Divider plain style={{ marginTop: 8, marginBottom: 0 }} />
          <Button type="text" block onClick={async () => { await logout(); navigate("/login"); }}>
            {t.auth.logout}
          </Button>
        </Space>
      </Card>
    </div>
  );
}
