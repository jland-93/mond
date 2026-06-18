/**
 * 🌒 Login — Editorial Dark + Moon Jar Hero
 *
 * 좌측 50% 달항아리 hero + 우측 50% form. AI 디폴트(중앙정렬 카드 + 균일 grid)에서
 * 정확히 반대. Sandoll CompSerif 헤드라인 + 한국적 차분한 톤.
 */

import { LoginOutlined, SafetyOutlined } from "@ant-design/icons";
import { useQuery } from "@tanstack/react-query";
import { Alert, Button, Divider, Form, Input, Space, Typography, message } from "antd";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { useAuth } from "@/auth/AuthContext";
import AIOrbHero from "@/components/AIOrbHero";
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

  const headline =
    locale === "ko"
      ? ["보안을", "AI에 맡기고", "잠은 푹"]
      : ["Hand security", "to your AI.", "Sleep well."];

  const sub =
    locale === "ko"
      ? "AI 셀프서비스 DevSecOps — 스캔·분석·승인·기록까지 한 흐름으로. 직원은 신청만, 나머지는 Mond가."
      : "AI self-service DevSecOps — scan, triage, approve, audit in one flow. Employees just ask; Mond does the rest.";

  const pillars =
    locale === "ko"
      ? [
          { kw: "AI Triage", desc: "발견사항을 Claude가 1차 분석" },
          { kw: "Self-service", desc: "권한·스캔을 직원이 직접 요청" },
          { kw: "Auto-audit", desc: "ISMS-P·PCI DSS·GDPR 자동 매핑" },
        ]
      : [
          { kw: "AI Triage", desc: "Claude grades every finding" },
          { kw: "Self-service", desc: "Employees request access & scans" },
          { kw: "Auto-audit", desc: "ISMS-P · PCI DSS · GDPR mapped" },
        ];

  return (
    <div className="login-shell">
      {/* ── 좌측 hero (50%) — AI Orb + 제품 가치 카피 ─────────────── */}
      <div className="login-hero">
        <div className="login-hero-inner">
          <div className="login-mark">
            <img src="/logo.png" alt="Mond" width={28} height={28} />
            <span style={{ fontWeight: 600, letterSpacing: "-0.01em", fontSize: 17 }}>
              Mond
            </span>
            <span
              style={{
                fontSize: 11,
                color: "var(--accent)",
                background: "color-mix(in oklch, var(--accent) 10%, transparent)",
                border: "1px solid var(--accent-dim)",
                padding: "2px 8px",
                borderRadius: 999,
                marginLeft: 4,
                letterSpacing: "0.04em",
              }}
            >
              AI · DevSecOps
            </span>
          </div>

          <div className="login-orb-wrap">
            <AIOrbHero size={340} />
          </div>

          <div className="login-headline">
            <Title
              level={1}
              style={{
                fontFamily: "var(--font-display)",
                fontSize: 56,
                lineHeight: 1.05,
                margin: 0,
                color: "var(--fg-primary)",
                letterSpacing: "-0.025em",
                fontWeight: 600,
              }}
            >
              {headline[0]}
              <br />
              <span
                style={{
                  background:
                    "linear-gradient(120deg, var(--accent) 10%, oklch(72% 0.16 295) 80%)",
                  WebkitBackgroundClip: "text",
                  WebkitTextFillColor: "transparent",
                  backgroundClip: "text",
                }}
              >
                {headline[1]}
              </span>
              <br />
              {headline[2]}
            </Title>
            <Paragraph
              style={{
                color: "var(--fg-secondary)",
                fontSize: 15,
                marginTop: 18,
                maxWidth: 420,
                lineHeight: 1.6,
              }}
            >
              {sub}
            </Paragraph>
          </div>

          {/* 3 pillars — 제품 가치 명시 */}
          <div className="login-pillars">
            {pillars.map((p) => (
              <div className="login-pillar" key={p.kw}>
                <div className="login-pillar-kw">{p.kw}</div>
                <div className="login-pillar-desc">{p.desc}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── 우측 form (50%) ──────────────────────────────────────── */}
      <div className="login-form">
        <div className="login-form-inner">
          <Space direction="vertical" size={6} style={{ marginBottom: 32 }}>
            <Text style={{ color: "var(--fg-tertiary)", fontSize: 12, letterSpacing: "0.04em" }}>
              {locale === "ko" ? "들어가기" : "SIGN IN"}
            </Text>
            <Title level={3} style={{ margin: 0, color: "var(--fg-primary)", fontWeight: 600 }}>
              {locale === "ko" ? "오늘도 안녕하세요" : "Welcome back"}
            </Title>
          </Space>

          {(data?.providers?.length ?? 0) > 0 && (
            <>
              <Space direction="vertical" style={{ width: "100%" }} size={10}>
                {data!.providers.map((p) => (
                  <Button
                    key={p.name}
                    type="primary"
                    size="large"
                    block
                    icon={<SafetyOutlined />}
                    href={ssoUrl(p.name)}
                    style={{
                      height: 48,
                      borderRadius: 10,
                      fontWeight: 500,
                      background: "var(--accent)",
                      color: "var(--surface-0)",
                      border: "none",
                    }}
                  >
                    {locale === "ko" ? `${p.display}로 들어가기` : `Continue with ${p.display}`}
                  </Button>
                ))}
              </Space>
              {data?.dev_login_enabled && (
                <Divider plain style={{ color: "var(--fg-tertiary)", margin: "24px 0" }}>
                  {locale === "ko" ? "또는" : "or"}
                </Divider>
              )}
            </>
          )}

          {data?.dev_login_enabled && (
            <>
              <Alert
                type="warning"
                showIcon
                style={{
                  marginBottom: 20,
                  background: "color-mix(in oklch, var(--severity-high) 10%, var(--surface-1))",
                  border: "1px solid var(--severity-high-bg)",
                }}
                message={
                  <span style={{ fontWeight: 500 }}>{t.auth.devModeTitle}</span>
                }
                description={
                  <span style={{ fontSize: 12, color: "var(--fg-secondary)" }}>
                    {t.auth.devModeDesc}
                  </span>
                }
              />

              <Form layout="vertical" onFinish={onDevLogin}>
                <Form.Item
                  label={
                    <span style={{ color: "var(--fg-secondary)", fontSize: 12, letterSpacing: "0.03em" }}>
                      {t.auth.email.toUpperCase()}
                    </span>
                  }
                  name="email"
                  rules={[{ required: true, type: "email" }]}
                >
                  <Input
                    placeholder="you@your-corp.com"
                    autoFocus
                    size="large"
                    style={{ height: 48, borderRadius: 10 }}
                  />
                </Form.Item>
                <Form.Item
                  label={
                    <span style={{ color: "var(--fg-secondary)", fontSize: 12, letterSpacing: "0.03em" }}>
                      {t.auth.displayName.toUpperCase()}
                    </span>
                  }
                  name="name"
                >
                  <Input
                    placeholder={locale === "ko" ? "예) 김보안" : "e.g. Jane Doe"}
                    size="large"
                    style={{ height: 48, borderRadius: 10 }}
                  />
                </Form.Item>
                <Button
                  type="primary"
                  htmlType="submit"
                  loading={busy}
                  block
                  size="large"
                  icon={<LoginOutlined />}
                  style={{
                    height: 48,
                    borderRadius: 10,
                    fontWeight: 500,
                    background: "var(--accent)",
                    color: "var(--surface-0)",
                    border: "none",
                  }}
                >
                  {t.auth.devLoginBtn}
                </Button>
              </Form>

              <Text
                type="secondary"
                style={{
                  display: "block",
                  fontSize: 12,
                  marginTop: 20,
                  color: "var(--fg-tertiary)",
                  textAlign: "center",
                }}
              >
                {t.auth.firstUserHint}
              </Text>
            </>
          )}
        </div>
      </div>

      <style>{`
        .login-shell {
          min-height: 100vh;
          display: grid;
          grid-template-columns: 1.05fr 1fr;
          background: var(--surface-0);
          color: var(--fg-primary);
        }
        @media (max-width: 960px) {
          .login-shell { grid-template-columns: 1fr; }
          .login-hero { display: none; }
        }
        .login-hero {
          position: relative;
          padding: 48px 56px 40px;
          background:
            radial-gradient(ellipse at 20% 0%, oklch(72% 0.10 200 / 0.18), transparent 55%),
            radial-gradient(ellipse at 100% 30%, oklch(62% 0.14 295 / 0.16), transparent 55%),
            radial-gradient(ellipse at 50% 100%, oklch(54% 0.08 250 / 0.10), transparent 60%),
            var(--surface-0);
          border-right: 1px solid var(--border);
          overflow: hidden;
        }
        .login-hero::after {
          content: "";
          position: absolute; inset: 0;
          background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='220' height='220'><filter id='n'><feTurbulence baseFrequency='0.9' numOctaves='2'/></filter><rect width='100%' height='100%' filter='url(%23n)' opacity='0.025'/></svg>");
          pointer-events: none;
        }
        .login-hero-inner {
          position: relative;
          height: 100%;
          display: flex;
          flex-direction: column;
          z-index: 1;
        }
        .login-mark {
          display: flex; align-items: center; gap: 10px;
          font-size: 17px;
        }
        .login-orb-wrap {
          flex: 1;
          display: flex; align-items: center; justify-content: center;
          margin: -12px 0 -24px;
        }
        .login-headline { margin-top: 8px; }
        .login-pillars {
          margin-top: 32px;
          padding-top: 24px;
          border-top: 1px solid var(--border);
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 16px;
          max-width: 520px;
        }
        .login-pillar-kw {
          font-size: 11px;
          font-weight: 600;
          letter-spacing: 0.06em;
          text-transform: uppercase;
          color: var(--accent);
        }
        .login-pillar-desc {
          font-size: 12px;
          color: var(--fg-tertiary);
          margin-top: 6px;
          line-height: 1.5;
        }
        .login-form {
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 48px;
          background:
            radial-gradient(ellipse at 100% 0%, oklch(82% 0.06 180 / 0.04), transparent 50%),
            var(--surface-0);
        }
        .login-form-inner {
          width: 100%;
          max-width: 380px;
        }
      `}</style>
    </div>
  );
}
