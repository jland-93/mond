/**
 * 🌙 Access Center — 직원이 권한을 요청하고 자기 요청 상태를 본다
 */

import { SendOutlined } from "@ant-design/icons";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Alert, Button, Card, Form, Input, InputNumber, Select, Space, Table, Tag, Typography } from "antd";

import { useI18n } from "@/i18n";
import { iamApi, type AccessRequest, type AccessRequestStatus } from "@/lib/iam-api";

const { Title, Paragraph } = Typography;
const { TextArea } = Input;

const STATUS_COLOR: Record<AccessRequestStatus, string> = {
  pending_ai_review: "blue",
  ai_auto_approved: "green",
  needs_human_review: "orange",
  human_approved: "green",
  human_denied: "red",
  granted: "green",
  grant_failed: "red",
};

const RISK_COLOR: Record<string, string> = {
  critical: "red",
  high: "orange",
  medium: "gold",
  low: "green",
};

export default function AccessCenter() {
  const { t } = useI18n();
  const qc = useQueryClient();
  const [form] = Form.useForm();

  const { data: identities } = useQuery({ queryKey: ["iam-identities"], queryFn: () => iamApi.listIdentities() });
  const { data: permissions } = useQuery({ queryKey: ["iam-permissions"], queryFn: () => iamApi.listPermissions() });
  const { data: requests } = useQuery({ queryKey: ["access-requests"], queryFn: () => iamApi.listRequests() });

  const submit = useMutation({
    mutationFn: (body: {
      requester: string;
      reason: string;
      target_identity_id: number;
      permission_id: number;
      duration_hours?: number;
    }) => iamApi.createRequest(body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["access-requests"] });
      form.resetFields();
    },
  });

  return (
    <div>
      <Title level={2} style={{ marginBottom: 8 }}>
        {t.iam.accessCenterTitle}
      </Title>
      <Paragraph type="secondary">{t.iam.accessCenterDesc}</Paragraph>

      <Card title={t.iam.submit} style={{ marginTop: 12 }}>
        <Form
          form={form}
          layout="vertical"
          onFinish={(v) =>
            submit.mutate({
              requester: v.requester,
              reason: v.reason,
              target_identity_id: v.target_identity_id,
              permission_id: v.permission_id,
              duration_hours: v.duration_hours ?? undefined,
            })
          }
        >
          <Form.Item label={t.iam.fields.requester} name="requester" rules={[{ required: true }]}>
            <Input placeholder="alice@example.com" />
          </Form.Item>
          <Form.Item label={t.iam.fields.identity} name="target_identity_id" rules={[{ required: true }]}>
            <Select
              showSearch
              optionFilterProp="label"
              options={(identities ?? []).map((i) => ({
                value: i.id,
                label: `${i.name} (${t.iam.identityTypes[i.identity_type]})`,
              }))}
            />
          </Form.Item>
          <Form.Item label={t.iam.fields.permission} name="permission_id" rules={[{ required: true }]}>
            <Select
              showSearch
              optionFilterProp="label"
              options={(permissions ?? []).map((p) => ({
                value: p.id,
                label: `${p.name}${p.risk_hint ? ` · ${p.risk_hint}` : ""}`,
              }))}
            />
          </Form.Item>
          <Form.Item label={t.iam.fields.duration} name="duration_hours">
            <InputNumber min={1} max={720} style={{ width: "100%" }} placeholder="8" />
          </Form.Item>
          <Form.Item label={t.iam.fields.reason} name="reason" rules={[{ required: true, min: 5 }]}>
            <TextArea rows={3} placeholder="이 권한이 왜 필요한지 구체적으로 적어주세요." />
          </Form.Item>
          <Button type="primary" icon={<SendOutlined />} loading={submit.isPending} onClick={() => form.submit()}>
            {t.iam.submit}
          </Button>
        </Form>
      </Card>

      <Card title={t.iam.accessCenterTitle === "Access Center" ? "My requests" : "내 요청"} style={{ marginTop: 16 }}>
        {(requests ?? []).length === 0 && (
          <Alert
            type="info"
            message={t.iam.accessCenterTitle === "Access Center" ? "No requests yet." : "아직 요청이 없습니다."}
          />
        )}
        <Table
          dataSource={requests ?? []}
          rowKey="id"
          size="small"
          expandable={{
            expandedRowRender: (r: AccessRequest) => (
              <Space direction="vertical">
                <div>
                  <Tag color="purple">{t.iam.aiDecision}</Tag>
                  <Tag color={RISK_COLOR[r.ai_decision.risk_level ?? "medium"]}>
                    risk: {r.ai_decision.risk_level ?? "—"}
                  </Tag>
                  {r.ai_decision.decision && (
                    <Tag>
                      {t.iam.decisions[r.ai_decision.decision as keyof typeof t.iam.decisions] ?? r.ai_decision.decision}
                    </Tag>
                  )}
                  <div style={{ marginTop: 6 }}>{r.ai_decision.reason}</div>
                </div>
                {r.human_decision.reviewer && (
                  <div>
                    <Tag color="cyan">{t.iam.humanDecision}</Tag>
                    <Tag color={r.human_decision.approve ? "green" : "red"}>
                      {r.human_decision.approve ? t.iam.approve : t.iam.deny}
                    </Tag>
                    <span style={{ marginLeft: 6 }}>{r.human_decision.reviewer}</span>
                    {r.human_decision.note && <div style={{ marginTop: 4 }}>{r.human_decision.note}</div>}
                  </div>
                )}
                {r.grant_result?.granted_at && (
                  <div>
                    <Tag color="green">{t.iam.grantResult}</Tag>
                    <span>{r.grant_result.success ? "✓" : "✗"} {String(r.grant_result.detail?.note ?? r.grant_result.detail?.policy_arn ?? "")}</span>
                  </div>
                )}
              </Space>
            ),
          }}
          columns={[
            { title: "#", dataIndex: "id", width: 60 },
            { title: t.iam.fields.requester, dataIndex: "requester" },
            {
              title: t.iam.fields.identity,
              dataIndex: "target_identity_id",
              render: (id: number) => identities?.find((x) => x.id === id)?.name ?? id,
            },
            {
              title: t.iam.fields.permission,
              dataIndex: "permission_id",
              render: (id: number) => permissions?.find((x) => x.id === id)?.name ?? id,
            },
            {
              title: t.iam.fields.status,
              dataIndex: "status",
              render: (s: AccessRequestStatus) => (
                <Tag color={STATUS_COLOR[s]}>{t.iam.statuses[s]}</Tag>
              ),
              width: 160,
            },
          ]}
        />
      </Card>
    </div>
  );
}
