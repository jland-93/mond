/**
 * Dashboard 상단 '다음 단계' 카드.
 *
 * 처음 띄운 사용자가 'docker compose up 후 뭘 하지?'에서 막히지 않도록
 * 페르소나(admin / employee)별 다음 액션을 명시. 완료된 단계는 자동 hide.
 * localStorage 'mond-next-steps-dismissed=1'이면 영구 hide.
 *
 * 단계 판정은 가벼운 GET — Dashboard overview · IAM sources · /integrations/ai
 * 만으로 끝남.
 */

import { CheckCircleFilled, CloseOutlined, RightOutlined } from "@ant-design/icons";
import { useQuery } from "@tanstack/react-query";
import { Button, Card, Progress, Space, Typography } from "antd";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { useAuth } from "@/auth/AuthContext";
import { useI18n } from "@/i18n";
import { api, type DashboardOverview } from "@/lib/api";
import { iamApi } from "@/lib/iam-api";

const { Text } = Typography;

const DISMISS_KEY = "mond-next-steps-dismissed";

interface Step {
  id: string;
  ko: string;
  en: string;
  href: string;
  done: boolean;
}

export default function NextSteps({ overview }: { overview: DashboardOverview | undefined }) {
  const { locale } = useI18n();
  const { user } = useAuth();
  const [dismissed, setDismissed] = useState<boolean>(false);

  useEffect(() => {
    setDismissed(typeof window !== "undefined" && window.localStorage.getItem(DISMISS_KEY) === "1");
  }, []);

  const { data: sources } = useQuery({
    queryKey: ["iam-sources"],
    queryFn: iamApi.listSources,
    staleTime: 60_000,
  });

  const { data: aiStatus } = useQuery({
    queryKey: ["integrations-ai"],
    queryFn: async () => {
      try {
        const { data } = await api.get<{ enabled: boolean }>("/integrations/ai");
        return data;
      } catch {
        return { enabled: false };
      }
    },
    staleTime: 60_000,
  });

  if (dismissed || !user) return null;

  const hasAssets = (overview?.asset_total ?? 0) > 0;
  const hasScans = (overview?.scans_last_7d ?? 0) > 0;
  const hasIamSource = (sources ?? []).length > 0;
  const aiEnabled = !!aiStatus?.enabled;
  const mfaOk = !!user.mfa_verified || !user.mfa_required;

  const isAdmin = user.role === "admin";

  const steps: Step[] = isAdmin
    ? [
        {
          id: "iam",
          ko: "IAM 소스 연결 (AWS · GCP · Azure · K8s · LDAP)",
          en: "Connect an IAM source",
          href: "/admin/connections",
          done: hasIamSource,
        },
        {
          id: "assets",
          ko: "자산 등록 — 회사 repo · 컨테이너 · URL",
          en: "Register assets",
          href: "/assets",
          done: hasAssets,
        },
        {
          id: "scan",
          ko: "첫 스캔 실행",
          en: "Run your first scan",
          href: "/scans",
          done: hasScans,
        },
        {
          id: "ai",
          ko: "AI provider 등록 (Anthropic · OpenAI · Bedrock · Ollama)",
          en: "Enable an AI provider",
          href: "/admin/connections",
          done: aiEnabled,
        },
        {
          id: "mfa",
          ko: "본인 MFA 등록 (패스키 / TOTP)",
          en: "Enroll MFA",
          href: "/security",
          done: mfaOk,
        },
      ]
    : [
        {
          id: "mfa",
          ko: "본인 MFA 등록 (패스키 / TOTP)",
          en: "Enroll MFA",
          href: "/security",
          done: mfaOk,
        },
        {
          id: "owner",
          ko: "내가 담당하는 자산 표시",
          en: "Claim assets you own",
          href: "/assets",
          done: false, // employee에게는 권장 — 영구 표시
        },
        {
          id: "request",
          ko: "필요한 권한 요청",
          en: "Request access",
          href: "/access-center",
          done: false,
        },
      ];

  const total = steps.length;
  const doneCount = steps.filter((s) => s.done).length;
  const remaining = steps.filter((s) => !s.done);

  // 모두 완료 또는 표시할 단계가 없으면 자동 hide
  if (remaining.length === 0) return null;

  return (
    <Card
      style={{ marginBottom: 16, borderColor: "var(--mond-source-ai, #6a4cff)" }}
      styles={{ body: { paddingBlock: 14 } }}
    >
      <Space direction="vertical" size={8} style={{ width: "100%" }}>
        <Space style={{ width: "100%", justifyContent: "space-between" }}>
          <Space size={8}>
            <Text strong style={{ fontSize: 14 }}>
              {locale === "ko" ? "다음 단계" : "Next steps"}
            </Text>
            <Text type="secondary" style={{ fontSize: 12 }}>
              {doneCount}/{total} {locale === "ko" ? "완료" : "done"}
            </Text>
          </Space>
          <Button
            size="small"
            type="text"
            icon={<CloseOutlined />}
            onClick={() => {
              window.localStorage.setItem(DISMISS_KEY, "1");
              setDismissed(true);
            }}
          >
            {locale === "ko" ? "닫기" : "Dismiss"}
          </Button>
        </Space>

        <Progress
          percent={total > 0 ? Math.round((doneCount / total) * 100) : 0}
          showInfo={false}
          strokeColor="var(--mond-source-ai, #6a4cff)"
          style={{ marginBottom: 0 }}
        />

        <Space direction="vertical" size={4} style={{ width: "100%" }}>
          {steps.map((s) => {
            const label = locale === "ko" ? s.ko : s.en;
            if (s.done) {
              return (
                <Space key={s.id} size={6}>
                  <CheckCircleFilled style={{ color: "var(--severity-low, #4ad28d)" }} />
                  <Text style={{ color: "var(--mond-text-dim)", textDecoration: "line-through" }}>
                    {label}
                  </Text>
                </Space>
              );
            }
            return (
              <Space key={s.id} size={6} style={{ width: "100%" }}>
                <span
                  style={{
                    display: "inline-block",
                    width: 14,
                    height: 14,
                    borderRadius: "50%",
                    border: "1.5px solid var(--mond-text-dim)",
                  }}
                />
                <Link to={s.href} style={{ flex: 1 }}>
                  <Space size={4}>
                    <Text strong>{label}</Text>
                    <RightOutlined style={{ fontSize: 11, color: "var(--mond-text-dim)" }} />
                  </Space>
                </Link>
              </Space>
            );
          })}
        </Space>
      </Space>
    </Card>
  );
}
