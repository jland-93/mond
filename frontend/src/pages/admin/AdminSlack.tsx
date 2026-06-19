/**
 * Admin · Slack 연동 — 워크스페이스 채널을 purpose별로 매핑.
 *
 * 채널 4종 (default / digest / finding / access_request / role_request) 각각
 * Slack Incoming Webhook URL을 등록. ENV(SLACK_WEBHOOK_URL · DIGEST_SLACK_WEBHOOK_URL)는
 * DB가 비었을 때만 fallback으로 쓰인다.
 */

import { DeleteOutlined, SendOutlined, SlackOutlined } from "@ant-design/icons";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Alert,
  Button,
  Card,
  Form,
  Input,
  Popconfirm,
  Space,
  Switch,
  Tag,
  Typography,
  message,
} from "antd";

import { useI18n } from "@/i18n";
import {
  adminSlackApi,
  type SlackChannelRow,
  type SlackPurpose,
} from "@/lib/admin-slack-api";

const { Title, Paragraph, Text } = Typography;

interface PurposeDef {
  key: SlackPurpose;
  ko: string;
  en: string;
  desc_ko: string;
  desc_en: string;
}

const PURPOSES: PurposeDef[] = [
  {
    key: "default",
    ko: "기본 채널",
    en: "Default",
    desc_ko: "다른 purpose에 맞는 채널이 없을 때 폴백.",
    desc_en: "Fallback when a more specific channel is not set.",
  },
  {
    key: "digest",
    ko: "Daily Digest",
    en: "Daily Digest",
    desc_ko: "매일 어제 일어난 일을 요약하는 카드.",
    desc_en: "Daily summary card of yesterday.",
  },
  {
    key: "finding",
    ko: "발견사항 알림",
    en: "Findings",
    desc_ko: "severity 임계 이상 신규 발견 알림.",
    desc_en: "New findings above severity threshold.",
  },
  {
    key: "access_request",
    ko: "권한 요청",
    en: "Access Requests",
    desc_ko: "권한 요청 / 검토 / 회수 흐름.",
    desc_en: "Access request, review, and revoke events.",
  },
  {
    key: "role_request",
    ko: "역할 변경 요청",
    en: "Role Changes",
    desc_ko: "임직원 role 변경 요청 알림.",
    desc_en: "Employee role-change requests.",
  },
];

export default function AdminSlack() {
  const { locale } = useI18n();
  const qc = useQueryClient();

  const { data: rows, isLoading } = useQuery({
    queryKey: ["admin-slack-channels"],
    queryFn: adminSlackApi.list,
  });

  const byPurpose = (p: SlackPurpose): SlackChannelRow | undefined =>
    (rows ?? []).find((r) => r.purpose === p);

  return (
    <div>
      <Title level={2} style={{ marginBottom: 4 }}>
        {locale === "ko" ? "Slack 연동" : "Slack Integration"}
      </Title>
      <Paragraph type="secondary">
        {locale === "ko"
          ? "워크스페이스의 Incoming Webhook URL을 목적별 채널에 매핑합니다. 등록된 채널이 있으면 그것을 우선 사용하고, 비어 있으면 .env의 SLACK_WEBHOOK_URL / DIGEST_SLACK_WEBHOOK_URL을 fallback으로 사용합니다."
          : "Map Slack Incoming Webhook URLs to channels by purpose. DB values take precedence over .env fallbacks (SLACK_WEBHOOK_URL / DIGEST_SLACK_WEBHOOK_URL)."}
      </Paragraph>

      <Alert
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
        message={
          locale === "ko"
            ? "Slack workspace에서 Incoming Webhook을 만드는 법"
            : "How to create a Slack Incoming Webhook"
        }
        description={
          <Text style={{ fontSize: 12 }}>
            Slack workspace → Apps → 검색 <b>Incoming Webhooks</b> → 채널 선택 → URL 복사.{" "}
            <a
              href="https://api.slack.com/messaging/webhooks"
              target="_blank"
              rel="noreferrer"
            >
              공식 가이드
            </a>
          </Text>
        }
      />

      <Space direction="vertical" style={{ width: "100%" }} size={12}>
        {PURPOSES.map((p) => (
          <ChannelCard
            key={p.key}
            def={p}
            row={byPurpose(p.key)}
            loading={isLoading}
            onChange={() => qc.invalidateQueries({ queryKey: ["admin-slack-channels"] })}
          />
        ))}
      </Space>
    </div>
  );
}

