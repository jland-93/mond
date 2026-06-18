/**
 * Admin · Connections — 외부 시스템 연동 통합 관리 (IAM Source · SSO · AI · Webhook).
 *
 * 책임 분리:
 *   - IAMSourceCard      등록된 IAM source 목록 + 동기화
 *   - IAMSourceModal     신규 source 추가 (kind별 form fields 포함)
 *   - SSOCard            SSO 모드 / 활성 IdP / .env 힌트
 *   - AIProvidersCard    AI provider 4종 등록 · 활성화 · 테스트
 *   - WebhookCard        GitHub webhook 안내
 */

import { Typography } from "antd";
import { useState } from "react";

import { useI18n } from "@/i18n";

import AIProvidersCard from "./connections/AIProvidersCard";
import IAMSourceCard from "./connections/IAMSourceCard";
import IAMSourceModal from "./connections/IAMSourceModal";
import SSOCard from "./connections/SSOCard";
import WebhookCard from "./connections/WebhookCard";

const { Title, Paragraph } = Typography;

export default function AdminConnections() {
  const { t } = useI18n();
  const [modalOpen, setModalOpen] = useState(false);

  return (
    <div>
      <Title level={2} style={{ marginBottom: 8 }}>
        {t.adminArea.connectionsTitle}
      </Title>
      <Paragraph type="secondary">{t.adminArea.connectionsDesc}</Paragraph>

      <IAMSourceCard onAdd={() => setModalOpen(true)} />
      <SSOCard />
      <AIProvidersCard />
      <WebhookCard />

      <IAMSourceModal open={modalOpen} onClose={() => setModalOpen(false)} />
    </div>
  );
}
