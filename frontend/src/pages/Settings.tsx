/**
 * Settings — 시스템 통합 상태 + 환경 정보.
 *
 * admin이 한 화면에서 backend / DB / Redis / AI provider / OPA / scanner
 * 어댑터의 가용성을 점검. 각 카드는 ok/warn/down 3-state 색 점.
 */

import {
  CheckCircleFilled,
  CloseCircleFilled,
  ExclamationCircleFilled,
} from "@ant-design/icons";
import { useQuery } from "@tanstack/react-query";
import { Alert, Card, Col, Row, Space, Tag, Typography } from "antd";
import type React from "react";

import { useI18n } from "@/i18n";
import { api } from "@/lib/api";

const { Title, Paragraph, Text } = Typography;

interface Health {
  status: string;
  db: boolean;
  version: string;
  environment: string;
  ai_enabled: boolean;
}

interface AIIntegration {
  enabled: boolean;
  provider: string | null;
  model: string | null;
}

interface OpaIntegration {
  available: boolean;
  binary: string | null;
}

interface ScannerIntegrations {
  scanners: Array<{ name: string; asset_types: string[] }>;
}

type StateLevel = "ok" | "warn" | "down";

function StatusDot({ level }: { level: StateLevel }) {
  if (level === "ok")
    return <CheckCircleFilled style={{ color: "var(--severity-low, #4ad28d)" }} />;
  if (level === "warn")
    return <ExclamationCircleFilled style={{ color: "var(--severity-medium, #eab308)" }} />;
  return <CloseCircleFilled style={{ color: "var(--severity-high, #f29142)" }} />;
}

function StatusCard({
  title,
  level,
  primary,
  secondary,
}: {
  title: string;
  level: StateLevel;
  primary: React.ReactNode;
  secondary?: React.ReactNode;
}) {
  return (
    <Card style={{ height: "100%" }} styles={{ body: { paddingBlock: 16 } }}>
      <Space direction="vertical" size={4} style={{ width: "100%" }}>
        <Space size={6}>
          <StatusDot level={level} />
          <Text type="secondary" style={{ fontSize: 11, letterSpacing: "0.06em" }}>
            {title.toUpperCase()}
          </Text>
        </Space>
        <div style={{ fontSize: 16, fontWeight: 600 }}>{primary}</div>
        {secondary && (
          <Text type="secondary" style={{ fontSize: 12 }}>
            {secondary}
          </Text>
        )}
      </Space>
    </Card>
  );
}