function ChannelCard({
  def,
  row,
  loading,
  onChange,
}: {
  def: PurposeDef;
  row: SlackChannelRow | undefined;
  loading: boolean;
  onChange: () => void;
}) {
  const { locale } = useI18n();
  const [form] = Form.useForm();

  const upsert = useMutation({
    mutationFn: (v: { webhook_url: string; label?: string; enabled: boolean }) =>
      adminSlackApi.upsert({
        purpose: def.key,
        webhook_url: v.webhook_url,
        label: v.label ?? null,
        enabled: v.enabled,
      }),
    onSuccess: () => {
      message.success(locale === "ko" ? "저장됨" : "Saved");
      form.resetFields(["webhook_url"]);
      onChange();
    },
    onError: (e: Error & { response?: { data?: { detail?: string } } }) =>
      message.error(e.response?.data?.detail ?? e.message),
  });

  const remove = useMutation({
    mutationFn: () => adminSlackApi.remove(def.key),
    onSuccess: () => {
      message.success(locale === "ko" ? "삭제됨" : "Deleted");
      onChange();
    },
  });

  const testSend = useMutation({
    mutationFn: () =>
      adminSlackApi.test({
        purpose: def.key,
        text: `Mond ${def.en} test — ${new Date().toISOString()}`,
      }),
    onSuccess: (r) => {
      if (r.ok) message.success(locale === "ko" ? "전송됨" : "Sent");
      else message.error(r.error || "fail");
    },
  });

  return (
    <Card
      size="small"
      title={
        <Space>
          <SlackOutlined />
          <span>{locale === "ko" ? def.ko : def.en}</span>
          {row?.enabled && <Tag color="green">{locale === "ko" ? "활성" : "Active"}</Tag>}
          {row && !row.enabled && <Tag>{locale === "ko" ? "비활성" : "Disabled"}</Tag>}
          {!row && <Tag>{locale === "ko" ? "미설정 — ENV fallback" : "Not set — ENV fallback"}</Tag>}
        </Space>
      }
      loading={loading}
      extra={
        row && (
          <Space>
            <Button
              size="small"
              icon={<SendOutlined />}
              loading={testSend.isPending}
              onClick={() => testSend.mutate()}
            >
              {locale === "ko" ? "테스트" : "Test"}
            </Button>
            <Popconfirm
              title={locale === "ko" ? "이 채널 매핑을 삭제할까요?" : "Delete this mapping?"}
              okType="danger"
              onConfirm={() => remove.mutate()}
            >
              <Button size="small" danger icon={<DeleteOutlined />}>
                {locale === "ko" ? "삭제" : "Remove"}
              </Button>
            </Popconfirm>
          </Space>
        )
      }
    >
      <Paragraph type="secondary" style={{ marginBottom: 12, fontSize: 12 }}>
        {locale === "ko" ? def.desc_ko : def.desc_en}
      </Paragraph>

      {row && (
        <Space wrap style={{ marginBottom: 12 }}>
          {row.label && <Tag color="geekblue">{row.label}</Tag>}
          <code style={{ fontFamily: "monospace", fontSize: 12 }}>{row.webhook_masked}</code>
        </Space>
      )}

      <Form
        form={form}
        layout="vertical"
        initialValues={{
          label: row?.label ?? "",
          enabled: row?.enabled ?? true,
        }}
        onFinish={(v) =>
          upsert.mutate({
            webhook_url: v.webhook_url,
            label: v.label,
            enabled: v.enabled,
          })
        }
      >
        <Form.Item
          name="webhook_url"
          label={locale === "ko" ? "Webhook URL" : "Webhook URL"}
          rules={[
            { required: true },
            {
              pattern: /^https:\/\/hooks\.slack\.com\//,
              message: locale === "ko" ? "Slack incoming webhook URL이어야 합니다" : "Must be a Slack hooks URL",
            },
          ]}
          extra={
            row
              ? locale === "ko"
                ? "비워두면 기존 값 유지가 아니라 변경하려면 새 URL을 적어주세요."
                : "Submit a new URL to overwrite."
              : undefined
          }
        >
          <Input.Password placeholder="https://hooks.slack.com/services/T.../B.../XXXX" autoComplete="off" />
        </Form.Item>

        <Space>
          <Form.Item name="label" label={locale === "ko" ? "라벨 (예: #mond-alerts)" : "Label"} style={{ marginBottom: 0, width: 260 }}>
            <Input placeholder="#mond-alerts" />
          </Form.Item>
          <Form.Item name="enabled" label={locale === "ko" ? "활성" : "Enabled"} valuePropName="checked" style={{ marginBottom: 0 }}>
            <Switch />
          </Form.Item>
          <Form.Item style={{ marginBottom: 0 }}>
            <Button type="primary" htmlType="submit" loading={upsert.isPending}>
              {row ? (locale === "ko" ? "갱신" : "Update") : locale === "ko" ? "등록" : "Save"}
            </Button>
          </Form.Item>
        </Space>
      </Form>
    </Card>
  );
}
