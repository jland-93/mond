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
            <FirstTimeEnroll
              busy={busy}
              onPasskey={enrollPasskey}
              locale={locale}
              after={after}
              setBusy={setBusy}
            />
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


// ── 미등록 사용자 — 패스키 + TOTP 양쪽 인라인 등록 ─────────────
// WebAuthn은 HTTPS / localhost에서만 동작하므로, 사내 IP에서 띄운 경우
// 패스키가 실패할 수 있다. TOTP는 어디서든 동작 → 안전한 폴백.
function FirstTimeEnroll({
  busy, onPasskey, locale, after, setBusy,
}: {
  busy: boolean;
  onPasskey: () => Promise<void>;
  locale: "ko" | "en";
  after: () => Promise<void>;
  setBusy: (b: boolean) => void;
}) {
  const [totpData, setTotpData] = useState<{ secret: string; qr: string } | null>(null);
  const [totpCode, setTotpCode] = useState("");

  const startTotp = async () => {
    setBusy(true);
    try {
      const r = await mfaApi.totpSetup();
      setTotpData({ secret: r.secret, qr: r.qr_png_base64 });
    } catch (e) {
      const err = e as Error & { response?: { data?: { detail?: string } } };
      message.error(err.response?.data?.detail ?? err.message);
    } finally {
      setBusy(false);
    }
  };

  const verifyTotp = async () => {
    setBusy(true);
    try {
      await mfaApi.totpVerify(totpCode);
      // 등록 직후 즉시 challenge로 통과
      await mfaApi.totpChallenge(totpCode);
      message.success(locale === "ko" ? "MFA 등록 + 인증 완료" : "Enrolled and verified");
      await after();
    } catch (e) {
      const err = e as Error & { response?: { data?: { detail?: string } } };
      message.error(err.response?.data?.detail ?? err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <Space direction="vertical" style={{ width: "100%" }} size="middle">
      <Alert
        type="warning"
        showIcon
        message={
          locale === "ko"
            ? "MFA가 강제되지만 아직 등록된 인증 수단이 없습니다."
            : "MFA is required but no factor is enrolled yet."
        }
        description={
          locale === "ko"
            ? "패스키 또는 TOTP 중 하나를 지금 등록하세요. (패스키는 HTTPS 또는 localhost에서만 동작 — 안 되면 TOTP를 쓰세요)"
            : "Enroll a passkey or TOTP now. (Passkey requires HTTPS or localhost — fall back to TOTP otherwise)"
        }
      />

      <Tabs
        defaultActiveKey="passkey"
        items={[
          {
            key: "passkey",
            label: (
              <Space>
                <KeyOutlined />
                {locale === "ko" ? "패스키" : "Passkey"}
              </Space>
            ),
            children: (
              <Space direction="vertical" style={{ width: "100%" }}>
                <Paragraph type="secondary" style={{ marginBottom: 4 }}>
                  {locale === "ko"
                    ? "디바이스 생체인증(Touch ID · Face ID · Windows Hello) 또는 YubiKey를 사용합니다."
                    : "Use device biometrics or a security key."}
                </Paragraph>
                <Button
                  type="primary"
                  icon={<KeyOutlined />}
                  block
                  size="large"
                  loading={busy}
                  onClick={onPasskey}
                >
                  {locale === "ko" ? "지금 패스키 등록" : "Enroll passkey now"}
                </Button>
              </Space>
            ),
          },
          {
            key: "totp",
            label: (
              <Space>
                <MobileOutlined />
                {locale === "ko" ? "TOTP" : "TOTP"}
              </Space>
            ),
            children: (
              <Space direction="vertical" style={{ width: "100%" }}>
                <Paragraph type="secondary" style={{ marginBottom: 4 }}>
                  {locale === "ko"
                    ? "Google Authenticator · 1Password · Authy 등 어디서나 동작. HTTPS 미설정 환경에서도 안전한 방법입니다."
                    : "Works anywhere with Google Authenticator / 1Password / Authy. Safe for non-HTTPS setups."}
                </Paragraph>
                {!totpData ? (
                  <Button type="primary" block size="large" loading={busy} onClick={startTotp}>
                    {locale === "ko" ? "TOTP QR 받기" : "Get TOTP QR"}
                  </Button>
                ) : (
                  <>
                    <div style={{ textAlign: "center" }}>
                      <img
                        src={`data:image/png;base64,${totpData.qr}`}
                        alt="TOTP QR"
                        style={{
                          width: 180, height: 180,
                          background: "#fff", padding: 8, borderRadius: 8,
                        }}
                      />
                    </div>
                    <Text type="secondary" copyable={{ text: totpData.secret }} style={{ fontFamily: "monospace", fontSize: 11 }}>
                      {locale === "ko" ? "수동 입력 키" : "Manual key"}: {totpData.secret}
                    </Text>
                    <Input
                      size="large"
                      placeholder="123 456"
                      value={totpCode}
                      onChange={(e) => setTotpCode(e.target.value.replace(/\D/g, ""))}
                      maxLength={8}
                      autoFocus
                    />
                    <Button
                      type="primary"
                      block
                      size="large"
                      loading={busy}
                      disabled={!/^\d{6,8}$/.test(totpCode)}
                      onClick={verifyTotp}
                    >
                      {locale === "ko" ? "확인 + 통과" : "Verify and continue"}
                    </Button>
                  </>
                )}
              </Space>
            ),
          },
        ]}
      />
    </Space>
  );
}
