/**
 * 내 Slack DM 알림 설정 — 본인 owner asset의 finding 발생 시 본인 DM 또는
 * organization 채널에 @mention.
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
import { api } from "@/lib/api";

const { Paragraph, Text } = Typography;

interface SlackPref {
  configured: boolean;
  webhook_masked?: string;
  slack_user_id?: string | null;
  notify_finding: boolean;
}

export default function MySlackDmCard() {
  const { locale } = useI18n();
  const qc = useQueryClient();
  const [form] = Form.useForm();

  const { data, isLoading } = useQuery({
    queryKey: ["me-slack-pref"],
    queryFn: async () => (await api.get<SlackPref>("/me/slack-preference")).data,
  });

  const save = useMutation({
    mutationFn: (v: { slack_dm_webhook_url: string; slack_user_id: string; notify_finding: boolean }) =>
      api.put<SlackPref>("/me/slack-preference", {
        slack_dm_webhook_url: v.slack_dm_webhook_url || null,
        slack_user_id: v.slack_user_id || null,
        notify_finding: v.notify_finding,
      }),
    onSuccess: () => {
      message.success(locale === "ko" ? "저장됨" : "Saved");
      form.resetFields(["slack_dm_webhook_url"]);
      qc.invalidateQueries({ queryKey: ["me-slack-pref"] });
    },
    onError: (e: Error & { response?: { data?: { detail?: string } } }) =>
      message.error(e.response?.data?.detail ?? e.message),
  });

  const remove = useMutation({
    mutationFn: () => api.delete("/me/slack-preference"),
    onSuccess: () => {
      message.success(locale === "ko" ? "삭제됨" : "Deleted");
      form.resetFields();
      qc.invalidateQueries({ queryKey: ["me-slack-pref"] });
    },
  });

  const testSend = useMutation({
    mutationFn: () => api.post<{ ok: boolean; error: string | null }>("/me/slack-preference/test"),
    onSuccess: (r) => {
      if (r.data.ok) message.success(locale === "ko" ? "전송됨" : "Sent");
      else message.error(r.data.error || "fail");
    },
    onError: (e: Error & { response?: { data?: { detail?: string } } }) =>
      message.error(e.response?.data?.detail ?? e.message),
  });

  return (
    <Card
      title={
        <Space>
          <SlackOutlined />
          <span>{locale === "ko" ? "내 Slack 알림" : "My Slack Notifications"}</span>
          {data?.configured && <Tag color="green">{locale === "ko" ? "활성" : "Active"}</Tag>}
        </Space>
      }
      style={{ marginTop: 16 }}
      loading={isLoading}
      extra={
        data?.configured && (
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
              title={locale === "ko" ? "내 Slack 설정을 지울까요?" : "Remove your Slack preferences?"}
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
      <Paragraph type="secondary" style={{ marginBottom: 12 }}>
        {locale === "ko"
          ? "내가 owner인 자산의 finding이 생기면 본인 Slack DM으로 받거나, organization 채널에 본인 @mention을 추가합니다. 둘 중 하나만 등록해도 됩니다."
          : "Get DMs (or be @mentioned in the org channel) when findings appear on assets you own."}
      </Paragraph>

      {data?.configured && (
        <Space wrap style={{ marginBottom: 12 }}>
          {data.webhook_masked && (
            <Tag>
              {locale === "ko" ? "내 DM" : "My DM"}: <code style={{ fontFamily: "monospace" }}>{data.webhook_masked}</code>
            </Tag>
          )}
          {data.slack_user_id && (
            <Tag>
              @mention: <code style={{ fontFamily: "monospace" }}>{data.slack_user_id}</code>
            </Tag>
          )}
        </Space>
      )}

      <Form
        form={form}
        layout="vertical"
        initialValues={{
          slack_user_id: data?.slack_user_id ?? "",
          notify_finding: data?.notify_finding ?? true,
        }}
        onFinish={(v) => save.mutate(v)}
      >
        <Form.Item
          name="slack_dm_webhook_url"
          label={locale === "ko" ? "내 DM webhook URL (선택)" : "My DM webhook URL (optional)"}
          extra={
            locale === "ko"
              ? "본인 DM 채널을 가진 워크스페이스에서 만든 Incoming Webhook URL. 등록 시 본인만 받는 DM으로 발송."
              : "Slack Incoming Webhook URL pointing to your DM channel."
          }
          rules={[
            {
              validator: (_, v) =>
                !v || /^https:\/\/hooks\.slack\.com\//.test(v)
                  ? Promise.resolve()
                  : Promise.reject(new Error("Slack hooks URL")),
            },
          ]}
        >
          <Input.Password placeholder="https://hooks.slack.com/services/..." autoComplete="off" />
        </Form.Item>

        <Form.Item
          name="slack_user_id"
          label={locale === "ko" ? "Slack user ID (선택, @mention용)" : "Slack user ID (optional, for @mention)"}
          extra={
            locale === "ko"
              ? "U12345 형식. 본인 Slack 프로필 → 더보기 → 멤버 ID 복사. 조직 채널 알림에 본인 mention이 추가됩니다."
              : "U12345 format. From Slack profile → More → Copy member ID."
          }
          rules={[
            {
              validator: (_, v) =>
                !v || /^[UW][A-Z0-9]+$/.test(v)
                  ? Promise.resolve()
                  : Promise.reject(new Error("U.. or W.. ID")),
            },
          ]}
        >
          <Input placeholder="U12345ABCDE" />
        </Form.Item>

        <Form.Item name="notify_finding" valuePropName="checked" label={locale === "ko" ? "발견사항 알림 받기" : "Notify on findings"}>
          <Switch />
        </Form.Item>

        <Form.Item style={{ marginBottom: 0 }}>
          <Button type="primary" htmlType="submit" loading={save.isPending}>
            {data?.configured ? (locale === "ko" ? "갱신" : "Update") : locale === "ko" ? "등록" : "Save"}
          </Button>
        </Form.Item>
      </Form>

      <Alert
        type="info"
        showIcon
        style={{ marginTop: 12 }}
        message={
          <Text style={{ fontSize: 12 }}>
            {locale === "ko"
              ? "본인이 owner로 등록된 자산의 finding이 trigger됩니다. 자산 상세에서 owner = 본인 이메일 확인."
              : "Triggered for findings on assets where owner = your email."}
          </Text>
        }
      />
    </Card>
  );
}
