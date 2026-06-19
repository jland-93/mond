import { ClockCircleOutlined, SendOutlined } from "@ant-design/icons";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Alert, Button, Card, Space, Tag, Typography, message } from "antd";

import { useI18n } from "@/i18n";
import { api } from "@/lib/api";

const { Paragraph, Text } = Typography;

interface DigestData {
  period: { since: string; until: string };
  findings: { total: number; by_severity: Record<string, number> };
  scans: { total: number; failed: number };
  access_requests: { total: number; granted: number; denied: number; pending: number };
}

interface PreviewResp {
  digest: DigestData;
  slack_message: { text: string };
}

interface SendResp {
  digest: DigestData;
  sent: string[];
  errors: string[];
}

export default function DailyDigestCard() {
  const { locale } = useI18n();

  const { data, isLoading, refetch } = useQuery({
    queryKey: ["digest-preview"],
    queryFn: async () => (await api.get<PreviewResp>("/admin/digest/preview")).data,
  });

  const send = useMutation({
    mutationFn: async () => (await api.post<SendResp>("/admin/digest/send")).data,
    onSuccess: (r) => {
      if (r.sent.length > 0) {
        message.success(
          locale === "ko" ? `전송됨 — ${r.sent.join(", ")}` : `Sent — ${r.sent.join(", ")}`,
        );
      } else if (r.errors.length > 0) {
        message.error(r.errors.join(" / "));
      } else {
        message.warning(
          locale === "ko"
            ? "Slack URL이 비어 있습니다. DIGEST_SLACK_WEBHOOK_URL 또는 SLACK_WEBHOOK_URL을 채워주세요."
            : "No Slack URL configured (DIGEST_SLACK_WEBHOOK_URL or SLACK_WEBHOOK_URL).",
        );
      }
      refetch();
    },
    onError: (e: Error) => message.error(e.message),
  });

  const d = data?.digest;
  const sev = d?.findings.by_severity ?? {};
  const day = d?.period.since.slice(0, 10);

  return (
    <Card
      title={
        <Space>
          <ClockCircleOutlined />
          <span>Daily Security Digest</span>
        </Space>
      }
      extra={
        <Button
          type="primary"
          icon={<SendOutlined />}
          loading={send.isPending}
          onClick={() => send.mutate()}
        >
          {locale === "ko" ? "지금 전송" : "Send now"}
        </Button>
      }
      style={{ marginBottom: 16 }}
      loading={isLoading}
    >
      <Paragraph type="secondary" style={{ marginBottom: 8 }}>
        {locale === "ko"
          ? "어제 일어난 일을 Slack 한 카드로 요약합니다. 자동 발송은 외부 cron(k8s CronJob 등)이 POST /api/v1/admin/digest/send를 호출하는 패턴을 권장합니다."
          : "Yesterday in one Slack card. For automation, schedule an external cron to POST /api/v1/admin/digest/send."}
      </Paragraph>

      {d && (
        <>
          <Text type="secondary" style={{ fontSize: 12 }}>
            {locale === "ko" ? "집계 기간: " : "Period: "}
            {day}
          </Text>
          <Space wrap style={{ marginTop: 8, marginBottom: 8 }}>
            <Tag>
              {locale === "ko" ? "신규" : "New"} {d.findings.total}
            </Tag>
            {sev.critical > 0 && <Tag color="red">critical {sev.critical}</Tag>}
            {sev.high > 0 && <Tag color="volcano">high {sev.high}</Tag>}
            {sev.medium > 0 && <Tag color="orange">medium {sev.medium}</Tag>}
            <Tag>
              {locale === "ko" ? "스캔" : "Scans"} {d.scans.total}
              {d.scans.failed > 0 ? ` (fail ${d.scans.failed})` : ""}
            </Tag>
            <Tag>
              {locale === "ko" ? "권한 요청" : "Access"} {d.access_requests.total}
              {d.access_requests.granted > 0 ? ` · ${d.access_requests.granted} granted` : ""}
            </Tag>
          </Space>
        </>
      )}

      <Alert
        type="info"
        showIcon
        style={{ marginTop: 8 }}
        message={
          <Text style={{ fontSize: 12 }}>
            <code>DIGEST_SLACK_WEBHOOK_URL</code>
            {locale === "ko" ? " (없으면 " : " (falls back to "}
            <code>SLACK_WEBHOOK_URL</code>
            {locale === "ko" ? ") · 자동 발송 가이드는 " : ") · CronJob example: "}
            <a
              href="https://github.com/jland-93/mond/blob/main/docs/SETUP.md#daily-digest"
              target="_blank"
              rel="noreferrer"
            >
              SETUP.md
            </a>
          </Text>
        }
      />
    </Card>
  );
}