export default function Settings() {
  const { t, locale } = useI18n();
  const { data: health } = useQuery({
    queryKey: ["health"],
    queryFn: async () => (await api.get<Health>("/health")).data,
    refetchInterval: 15_000,
  });
  const { data: aiInt } = useQuery({
    queryKey: ["integrations-ai"],
    queryFn: async () => {
      try {
        return (await api.get<AIIntegration>("/integrations/ai")).data;
      } catch {
        return { enabled: false, provider: null, model: null };
      }
    },
    staleTime: 30_000,
  });
  const { data: opaInt } = useQuery({
    queryKey: ["integrations-opa"],
    queryFn: async () => {
      try {
        return (await api.get<OpaIntegration>("/integrations/opa")).data;
      } catch {
        return { available: false, binary: null };
      }
    },
    staleTime: 60_000,
  });
  const { data: scannerInt } = useQuery({
    queryKey: ["integrations-scanners"],
    queryFn: async () => {
      try {
        return (await api.get<ScannerIntegrations>("/integrations/scanners")).data;
      } catch {
        return { scanners: [] };
      }
    },
    staleTime: 60_000,
  });

  const backendLevel: StateLevel = health?.status === "ok" ? "ok" : "warn";
  const dbLevel: StateLevel = health?.db ? "ok" : "down";
  const aiLevel: StateLevel = aiInt?.enabled ? "ok" : "warn";
  const opaLevel: StateLevel = opaInt?.available ? "ok" : "warn";

  return (
    <div>
      <Title level={2} style={{ marginBottom: 4 }}>
        {t.settings.title}
      </Title>
      <Paragraph type="secondary" style={{ marginBottom: 16 }}>
        {locale === "ko"
          ? "백엔드·데이터베이스·AI provider·OPA·스캐너 어댑터의 통합 상태를 한 화면에. ADMIN 화면이 아니므로 모든 로그인 사용자가 헬스 정보를 볼 수 있습니다."
          : "Backend / DB / AI provider / OPA / scanners — integration health at a glance."}
      </Paragraph>

      <Row gutter={[12, 12]} style={{ marginBottom: 12 }}>
        <Col xs={24} md={12} xl={6}>
          <StatusCard
            title={t.settings.serviceStatus}
            level={backendLevel}
            primary={
              <Space size={6}>
                <span>{health?.status ?? "—"}</span>
                {health?.version && (
                  <Tag style={{ marginInlineEnd: 0, fontSize: 11 }}>v{health.version}</Tag>
                )}
              </Space>
            }
            secondary={
              health?.environment
                ? `${t.settings.environment}: ${health.environment}`
                : undefined
            }
          />
        </Col>
        <Col xs={24} md={12} xl={6}>
          <StatusCard
            title={t.settings.db}
            level={dbLevel}
            primary={health?.db ? (locale === "ko" ? "연결됨" : "Connected") : (locale === "ko" ? "연결 끊김" : "Down")}
            secondary="PostgreSQL · asyncpg"
          />
        </Col>
        <Col xs={24} md={12} xl={6}>
          <StatusCard
            title={t.settings.ai}
            level={aiLevel}
            primary={
              aiInt?.enabled ? (
                <Space size={6}>
                  <span>{aiInt.provider ?? "AI"}</span>
                  {aiInt.model && (
                    <Tag style={{ marginInlineEnd: 0, fontSize: 11 }}>{aiInt.model}</Tag>
                  )}
                </Space>
              ) : locale === "ko" ? (
                "기본 규칙 모드"
              ) : (
                "Rule-based fallback"
              )
            }
            secondary={
              aiInt?.enabled
                ? locale === "ko"
                  ? "외부 LLM provider 활성"
                  : "External LLM active"
                : locale === "ko"
                  ? "AI provider 미설정 — 휴리스틱 동작"
                  : "No AI provider — heuristic mode"
            }
          />
        </Col>
        <Col xs={24} md={12} xl={6}>
          <StatusCard
            title="OPA"
            level={opaLevel}
            primary={
              opaInt?.available
                ? locale === "ko"
                  ? "사용 가능"
                  : "Available"
                : locale === "ko"
                  ? "미설치"
                  : "Not installed"
            }
            secondary={
              opaInt?.available
                ? opaInt.binary ?? undefined
                : locale === "ko"
                  ? "Rego 정책 평가는 builtin engine만 동작"
                  : "Builtin engine only"
            }
          />
        </Col>
      </Row>

      {/* 스캐너 어댑터 */}
      <Card title={locale === "ko" ? "스캐너 어댑터" : "Scanner adapters"} style={{ marginBottom: 12 }}>
        {(scannerInt?.scanners ?? []).length === 0 ? (
          <Text type="secondary">
            {locale === "ko" ? "등록된 스캐너가 없습니다." : "No scanners registered."}
          </Text>
        ) : (
          <Space wrap size={[6, 6]}>
            {scannerInt!.scanners.map((s) => (
              <Tag key={s.name} color="cyan" style={{ marginInlineEnd: 0 }}>
                {s.name}
                <Text type="secondary" style={{ fontSize: 11, marginInlineStart: 6 }}>
                  · {s.asset_types.join(" · ")}
                </Text>
              </Tag>
            ))}
          </Space>
        )}
      </Card>

      <Card title={locale === "ko" ? "언어 · 환경" : "Locale · Environment"}>
        <Space size={12} wrap>
          <Tag>{t.settings.locale}: {locale.toUpperCase()}</Tag>
          <Tag>
            {t.settings.environment}: {health?.environment ?? "—"}
          </Tag>
        </Space>
      </Card>

      {!aiInt?.enabled && (
        <Alert
          type="info"
          showIcon
          style={{ marginTop: 16 }}
          message={
            locale === "ko"
              ? "AI provider 미설정 상태 — 모든 화면이 기본 규칙(휴리스틱)으로 동작합니다. 외부 LLM을 쓰려면 관리자 모드 → 연동 관리 → AI Providers에서 등록하세요."
              : "No AI provider configured — UI falls back to heuristic rules. Add a provider in Admin → Connections."
          }
        />
      )}

      <Paragraph type="secondary" style={{ marginTop: 16, fontSize: 12 }}>
        {t.settings.note}
      </Paragraph>
    </div>
  );
}
