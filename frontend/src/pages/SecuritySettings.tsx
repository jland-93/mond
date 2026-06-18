/**
 * 보안 설정 — 패스키 · TOTP · 백업 코드 · personal webhook 토큰 · 역할 변경 요청.
 *
 * 모든 카드가 자체 API query를 가지지만 TanStack Query가 같은 key는 dedupe하므로
 * 네트워크 호출은 카드 수 × 1이 아니라 unique key 수만큼만 일어난다.
 */

import { useQuery } from "@tanstack/react-query";
import { Alert, Typography } from "antd";

import { useI18n } from "@/i18n";
import { mfaApi } from "@/lib/mfa-api";

import BackupCodesCard from "./security/BackupCodesCard";
import PasskeysCard from "./security/PasskeysCard";
import PersonalWebhookTokensCard from "./security/PersonalWebhookTokensCard";
import RoleChangeRequestCard from "./security/RoleChangeRequestCard";
import TOTPCard from "./security/TOTPCard";

const { Title, Paragraph } = Typography;

export default function SecuritySettings() {
  const { t } = useI18n();
  const { data: status } = useQuery({ queryKey: ["mfa-status"], queryFn: mfaApi.status });

  return (
    <div>
      <Title level={2} style={{ marginBottom: 4 }}>
        {t.security.title}
      </Title>
      <Paragraph type="secondary">{t.security.desc}</Paragraph>

      {status?.required && !status.enrolled && (
        <Alert
          type="warning"
          showIcon
          style={{ marginBottom: 16 }}
          message={t.security.requiredWarning}
        />
      )}

      <PasskeysCard />
      <TOTPCard />
      <BackupCodesCard />

      <PersonalWebhookTokensCard />
      <RoleChangeRequestCard />
    </div>
  );
}
